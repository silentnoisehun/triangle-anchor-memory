"""QPU-beküldő — MINDEN AUDIT ELŐTT TILOS FUTTATNI.

A QPU-beküldést a Control Agent végzi a tulajdonos rövid életű tokenjével
(terv 1. fázis). Ez a fájl CSISZOLAT, amelyet a beküldés előtt auditálni kell.

Kemény szabályok (a terv 7. pontjából, változatlanul):
- A tokent KIZÁRÓLAG az IBM_QUANTUM_TOKEN környezeti változóból olvassa;
  semmilyen fájlba, sehova nem kerül token.
- A jobok sorrendje: a kalibráció ELŐRE, majd a karok sorsolása (shuffle) —
  a seed és a teljes sorrend a data/job_meta.json-ba kerül a beküldés
  PILLANATÁBAN (külön a lekérdezéstől).
- A job_id csak a job_meta.json-ba íródik; commit-üzenetbe nem kerül.
- A beküldés után a job_meta.json SOHA nem írandó újra.
- A nyers counts azonnal mentendő (data/raw_counts.json) és SHA-256-hash-elendő.

Control Agent audit (2026-11-11) utáni javítások — MIND kódbeli, QPU-hívás nélkül:
1. Backend-választás: valódi, működő Heron-backend a futtató környezetből,
   csatorna = ibm_quantum_platform; a qubit-választás a terv 3.1 pontozása
   szerint (S: három fizikai szomszéd; min(T1,T2)/(1+20ε), ε = a qubit
   incidens 2Q-kapu-hibáinak maximuma — dokumentált döntés, lásd
   ``_score_qubit``). A választott elrendezés initial_layout-tal
   transpile-nál rögzítve (optimization_level=0 — az üres időrések időzítése
   nem optimalizálható el!).
2. A kalibrációs áramkörök (T1, Hahn-T2, kiolvasás, φ_eff minden S–Ai párra)
   ugyanabba a jobba kerülnek, a karok ELÉ.
3. A backend-pillanatkép (snapshot: T1/T2/ε minden érintett qubitre, dt,
   csatolási térkép) a beküldéskor data/snapshot.json-ba íródik, még az
   job indítása ELŐTT, és a sim.validate_snapshot()-tel ellenőrzött,
   így egy az egyben behelyettesíthető a zajmodellbe.
4. A fetch_raw_counts() ténylegesen kiolvassa a SamplerV2 countsait a
   job_meta "order" listájával azonos sorrendben, név szerint rendeli az
   áramkörökhöz, teljességet ellenőriz, és data/raw_counts.sha256-ba írja
   a hash-t. Üres helyőrző nincs.

Ennek a fájlnak a futtatása ebben a fázisban TILOS — a feladat része, hogy
létrehozzuk és auditálhatóvá tegyük, de QPU-jobot NE indítson el senki
beszámolás/audit nélkül.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import random
import sys
import tempfile
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

from . import config
from .circuits import (
    build_arm_circuit,
    build_hahn_t2_circuit,
    build_pair_pswap_circuit,
    build_readout_circuit,
    build_t1_circuit,
)
from .sim import validate_snapshot

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
JOB_META_PATH = DATA_DIR / "job_meta.json"
RAW_COUNTS_PATH = DATA_DIR / "raw_counts.json"
RAW_COUNTS_SHA_PATH = DATA_DIR / "raw_counts.sha256"
SNAPSHOT_PATH = DATA_DIR / "snapshot.json"

SHUFFLE_SEED = 20261111  # az 1. fázis kar-sorrendjének rögzített sorsolás-seedje (a job_meta tartalmazza)
IBM_CHANNEL = "ibm_quantum_platform"

# Heron-felismerés: elsősorban a backend családjelölő attribútuma alapján;
# ismert nevek csak tartalék (nevek családja időről időre bővül — auditálandó).
HERON_NAME_HINTS = {"ibm_torino", "ibm_fez", "ibm_marrakesh", "ibm_kingston"}

# Kalibrációs késleltetés-rácsk (mikroszekundum) — T1 és Hahn-T2 karakterisztika
T1_DELAYS_US = [0, 20, 50, 100, 150, 200, 300]
HAHN_DELAYS_US = [0, 20, 50, 100, 150, 200, 300]


# ---------------------------------------------------------------------------
# Backend- és qubit-választás (terv 3.1)
# ---------------------------------------------------------------------------
def heron_candidates(service):
    """Összes MŰKÖDŐ Heron-jelölt backend a futtató környezetből."""
    candidates = []
    for backend in service.backends():
        name = str(getattr(backend, "name", "") or "").lower()
        family = str(
            getattr(backend, "processor_type", None)
            or getattr(backend, "backend_type", None)
            or getattr(backend, "processor", None)
            or ""
        ).lower()
        try:
            operational = bool(backend.status().operational)
        except Exception:
            operational = False  # ha a státusz nem ellenőrizhető, nem tekintjük futásra késznek
        if not operational:
            continue
        if "heron" in family or "heron" in name or name in HERON_NAME_HINTS:
            candidates.append(backend)
    return candidates


def _target_error(target, instruction_name: str, qargs: tuple) -> float | None:
    try:
        props = target.instruction_properties(instruction_name)
    except Exception:
        return None
    if not props:
        return None
    prop = props.get(tuple(qargs))
    if prop is None:
        return None
    err = getattr(prop, "error", None)
    return float(err) if err is not None else None


def _target_duration(target, instruction_name: str, qargs: tuple) -> float | None:
    try:
        props = target.instruction_properties(instruction_name)
    except Exception:
        return None
    if not props:
        return None
    prop = props.get(tuple(qargs))
    if prop is None:
        return None
    dur = getattr(prop, "duration", None)
    return float(dur) if dur is not None else None


def _qubit_1q_error(target, qubit: int, preferred=("sx", "x")) -> float | None:
    for name in preferred:
        err = _target_error(target, name, (qubit,))
        if err is not None:
            return err
    return None


def _incident_2q_edges(coupling_edges, qubit: int):
    return [(a, b) for a, b in coupling_edges if qubit in (a, b)]


def _max_2q_error_incident(target, coupling_edges, qubit: int) -> float | None:
    """Konzervatív per-qubit 2Q-hiba: az összes incidens 2Q-él hibájának maximuma."""
    try:
        two_q_names = [
            name for name in target.operation_names
            if (props := target.instruction_properties(name))
            and any(len(qa) == 2 for qa in props)
        ]
    except Exception:
        return None
    best = None
    for a, b in _incident_2q_edges(coupling_edges, qubit):
        for name in two_q_names:
            err = _target_error(target, name, (a, b))
            if err is None:
                err = _target_error(target, name, (b, a))
            if err is not None:
                best = err if best is None else max(best, err)
    return best


def _readout_error(target, qubit: int) -> float | None:
    return _target_error(target, "measure", (qubit,))


def _t1_t2_us(backend, qubit: int) -> tuple[float, float]:
    qp = backend.qubit_properties(qubit)
    t1, t2 = qp.t1, qp.t2
    if t1 is None or t2 is None:
        raise RuntimeError(f"backend: nincs elérhető T1/T2 a {qubit}. qubitre — a snapshot nem építhető")
    return float(t1) * 1e6, float(t2) * 1e6


def _score_qubit(t1_us: float, t2_us: float, eps_2q: float) -> float:
    """A terv 3.1 pontozása: min(T1,T2)/(1+20ε).

    DÖNTÉS (auditra, dokumentálva): ε a qubit incidens 2Q-kapu-hibáinak
    maximuma, mert a csatolások 2Q-kapuk; az eps_readout külön kerül a
    snapshotba, és NEM része a pontozásnak.
    """
    return min(t1_us, t2_us) / (1.0 + 20.0 * eps_2q)


def _coupling_edges(backend):
    cmap = backend.coupling_map
    try:
        edges = list(cmap.get_edges())
    except AttributeError:
        edges = list(cmap)
    return [(int(a), int(b)) for a, b in edges]


def select_backend_and_layout(service, verbose: bool = True):
    """Heron-backendek pontozása a terv 3.1 szerint; a legjobb (backend, S, horgonyok).

    Visszatérés: (backend, selection_dict) — a selection tartalmazza a teljes
    rangsort is (auditra). Lépcsőzetes leállás: ha nincs Heron-jelölt vagy
    egyetlen jelölt sem ad teljes pontozást, kivételt dob (NEM adunk elhamart
    elrendezést).
    """
    candidates = heron_candidates(service)
    if not candidates:
        raise RuntimeError(
            "nem található működő Heron-backend a futtató környezetben "
            "(IBM_QUANTUM_BACKEND-del felülbírálható a backend — akkor is Heron kell legyen!)"
        )

    ranking = []
    incomplete = []
    for backend in candidates:
        edges = _coupling_edges(backend)
        try:
            adjacency: dict[int, set[int]] = {}
            for a, b in edges:
                adjacency.setdefault(a, set()).add(b)
                adjacency.setdefault(b, set()).add(a)
            target = backend.target
            num_q = int(backend.num_qubits)
            per_qubit = {}
            ok = True
            for q in range(num_q):
                try:
                    t1, t2 = _t1_t2_us(backend, q)
                except RuntimeError:
                    ok = False
                    break
                eps_2q = _max_2q_error_incident(target, edges, q)
                if eps_2q is None:
                    ok = False
                    break
                per_qubit[q] = {"T1_us": t1, "T2_us": t2, "eps_2q": eps_2q, "score": _score_qubit(t1, t2, eps_2q)}
            if not ok:
                incomplete.append(getattr(backend, "name", "?"))
                continue
            for s in range(num_q):
                neighbors = sorted(adjacency.get(s, set()))
                if len(neighbors) < 3:
                    continue
                f_s = per_qubit[s]["score"]
                for triple in combinations(neighbors, 3):
                    f_anchors = min(per_qubit[a]["score"] for a in triple)
                    ranking.append(
                        {
                            "backend": getattr(backend, "name", "?"),
                            "S": s,
                            "anchors": list(triple),
                            "score": f_s * f_anchors,
                            "score_S": f_s,
                            "score_anchors_min": f_anchors,
                        }
                    )
        except Exception as exc:  # egy váratlanul viselkedő backend ne borítsa a selejtezést
            incomplete.append(f"{getattr(backend, 'name', '?')} ({type(exc).__name__})")
            continue

    if not ranking:
        raise RuntimeError(
            "egyetlen Heron-jelölt sem ad teljes pontozást "
            f"(hiányzó T1/T2 vagy 2Q-hiba: {incomplete or 'n/a'}) — auditra vár."
        )
    ranking.sort(key=lambda r: r["score"], reverse=True)

    override = os.environ.get("IBM_QUANTUM_BACKEND")
    if override:
        chosen = next((r for r in ranking if r["backend"] == override), None)
        if chosen is None:
            raise RuntimeError(
                f"az IBM_QUANTUM_BACKEND={override!r} nem Heron-jelölt vagy nincs teljes pontozása — "
                "a felülbírálás csak a rangsorolt Heron backendeken engedélyezett."
            )
    else:
        chosen = ranking[0]

    backend = next(b for b in candidates if getattr(b, "name", "") == chosen["backend"])
    selection = {
        "policy": "min(T1,T2)/(1+20*eps_2q)[us]; eps_2q = incidens 2Q-kapu-hibák maximuma; "
                  "S: >=3 fizikai szomszéd; rangsor = S-pont × min(horgonypontok)",
        "chosen": chosen,
        "ranking_top10": ranking[:10],
        "incomplete_backends": incomplete,
    }
    if verbose:
        print("Heron-backendek pontozása (terv 3.1) — top 10:")
        for i, r in enumerate(ranking[:10], 1):
            print(
                f"  {i:2d}. {r['backend']:<16} S={r['S']:>3} anchors={r['anchors']} "
                f"score={r['score']:.3f} (S: {r['score_S']:.3f}, anchors min: {r['score_anchors_min']:.3f})"
            )
        print(f"  → választva: {chosen['backend']} S={chosen['S']} anchors={chosen['anchors']}")
    return backend, selection


# ---------------------------------------------------------------------------
# Snapshot (data/snapshot.json) — a beküldéskor, a job INDÍTÁSA ELŐTT
# ---------------------------------------------------------------------------
def _gate_durations_us(target, s_idx, anchor_indices):
    """t1q/t2q/treadout [µs] a target InstructionProperties-ből; hiány → RuntimeError."""
    def dur(names, qargs):
        for name in names:
            d = _target_duration(target, name, qargs)
            if d is not None:
                return d * 1e6
        return None

    involved = [s_idx, *anchor_indices]
    t1q = dur(("sx", "x"), (involved[0],))
    t2q = None
    for ai in anchor_indices:
        for name in target.operation_names:
            try:
                props = target.instruction_properties(name)
            except Exception:
                continue
            if props and any(len(qa) == 2 for qa in props):
                d = _target_duration(target, name, (s_idx, ai)) or _target_duration(target, name, (ai, s_idx))
                if d is not None:
                    t2q = d * 1e6 if t2q is None else max(t2q, d * 1e6)
    tread = dur(("measure",), (involved[0],))
    missing = [k for k, v in (("t1q_us", t1q), ("t2q_us", t2q), ("treadout_us", tread)) if v is None]
    if missing:
        raise RuntimeError(f"hiányzó kapuidő(k) a targetben: {missing} — a snapshot nem építhető, a job NEM indul")
    return {"t1q_us": t1q, "t2q_us": t2q, "treadout_us": tread}


def build_snapshot(backend, selection) -> dict:
    """A backend-pillanatkép a 4 érintett qubitről + dt + csatolási térkép.

    A séma a src/config.SNAPSHOT_SCHEMA_DOC szerinti (+ dt és coupling_map kiegészítés),
    így egy az egyben behelyettesíthető a zajmodellbe (sim.load_noise_snapshot).
    Hiányzó kötelező érték esetén kivételt dob — a job ilyenkor NEM indul.
    """
    edges = _coupling_edges(backend)
    target = backend.target
    ch = selection["chosen"]
    s_idx, anchors = int(ch["S"]), [int(a) for a in ch["anchors"]]
    layout = {"S": s_idx, "A1": anchors[0], "A2": anchors[1], "A3": anchors[2]}

    qubits = {}
    for name, q in layout.items():
        t1, t2 = _t1_t2_us(backend, q)
        eps_1q = _qubit_1q_error(target, q)
        eps_2q = _max_2q_error_incident(target, edges, q)
        eps_ro = _readout_error(target, q)
        missing = [k for k, v in (("eps_1q", eps_1q), ("eps_2q", eps_2q), ("eps_readout", eps_ro)) if v is None]
        if missing:
            raise RuntimeError(
                f"hiányzó kapu/kiolvasási hiba a {name} (fizikai {q}) qubitre: {missing} — a job NEM indul"
            )
        qp = backend.qubit_properties(q)
        qubits[name] = {
            "physical_qubit": q,
            "T1_us": t1,
            "T2_us": t2,
            "eps_1q": eps_1q,
            "eps_2q": eps_2q,
            "eps_readout": eps_ro,
            "frequency_hz": float(qp.frequency) if getattr(qp, "frequency", None) else None,
        }

    snapshot = {
        "source": f"IBM Heron backend-pillanatkép a job beküldésekor — backend: {getattr(backend, 'name', '?')}",
        "is_sample": False,
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "backend": getattr(backend, "name", "?"),
        "channel": IBM_CHANNEL,
        "dt_s": float(backend.dt) if getattr(backend, "dt", None) is not None else None,
        "coupling_map": [[int(a), int(b)] for a, b in edges],
        "qubits": qubits,
        "two_qubit_edges": [
            {"pair": f"S-{name}", "physical": [s_idx, q],
             "error": _max_2q_error_incident(target, [(s_idx, q)], s_idx)}
            for name, q in (("A1", anchors[0]), ("A2", anchors[1]), ("A3", anchors[2]))
        ],
        "gate_durations": _gate_durations_us(target, s_idx, anchors),
        "selection": selection["chosen"],
    }
    # Egy az egyben behelyettesíthetőség a zajmodellbe — ellenőrzés a job indítása ELŐTT
    validate_snapshot(snapshot)
    return snapshot


def write_snapshot_atomic(snapshot: dict, path: Path = SNAPSHOT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
        tmp = Path(f.name)
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# Áramkör-készlet: kalibráció (ELŐRE, rögzített sorrendben) + karok (shuffle)
# ---------------------------------------------------------------------------
def _transpile_one(qc, backend, initial_layout):
    from qiskit import transpile

    return transpile(qc, backend=backend, initial_layout=initial_layout, optimization_level=0)


def calibration_circuits(layout: dict[str, int], backend):
    """T1, Hahn-T2, kiolvasás (mind a 4 qubitre) + φ_eff minden S–Ai párra.

    Minden 1Q-kalibráció 1-qubites áramkör az adott FIZIKAI qubiten; a φ_eff
    kalibráció 2-qubites (S + Ai). optimization_level=0 — az időzítést nem
    változtatjuk. Visszaad: [(circuit_id, transpiled_circuit), …] rögzített sorrendben.
    """
    items = []
    for name in ("S", "A1", "A2", "A3"):
        q = layout[name]
        for d in T1_DELAYS_US:
            items.append((f"t1|{name}|d{d}us", _transpile_one(build_t1_circuit(q, d), backend, [q])))
        for d in HAHN_DELAYS_US:
            items.append((f"hahn_t2|{name}|d{d}us", _transpile_one(build_hahn_t2_circuit(q, d), backend, [q])))
        for prep in ("0", "1"):
            items.append((f"readout|{name}|prep{prep}", _transpile_one(build_readout_circuit(q, prep), backend, [q])))
    s_q = layout["S"]
    for name in ("A1", "A2", "A3"):
        ai_q = layout[name]
        for k in range(config.K + 1):
            items.append(
                (f"phi_eff|{name}|k{k}", _transpile_one(build_pair_pswap_circuit(name, k), backend, [s_q, ai_q]))
            )
    return items


def arm_circuits(layout: dict[str, int], backend):
    """A 594 kar-áramkör, initial_layout=[S, A1, A2, A3] leképezéssel, "ID-n alapuló" névadással."""
    initial_layout = [layout["S"], layout["A1"], layout["A2"], layout["A3"]]
    items = []
    for arm in config.ARM_NAMES:
        for k in range(config.K + 1):
            for init in config.POP_INITS:
                cid = f"{arm}|population|{init}|k{k}"
                items.append(
                    (cid, _transpile_one(build_arm_circuit(arm, k, config.BRANCH_POPULATION, init), backend, initial_layout))
                )
        for k in range(config.K + 1):
            cid = f"{arm}|coherence|+|k{k}"
            items.append(
                (cid, _transpile_one(build_arm_circuit(arm, k, config.BRANCH_COHERENCE), backend, initial_layout))
            )
    return items


def shuffled_order(items, seed: int):
    """Determinista, seedelt sorsolás — az eredeti lista MÁSOLATÁT rendezi újra."""
    order = list(items)
    random.Random(seed).shuffle(order)
    return order


def all_job_circuits(layout: dict[str, int], backend):
    """Kalibráció ELŐRE (rögzített sorrendben), majd a karok seedelt shuffle-lel."""
    calibration = calibration_circuits(layout, backend)
    arms = arm_circuits(layout, backend)
    arms_shuffled = shuffled_order(arms, SHUFFLE_SEED)
    return calibration + arms_shuffled


def canonical_payload_sha256(items) -> str:
    """A körök sorrendjében vett, kanonikus OpenQASM 3 reprezentáció SHA-256-ja."""
    from qiskit import qasm3  # lokális import — csak a beküldési útvonal igényli

    digest = hashlib.sha256()
    for cid, qc in items:
        digest.update(cid.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(qasm3.dumps(qc).encode("utf-8"))
        digest.update(b"\x00")
    return digest.hexdigest()


def write_job_meta_atomic(meta: dict, path: Path = JOB_META_PATH) -> None:
    """job_meta.json atomikusan (tmp + rename) — NEM írható újra."""
    if path.exists():
        raise RuntimeError(
            f"{path} már létezik — a job_meta.json a beküldés pillanatában jön létre, és SOHA nem írható újra."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
        tmp = Path(f.name)
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# Beküldés (QPU) — a Control Agent auditja UTÁN futtatható
# ---------------------------------------------------------------------------
def submit() -> int:
    token = os.environ.get("IBM_QUANTUM_TOKEN")
    if not token:
        print(
            "LEÁLL: nincs IBM_QUANTUM_TOKEN a környezeti változókban.\n"
            "A token sosem kerül fájlba; a Control Agent a tulajdonos rövid életű\n"
            f"tokenjével indítja a jobokat (terv, 1. és 7. fejezet, csatorna: {IBM_CHANNEL})."
        )
        return 2
    shots = int(os.environ.get("IBM_QUANTUM_SHOTS", str(config.SHOTS)))
    if shots <= 0:
        print("LEÁLL: az IBM_QUANTUM_SHOTS pozitív egész kell legyen.")
        return 2

    try:
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    except ImportError as exc:
        print(f"LEÁLL: a qiskit-ibm-runtime csomag nem érhető el ({exc}). A 0. fázishoz nem kell.")
        return 2

    service = QiskitRuntimeService(channel=IBM_CHANNEL, token=token)
    backend, selection = select_backend_and_layout(service)
    chosen = selection["chosen"]
    layout = {"S": int(chosen["S"]), "A1": int(chosen["anchors"][0]),
              "A2": int(chosen["anchors"][1]), "A3": int(chosen["anchors"][2])}

    # 3. pont: snapshot a beküldéskor — a job indítása ELŐTT, minden audit-ellenőrzéssel
    snapshot = build_snapshot(backend, selection)
    write_snapshot_atomic(snapshot)
    print(f"snapshot mentve: {SNAPSHOT_PATH}")

    # 1–2. pont: kalibráció előre, karok utána (shuffle); initial_layout rögzítve
    items = all_job_circuits(layout, backend)
    circuit_ids = [cid for cid, _ in items]
    circuits = [qc for _, qc in items]
    n_cal = len(T1_DELAYS_US) * 2 * 4 + 2 * 4 + 3 * (config.K + 1)
    payload_sha256 = canonical_payload_sha256(items)

    sampler = SamplerV2(mode=backend)
    submitted_at = datetime.now(timezone.utc).isoformat()
    job = sampler.run(circuits, shots=shots)

    meta = {
        "job_id": job.job_id(),
        "backend": selection["chosen"]["backend"],
        "channel": IBM_CHANNEL,
        "submitted_at": submitted_at,
        "shots": shots,
        "circuit_count": len(circuits),
        "calibration_count": n_cal,
        "arm_count": len(circuits) - n_cal,
        "layout": layout,
        "selection": selection,
        "shuffle_seed": SHUFFLE_SEED,
        "order": circuit_ids,
        "payload_sha256": payload_sha256,
        "snapshot_file": str(SNAPSHOT_PATH),
        "snapshot_sha256": hashlib.sha256(SNAPSHOT_PATH.read_bytes()).hexdigest(),
        "note": "A job_id a beküldés pillanatában került ide; a lekérdezés külön lépés (fázis 2).",
    }
    write_job_meta_atomic(meta)
    print(f"Job elküldve. job_meta.json mentve ide: {JOB_META_PATH}")
    print("A nyers counts-ot a befejeződés után a fetch_raw_counts() menti és hash-eli.")
    return 0


# ---------------------------------------------------------------------------
# Nyers counts kiolvasása — a job_meta "order" listájával azonos sorrendben
# ---------------------------------------------------------------------------
def _extract_counts(pub_result, cid: str) -> dict[str, int]:
    """A SamplerV2 egy pub-eredményéből bitstring→beéjezés darabszám."""
    data = pub_result.data
    bitarray = None
    keys = list(data.keys())
    if "c" in keys:  # minden áramkörünk 'c' nevű klasszikus regisztert használ
        bitarray = data["c"]
    else:
        candidates = [(name, data[name]) for name in keys if hasattr(data[name], "get_counts")]
        if len(candidates) == 1:
            bitarray = candidates[0][1]
        else:
            raise RuntimeError(
                f"nem tudom egyértelműen kiolvasni a counts-ot ({cid}): "
                f"a pub data kulcsai: {keys} — auditra vár"
            )
    counts = dict(bitarray.get_counts())
    return counts


def _assign_counts(dataset: dict, cid: str, counts: dict) -> None:
    parts = cid.split("|")
    kind = parts[0]
    if kind in ("t1", "hahn_t2", "readout", "phi_eff"):
        dataset["calibration"][cid] = counts
        return
    if kind not in config.ARM_NAMES:
        raise RuntimeError(f"ismeretlen circuit_id a job_meta order-listájában: {cid}")
    arm, branch = parts[0], parts[1]
    k = int(parts[-1][1:])  # 'k23' → 23
    if branch == config.BRANCH_POPULATION:
        init = parts[2]
        dataset["population"][arm][init][str(k)] = counts
    elif branch == config.BRANCH_COHERENCE:
        dataset["coherence"][arm][config.COH_INIT][str(k)] = counts
    else:
        raise RuntimeError(f"ismeretlen ág a circuit_id-ban: {cid}")


def fetch_raw_counts(job_id: str) -> int:
    """A nyers counts mentése és hash-elése (fázis 1 vége) — a Control Agent futtatja.

    Kiolvassa a SamplerV2 eredményt, a job_meta "order" listájával azonos
    sorrendben, név szerint rendeli minden áramkörhöz, teljességet ellenőriz
    (0 hiányzó), és data/raw_counts.sha256-ba írja a hash-t. A job_meta.json-t
    SOHA nem írja újra.
    """
    token = os.environ.get("IBM_QUANTUM_TOKEN")
    if not token:
        print("LEÁLL: nincs IBM_QUANTUM_TOKEN a környezetben.")
        return 2
    if not JOB_META_PATH.exists():
        print(f"LEÁLL: nincs {JOB_META_PATH} — előbb a beküldés pillanatában kell létrejönnie.")
        return 2
    meta = json.loads(JOB_META_PATH.read_text(encoding="utf-8"))
    if meta.get("job_id") != job_id:
        print("LEÁLL: a megadott job_id nem egyezik a job_meta.json-nal — semmibe nem nyúlunk.")
        return 2
    order = meta.get("order")
    if not order:
        print("LEÁLL: a job_meta.json nem tartalmaz 'order' listát.")
        return 2

    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
    except ImportError as exc:
        print(f"LEÁLL: a qiskit-ibm-runtime csomag nem érhető el ({exc}).")
        return 2

    service = QiskitRuntimeService(channel=meta.get("channel", IBM_CHANNEL), token=token)
    job = service.job(job_id)
    result = job.result()

    if len(result) != len(order):
        print(
            f"LEÁLL: az eredmény {len(result)} pubból áll, a job_meta order {len(order)} elemből — "
            "a sorrend nem garantálható, az adatokat nem írjuk ki."
        )
        return 2

    dataset = {
        "meta": meta,
        "shots": meta.get("shots"),
        "population": {arm: {i: {} for i in config.POP_INITS} for arm in config.ARM_NAMES},
        "coherence": {arm: {config.COH_INIT: {}} for arm in config.ARM_NAMES},
        "calibration": {},
    }
    missing, total_shots_seen = [], 0
    for i, cid in enumerate(order):
        counts = _extract_counts(result[i], cid)
        _assign_counts(dataset, cid, counts)
        total = sum(counts.values())
        total_shots_seen += total
        if total != meta.get("shots"):
            missing.append((cid, total))
    # Teljesség-ellenőrzés: minden arm-slot Nx Nx35 feltöltve?
    expected_slots = {
        ("population", arm, init, str(k)): None
        for arm in config.ARM_NAMES for init in config.POP_INITS for k in range(config.K + 1)
    }
    expected_slots.update(
        {("coherence", arm, config.COH_INIT, str(k)): None for arm in config.ARM_NAMES for k in range(config.K + 1)}
    )
    filled = {
        ("population", arm, init, k) for arm in dataset["population"] for init in dataset["population"][arm] for k in dataset["population"][arm][init]
    } | {
        ("coherence", arm, config.COH_INIT, k) for arm in dataset["coherence"] for k in dataset["coherence"][arm][config.COH_INIT]
    }
    absent = sorted(expected_slots.keys() - filled)
    if absent:
        print(f"LEÁLL: {len(absent)} arm-áramkör hiányzik az eredményből (pl. {absent[:5]}) — az adatokat NEM írjuk ki.")
        return 2

    with RAW_COUNTS_PATH.open("w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    digest = hashlib.sha256(RAW_COUNTS_PATH.read_bytes()).hexdigest()
    RAW_COUNTS_SHA_PATH.write_text(
        f"# nyers counts — a job {job_id}\n"
        f"# mentve (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
        f"{digest}  raw_counts.json\n",
        encoding="utf-8",
    )
    n_arm_circuits = (
        sum(len(dataset["population"][arm][init]) for arm in dataset["population"] for init in dataset["population"][arm])
        + sum(len(dataset["coherence"][arm][config.COH_INIT]) for arm in dataset["coherence"])
    )
    n_cal_circuits = sum(1 for cid in order if cid.split("|")[0] in ("t1", "hahn_t2", "readout", "phi_eff"))
    print(f"nyers counts mentve: {RAW_COUNTS_PATH}")
    print(f"  áramkörök: {len(order)} (kalibráció: {n_cal_circuits}, kar: {n_arm_circuits})")
    print(f"  összes lövés: {total_shots_seen}")
    if missing:
        print(f"  FIGYELEM — {len(missing)} áramkörnél a totál ≠ shots (pl. {missing[:3]}); a nyers adatot elmentettük, de az audit vizsgálja.")
    print(f"SHA-256: {digest}  (írva: {RAW_COUNTS_SHA_PATH})")
    print("A job_meta.json-t NEM írtuk újra. A független újraszámolás a nyers countsból, token nélkül végezhető.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--fetch":
        if len(sys.argv) != 3:
            print("használat: python -m src.run --fetch <job_id>")
            raise SystemExit(2)
        raise SystemExit(fetch_raw_counts(sys.argv[2]))
    raise SystemExit(submit())
