#!/usr/bin/env python3
"""Küszöb-job BEKÜLDŐ (v1.1) — ELŐKÉSZÍTVE; NEM KÜLD BE SEMMIT.

Forrás: Maya beküldési feltételei (2026-11-12 14:15 UTC §B és 14:17 UTC).
Ez a szkript a beküldés *eljárását* rögzíti; a beküldésről a TULAJDONOS
dönt külön (PLAN_KUSZOB_v1.1 §7). Az agent SQPU-t nem indít; a tokenhez
SEHOGYA nem fér hozzá (csak az IBM_QUANTUM_TOKEN környezeti változó
NÉV szerepel itt).

MIT TUD (a jővőbeli, külön tulajdonosi döntéssel indított --submit mód):
  1. Gate-ek (mindegyik fail-closed ⇒ a folyamat MEGÁLL, beküldés NÉLKÜL):
     G1  draft/elemző hash-kapu: a job_meta.draft_v1.1.json betöltése + az
         analyze_kuszob.py FAGYASZTOTT hash-e (6458a64d…) — eltérés ⇒ HALT;
     G2  manifest integritás-kapu: circuits_manifest.json hash (94048f35…)
         + payload recompute + minden QASM hash-e a manifesttel — eltérés ⇒ HALT;
     G3  snapshot-kapu: data/snapshot.json sha256 == a draft recordingje
         (2acfda2e…) — eltérés ⇒ HALT;
     G4  Kerék-integritás-kapu: frozen_wheel_params.json a .sha256 szerint —
         sérülés ⇒ HALT;
     G5  seed-kapu: a shuffle seed KIZÁRÓLAG env-ből (alapértelmezett név
         KUSZOB_SHUFFLE_SEED, --seed-env átnevezhető) vagy egy
         REPÓN KÍVÜLI fájlból (--seed-file) olvasható; a seed értéke SEHOVA
         nem íródik (nincs log/commit/job_meta); hash ==
         6a68d507df95063181a461b988e8b88ae3563a4b766e1c94eb14a5a7ef478f2f
         — eltérés ⇒ HALT;
     G6  backend-kapu: a backend KÖTELEZŐEN ibm_kingston — más ⇒ HALT
         (--submit módban az ÉLŐ backend .name-jét is ellenőrzi);
     G7  CZ-kapu (a beküldéskor, a run() hívás ELŐTT): az ÉLŐ ibm_kingston
         backenden transzpilált áramkörök CZ-száma és CZ-párjai PONTOSAN a
         circuits_manifest.json-nal egyezzenek
         (initial_layout [117,124,125,126], optimization_level 0,
         seed_transpiler 1234) — bármilyen eltérés ⇒ HALASZTÁS, beküldés NINCS.
         --dry-run módban ez HELYI transzpilációval fut (a snapshot
         coupling_map-ja; NEM élő backend — proxy, NEM hardware);
  2. Keverés (a beküldéskor): ids = sorted(order);
     rng = random.Random(int(seed_hex, 16)); rng.shuffle(ids) — a seed nem
     kerül elő sehol máshol;
  3. A qiskit / qiskit-aer (és ha importálható, qiskit-ibm-runtime)
     VERZIÓJA a job_metába kerül (Maya javaslata);
  4. BEKÜLDÉSKOR (KESOBB, külön tulajdonosi döntéssel): a job_id-t AZONNAL,
     KÜLÖN fájlba menti (job_id_record.json — record-first, az eredmény
     letöltése ELŐTT), majd job_meta.final.json-t ír a snapshottal, a napi
     kalibráció hivatkozásával és az ÉLŐ backenden normálázott payload-hashsel.

MIT NEM CSINÁL MOST: nem hív QPU-t, nem hív run()/Sampler-t, nem kér tokent,
nem tölt le eredményt. --dry-run módban minden gate lefut IBM-kapcsolat
NÉLKÜL, szintetikus adatzárral.

Jelölések: szimuláció/transzpiláció sosem HARDWARE; a ROGZUL ítélet
kötelező jelölése: "gep-alkalmassagi kapu, tankonyvi varakozas" (ez a
szkripptől független szabály — itt is rögzítve).

Exit kódok: 0 = minden gate zöld (dry-run ok / submit ok) · 3 = HALT
(valamelyik gate bukott — beküldés NÉLKÜL) · 2 = használati hiba.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
HERE = Path(__file__).resolve().parent

ANALYZER_SHA256 = "6458a64d616d28436429c06075f0ebdaabc482e1d72d405c3f45ce4871636e3d"
SEED_SHA256 = "6a68d507df95063181a461b988e8b88ae3563a4b766e1c94eb14a5a7ef478f2f"
MANIFEST_SHA256 = "94048f35ab7012f8027170adbc17b7f783e8b738abb1b17f7113d299cdcaf962"
PAYLOAD_SHA256 = "6194ef7adbc74901c57682408b9d421b373c148d67c9389c7de467487dacdb4e"
DRAFT_SHA256 = "0f6c66298e488ef08305907167f2ef21dadf4e41c93613c5180f351f2d4dedc8"
EXPECTED_BACKEND = "ibm_kingston"
EXPECTED_LAYOUT = [117, 124, 125, 126]
EXPECTED_OPT_LEVEL = 0
SEED_TRANSPILER = 1234
BASIS = ["cz", "rz", "sx", "x", "delay", "id"]
SHOTS = 4096
ROGZUL_MARKING = "gep-alkalmassagi kapu, tankonyvi varakozas"
IDS = [
    "kuszob_cut_k2", "kuszob_cut_k4", "kuszob_cut_k8",
    "kuszob_m+1_k0", "kuszob_m+1_k2", "kuszob_m+1_k4", "kuszob_m+1_k8",
    "kuszob_m-1_k0", "kuszob_m-1_k2", "kuszob_m-1_k4", "kuszob_m-1_k8",
    "kuszob_m0_k0", "kuszob_m0_k2", "kuszob_m0_k4", "kuszob_m0_k8",
    "kuszob_pc_k0", "kuszob_pc_k4",
]


class Halt(Exception):
    """Fail-closed kapu-bukás — a folyamat MEGÁLL, beküldés NÉLKÜL."""


def log(msg):
    print(msg, flush=True)


def ok(msg):
    log(f"[PASS] {msg}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path):
    try:
        with open(path, "rb") as f:
            return json.load(f)
    except FileNotFoundError:
        raise Halt(f"nem található: {path}")
    except json.JSONDecodeError as exc:
        raise Halt(f"érvénytelen JSON ({path}): {exc}")


def versions() -> dict:
    import qiskit
    import qiskit_aer
    out = {"qiskit_version": qiskit.__version__, "qiskit_aer_version": qiskit_aer.__version__}
    try:
        import qiskit_ibm_runtime  # noqa: F401
        out["qiskit_ibm_runtime_version"] = qiskit_ibm_runtime.__version__
    except Exception:
        out["qiskit_ibm_runtime_version"] = None
    return out


# ---------- G1: draft + elemző hash-kapu ----------
def gate_draft_and_analyzer(draft_path: Path):
    draft = load_json(draft_path)
    if draft.get("job_ids") != []:
        raise Halt("a draft job_ids nem üres — már beküldött/módosított állapot; HALT")
    routing = draft.get("routing", {})
    if routing.get("initial_layout") != EXPECTED_LAYOUT:
        raise Halt(f"initial_layout {routing.get('initial_layout')!r} != {EXPECTED_LAYOUT} — HALT")
    if routing.get("optimization_level") != EXPECTED_OPT_LEVEL:
        raise Halt(f"optimization_level != {EXPECTED_OPT_LEVEL} — HALT")
    if routing.get("seed_transpiler") != SEED_TRANSPILER:
        raise Halt("seed_transpiler != 1234 — HALT")
    if draft.get("backend") != EXPECTED_BACKEND:
        raise Halt(f"backend {draft.get('backend')!r} != {EXPECTED_BACKEND} — HALT")
    # a DRAFT hash-e (ha a kanonikus v1.1 fájlról van szó)
    actual_draft = sha256_file(draft_path)
    if draft_path.name == "job_meta.draft_v1.1.json" and actual_draft != DRAFT_SHA256:
        raise Halt(f"a draft hash-e nem egyezik a v1.1 hash-sel ({DRAFT_SHA256[:12]}…) — HALT")
    # elemző: fájl-hash == draft-érték == kanonikus fagyasztott érték
    analyzer = HERE / "analyze_kuszob.py"
    actual = sha256_file(analyzer)
    pinned = (draft.get("analysis_freeze") or {}).get("sha256")
    if pinned != ANALYZER_SHA256:
        raise Halt("a draft analysis_freeze.sha256 nem a kanonikus fagyasztott érték — HALT")
    if actual != ANALYZER_SHA256:
        raise Halt(f"analyze_kuszob.py hash-e ({actual[:12]}…) != fagyasztott 6458a64d… — HALT")
    # snapshot: nyers hash == draft recording
    snap = ROOT / "data" / "snapshot.json"
    snap_sha = sha256_file(snap)
    if snap_sha != draft.get("snapshot_sha256"):
        raise Halt("a data/snapshot.json sha256 nem egyezik a draft-tal — HALT")
    ok(f"G1 draft/elemző/snapshot hash-kapu zöld (draft {actual_draft[:12]}…, elemző 6458a64d…, snapshot 2acfda2e…)")
    return draft


# ---------- G2: manifest integritás + QASM-hashek ----------
def gate_manifest(manifest_path: Path):
    man = load_json(manifest_path)
    actual = sha256_file(manifest_path)
    canonical = manifest_path.name == "circuits_manifest.json"
    if canonical and actual != MANIFEST_SHA256:
        raise Halt(f"circuits_manifest.json hash-e ({actual[:12]}…) != 94048f35… — HALT")
    if man.get("payload_sha256") != PAYLOAD_SHA256:
        raise Halt("a manifest payload_sha256 nem 6194ef7a… — HALT")
    if man.get("circuit_count") != 17 or len(man.get("circuits", [])) != 17:
        raise Halt("a manifest nem 17 áramkört tartalmaz — HALT")
    # recompute payload (id-sorrend + qasm-hashek konkatenációja)
    csat = "".join(c["qasm_sha256"] for c in sorted(man["circuits"], key=lambda c: c["id"]))
    if hashlib.sha256(csat.encode()).hexdigest() != PAYLOAD_SHA256:
        raise Halt("a payload recompute nem egyezik — HALT")
    # QASM-hashek a fájlokból
    for c in man["circuits"]:
        qpath = HERE / c["qasm_file"]
        if sha256_file(qpath) != c["qasm_sha256"]:
            raise Halt(f"{c['id']}: qasm hash-eltérés — HALT")
    ok(f"G2 manifest integritás-kapu zöld (manifest {actual[:12]}…, payload 6194ef7a…, 17/17 qasm-hash)")
    return man


# ---------- G4: a fagyasztott Kerék-fájl integritása ----------
def gate_frozen_wheel():
    sha_lines = (ROOT / "preregistration" / "frozen_wheel_params.sha256").read_text().splitlines()
    pinned = None
    for line in sha_lines:
        parts = line.split()
        if len(parts) >= 2 and parts[-1] == "frozen_wheel_params.json":
            pinned = parts[0]
    actual = sha256_file(ROOT / "preregistration" / "frozen_wheel_params.json")
    if pinned != actual:
        raise Halt("frozen_wheel_params.json integritás sérült — HALT")
    ok(f"G4 Kerék-fagyasztás integritás zöld ({actual[:12]}…)")


# ---------- G5: seed-kapu (a seed értéke sehova nem íródik) ----------
def read_seed(args) -> str:
    if args.seed_file:
        p = Path(args.seed_file).resolve()
        if ROOT in p.parents or p == ROOT:
            raise Halt("a seed-fájl REPÓN BELÜL található — REPÓN KÍVÜLI fájl szükséges — HALT")
        seed = p.read_text(encoding="utf-8").strip().splitlines()[-1].strip()
        origin = f"fájl: {p}"
    else:
        var = args.seed_env
        seed = os.environ.get(var)
        origin = f"env: {var}"
        if not seed:
            raise Halt(f"a shuffle seed nem adott (env {var} üres, nincs --seed-file) — HALT")
    seed = seed.strip()
    if len(seed) != 64 or any(c not in "0123456789abcdef" for c in seed):
        raise Halt("a seed nem 64-karakteres kisbetűs hex — HALT")
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    if digest != SEED_SHA256:
        # FIGYELEM: a seed értéket SOHA nem írjuk ki — csak a hash-eltérést jelezzük.
        raise Halt(f"shuffle seed hash mismatch ({origin}); elvárt 6a68d507… — HALT")
    ok(f"G5 seed-kapu zöld ({origin}; hash 6a68d507… egyezik; a seed értéke NEM kerül kiírásra)")
    return seed  # csak memóriában él tovább


def shuffled_order(order, seed_hex):
    ids = sorted(order)
    rng = random.Random(int(seed_hex, 16))
    rng.shuffle(ids)
    return ids


def order_digest(order) -> str:
    """A kevert sorrend ELŐRE KÖZZÉTETT-ALKALMASSÁGÚ hash-e (a nyers sorrend
    nem kerül a repóba az unblinding előtt)."""
    return hashlib.sha256(",".join(order).encode("utf-8")).hexdigest()


# ---------- G7: CZ-kapu (helyi transzpiláció proxy vagy ÉLŐ backend) ----------
def _pruned_circuits():
    """A TÉNYLEGESEN beküldendő (prune-olt, routolt) áramkörök — a manifesttel
    azonos pipeline-nal (build → transpile(opt=0) → prune), MÉRÉS NÉLKÜL.
    A prune-olt q0..q3 = a használt fizikai qubitek növekvő sorrendje —
    pontosan ezekre vonatkozik a beküldési initial_layout."""
    import submission.kuszob.build_kuszob as bk  # noqa: PLC0415
    out = {}
    for arm, ks in bk.ARMS.items():
        for k in ks:
            cid = f"kuszob_{arm}_k{k}"
            qc_unit = bk.build_logical(arm, k)
            sub, used, fl, _t0 = bk.transpile_pruned(qc_unit)
            out[cid] = (sub, used)
    return out


def transpile_circuits(layout, coupling_map=None, backend=None):
    """A beküldés útját modellező kapu-transzpiláció.

    --dry-run: a prune-olt áramkörök a SNAPSHOT coupling_mapjére transzpilálva
    (HELYI proxy; NEM élő backend; routing-ellenőrzés, nem memória-teszt).
    --submit:  a prune-olt áramkörök az ÉLŐ backendre transzpilálva — a
    bekuldott payload maga megy át a CX-kapun a run() hívás ELŐTT.
    """
    from qiskit import transpile
    from src.wheel.noise import load_snapshot  # noqa: PLC0415
    snap_coupling = coupling_map
    if snap_coupling is None and backend is None:
        snap_coupling = load_snapshot()["coupling_map"]
    out = {}
    for cid, (sub, used) in _pruned_circuits().items():
        try:
            if backend is not None:
                t = transpile(sub, backend=backend, initial_layout=layout,
                              optimization_level=EXPECTED_OPT_LEVEL,
                              seed_transpiler=SEED_TRANSPILER)
            else:
                t = transpile(sub, basis_gates=BASIS, coupling_map=snap_coupling,
                              initial_layout=layout, optimization_level=EXPECTED_OPT_LEVEL,
                              seed_transpiler=SEED_TRANSPILER)
        except Exception as exc:
            raise Halt(f"{cid}: transzpiláció bukott ({exc}) — HALASZTÁS, beküldés NINCS")
        out[cid] = t
    return out


def gate_cz(transpiled, manifest) -> None:
    by_id = {c["id"]: c for c in manifest["circuits"]}
    mismatches = []
    import re
    for cid, t in transpiled.items():
        # fizikai CZ-párok: a transpile után a q-bit indexek a coupling-map fizikai id-k
        pairs: dict[str, int] = {}
        n_cz = 0
        for ins in t.data:
            if ins.operation.name == "cz":
                pa = int(t.find_bit(ins.qubits[0]).index)
                pb = int(t.find_bit(ins.qubits[1]).index)
                a, b = (pa, pb) if pa <= pb else (pb, pa)
                key = f"{a}-{b}"
                pairs[key] = pairs.get(key, 0) + 1
                n_cz += 1
        exp_n = by_id[cid]["n_cz"]
        exp_pairs = by_id[cid]["cz_pairs"]
        if n_cz != exp_n or pairs != exp_pairs:
            mismatches.append(f"{cid}: qasm cz={n_cz} (elvárt {exp_n}), párok={pairs} (elvárt {exp_pairs})")
    if mismatches:
        details = "\n  - " + "\n  - ".join(mismatches)
        raise Halt(f"CZ-KAPU BUKOTT — beküldés NINCS:{details}")
    ok(f"G7 CZ-kapu zöld: 17/17 áramkör CZ-száma és CZ-párjai pontosan a manifesttel (pl. m+1_k8: 92 CZ; 117-125: 3, 124-125: 44, 125-126: 45)")


# ---------- --submit: a valódi beküldési utak (MOST SOSEM FUT LE) ----------
def do_submit(args, draft, manifest):
    token = os.environ.get("IBM_QUANTUM_TOKEN")
    if not token:
        raise Halt("IBM_QUANTUM_TOKEN nincs a környezetben — a token a tulajdonosé; a szkript nem kéri és nem tárolja — HALT")
    log("FIGYELEM: ez a mód VALÓDI beküldést végezhet — csak külön tulajdonosi döntéssel.")
    if not sys.stdin.isatty():
        raise Halt("nem interaktív terminál — a beküldés csak gépelve erősíthető meg — HALT")
    answer = input("A beküldés megerősítéséhez írd be pontosan: KUSZOB BEKULDES → ").strip()
    if answer != "KUSZOB BEKULDES":
        raise Halt("megerősítés nem érkezett meg — HALT")

    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2  # noqa: PLC0415
    service = QiskitRuntimeService()  # a token a környezetből jön — soha nem kezeljük
    backend = service.backend(EXPECTED_BACKEND)
    if getattr(backend, "name", None) != EXPECTED_BACKEND:
        raise Halt(f"az élő backend nem {EXPECTED_BACKEND} — HALT")
    ok(f"G6 élő backend-kapu zöld: {backend.name}")

    seed = read_seed(args)  # G5
    transpiled = transpile_circuits(EXPECTED_LAYOUT, backend=backend)
    gate_cz(transpiled, manifest)  # G7 — run() ELŐTT; bukás ⇒ HALASZTÁS, beküldés NINCS

    order = shuffled_order(draft["order"], seed)
    batch = [transpiled[cid] for cid in order]
    from qiskit import qasm2  # noqa: PLC0415
    backend_qasm = [qasm2.dumps(qc) for qc in batch]
    backend_payload = hashlib.sha256("".join(
        hashlib.sha256(q.encode()).hexdigest() for q in backend_qasm).encode()).hexdigest()

    sampler = SamplerV2(mode=backend)
    job = sampler.run(batch, shots=SHOTS)

    # RECORD-FIRST: a job_id-t AZONNAL, külön fájlba mentjük az eredmény letöltése ELŐTT
    rec = {
        "job_id": job.job_id(),
        "recorded_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "backend": backend.name,
        "circuit_count": len(batch),
        "shots": SHOTS,
        "order_sha256": order_digest(order),
        "backend_normalized_payload_sha256": backend_payload,
        "note": "record-first — az eredmény letöltése ELŐTT mentve; az agent az eredményt nem tölti le; a nyers kevert sorrend nincs a repóban (unblindingkor a seeddel reprodukálható)",
    }
    with open(HERE / "job_id_record.json", "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=2, ensure_ascii=False)
    log(f"[RECORD-FIRST] job_id_record.json megírva ({rec['recorded_utc']})")

    final = {
        **{k: v for k, v in draft.items() if k not in ("warning", "job_ids", "shuffle", "shuffle_seed")},
        "status": "BEKÜLDVE (record-first) — az eredmény letöltése még NEM történt meg",
        "submitted_utc": rec["recorded_utc"],
        "job_ids": [rec["job_id"]],
        "order_sha256": rec["order_sha256"],
        "backend_normalized_payload_sha256": backend_payload,
        "snapshot_file": "data/snapshot.json",
        "snapshot_sha256": draft["snapshot_sha256"],
        "daily_calibration": {
            "backend": backend.name,
            "note": "napi kalibráció: LD. a beküldés napján vett snapshot.json; a T1/T2/2Q-hibák a snapshotból olvasandók; a drift miatt a snapshot nem újrafelhasználható más napra",
        },
        **versions(),
    }
    with open(HERE / "job_meta.final.json", "w", encoding="utf-8") as f:
        json.dump(final, f, indent=2, ensure_ascii=False)
    log("[RECORD-FIRST] job_meta.final.json megírva (verziók + snapshot + napi kalibráció hivatkozás; SEED NEM került bele)")
    log("KÉSZ — az eredmény letöltése KÜLÖN lépés (nem ez a szkript dolga).")


def _load_snapshot_coupling():
    from src.wheel.noise import load_snapshot  # noqa: PLC0415
    return load_snapshot()["coupling_map"]


def main() -> int:
    ap = argparse.ArgumentParser(description="Küszöb-job beküldő v1.1 — ELŐKÉSZÍTVE; QPU-t most nem indít")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true",
                      help="minden gate lefut IBM-kapcsolat NÉLKÜL; beküldés NINCS")
    mode.add_argument("--submit", action="store_true",
                      help="VALÓDI beküldés (CSAK külön tulajdonosi döntéssel; interaktív megerősítés; token az IBM_QUANTUM_TOKEN env-ből)")
    ap.add_argument("--draft", default=str(HERE / "job_meta.draft_v1.1.json"))
    ap.add_argument("--manifest", default=str(HERE / "circuits_manifest.json"))
    ap.add_argument("--backend", default=EXPECTED_BACKEND,
                    help="csak ibm_kingston érvényes — bármi más ⇒ HALT (T3 teszt)")
    ap.add_argument("--seed-file", default=None, help="REPÓN KÍVÜLI fájl a shuffle seeddel")
    ap.add_argument("--seed-env", default="KUSZOB_SHUFFLE_SEED", help="a seed környezeti változójának neve")
    ap.add_argument("--test-inject-layout", default=None,
                    help="CSAK NEGATÍV TESZT: felülírja a beküldési initial_layout-ot (pl. 125,117,124,126 — Maya hibája)")
    args = ap.parse_args()

    try:
        layout = EXPECTED_LAYOUT
        if args.test_inject_layout is not None:
            layout = [int(x) for x in args.test_inject_layout.split(",")]
            log(f"[TESZT] injected layout: {layout} — a CZ-kapunak MEG KELL bukania")
        if args.backend != EXPECTED_BACKEND:
            raise Halt(f"G6 backend-kapu: {args.backend!r} nem {EXPECTED_BACKEND} — HALT")
        ok(f"G6 backend-kapu zöld (paraméter: {args.backend})" + ("" if not args.submit else " (+ élő ellenőrzés alább)"))

        draft = gate_draft_and_analyzer(Path(args.draft))   # G1
        manifest = gate_manifest(Path(args.manifest))       # G2
        gate_frozen_wheel()                                 # G4
        seed = read_seed(args)                              # G5
        order = shuffled_order(draft["order"], seed)        # keverés (seed NEM íródik ki)
        log("[shuffle] 17 áramkör keverve (seed csak memóriában; a nyers sorrend nem kerül kiírásra — csak az order_sha256)")

        if args.dry_run:
            transpiled = transpile_circuits(layout, coupling_map=_load_snapshot_coupling())
            # a proxy-transzpilációt NEM írjuk a repóba; csak a CZ-kaput futtatjuk
            gate_cz(transpiled, manifest)                     # G7 (proxy)
            report = {
                "kind": "KUSZOB v1.1 DRY-RUN — SZIMULÁCIÓ/ELŐKÉSZÍTÉS, NEM HARDWARE; QPU NEM INDULT",
                "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "backend_param": args.backend,
                "layout_used_for_check": layout,
                "layout_note": "dry-run: a CZ-kapu a SNAPSHOT coupling_mapjével transzpilálva fut (proxy; nem élő backend)",
                "gates": {"G1_draft_analyzer": "PASS", "G2_manifest": "PASS", "G4_frozen_wheel": "PASS",
                          "G5_seed": "PASS", "G6_backend": "PASS", "G7_cz_proxy": "PASS"},
                "shuffled_order_sha256": order_digest(order),
                "note": "a nyers kevert sorrend NEM kerül a repóba — unblindingkor a seedből reprodukálható",
                **versions(),
                "qpu_executed": False,
            }
            out = HERE / "dry_run_report.json"
            with open(out, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            ok("DRY-RUN OK — minden gate zöld; beküldés NEM történt; QPU nem indult.")
            log(f"jelentés: {out} (verziók + kapu-eredmények + sorrend-hash; SEED ÉS NYERS SORREND NINCS BENNE)")
            log(f"ROGZUL-jelölés emlékeztető: \"{ROGZUL_MARKING}\" — nem memória-teszt")
            return 0

        # --submit: VALÓDI út — MOST SOSEM FUT LE (külön tulajdonosi döntés, interaktív)
        do_submit(args, draft, manifest)
        return 0
    except Halt as exc:
        log(f"HALT — a folyamat MEGÁLL, beküldés NÉLKÜL: {exc}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
