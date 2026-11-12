#!/usr/bin/env python3
"""Küszöb-job BEKÜLDŐ (v1.3) — ELŐKÉSZÍTVE; NEM KÜLD BE SEMMIT.

Forrás: Maya beküldési feltételei (2026-11-12 14:15 UTC §B és 14:17 UTC) +
seed-amendment v1.2 + v1.3 mérés-hiány javítás (a 2026-11-12 14:49 UTC-kor
beadott dbqt3q9abdes73fosj8g job 19:16 UTC-kor ERROR állapotban végzett,
adat NÉLKÜL; IBM hibakód 1515: "Circuits without measurements are not
allowed" — a payload mérés nélküli áramköröket tartalmazott; precedencia:
PLAN_KUSZOB_v1.3.md).
Ez a szkript a beküldés *eljárását* rögzíti; a beküldésről a TULAJDONOS
dönt külön (PLAN_KUSZOB_v1.3 §7). Az agent QPU-t nem indít; a tokenhez
SEHOGYA nem fér hozzá (csak az IBM_QUANTUM_TOKEN környezeti változó
NÉV szerepel itt).

v1.3-ban a payload-áramkörök a build_kuszob saját with_measurements()
lépésével kapják meg a méréseket a backend-transzpiláció ELŐTT (a mérés-
huzalozás a fagyasztott QASM-okéval AZONOS — agent-oldali újraépítési
ellenőrzés: 17/17 byte-azonos); új: G8 mérés-kapu (17/17 áramkör pontosan
3 mérést tartalmaz, a c0/c1/c2 clbit-ekkel) — mind dry-run, mind submit
úton, run() ELŐTT; különben HALT.
A várt shuffle-seed-hash a submit_manifest_v1.3.json-ból (ill. a
job_meta.draft_v1.3.json-ból, keresztellenőrzéssel) olvasódik — NINCS
beégetett konstans; a v1.1-es seed (hash 6a68d507…) ÉRVÉNYÉT VESZTETTE.
Kanonikus hivatkozás-lánc: PLAN_KUSZOB_v1.3.md → submit_manifest_v1.3.json →
(job_meta.draft_v1.3.json, analyze_kuszob.py, circuits_manifest.json);
bármilyen eltérés ⇒ HALT.

MIT TUD (a jővőbeli, külön tulajdonosi döntéssel indított --submit mód):
  1. Gate-ek (mindegyik fail-closed ⇒ a folyamat MEGÁLL, beküldés NÉLKÜL):
     G1  draft/elemző hash-kapu: a job_meta.draft_v1.3.json betöltése + az
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
         nem íródik (nincs log/commit/job_meta); hash == a v1.2 manifest/draft
         szerinti érték (83f43b94…) — eltérés ⇒ HALT;
     G6  backend-kapu: a backend KÖTELEZŐEN ibm_kingston — más ⇒ HALT
         (--submit módban az ÉLŐ backend .name-jét is ellenőrzi);
     G7  CZ-kapu (a beküldéskor, a run() hívás ELŐTT): az ÉLŐ ibm_kingston
         backenden transzpilált áramkörök CZ-száma és CZ-párjai PONTOSAN a
         circuits_manifest.json-nal egyezzenek
         (initial_layout [117,124,125,126], optimization_level 0,
         seed_transpiler 1234) — bármilyen eltérés ⇒ HALASZTÁS, beküldés NINCS.
         --dry-run módban ez HELYI transzpilációval fut (a snapshot
         coupling_map-ja; NEM élő backend — proxy, NEM hardware);
     G8  mérés-kapu (v1.3, a run() hívás ELŐTT): minden payload-áramkör
         PONTOSAN 3 mérést tartalmaz a c0/c1/c2 clbit-ekre; bármely
         áramkör mérés nélkül (vagy nem-3 méréssel) ⇒ HALT, run() NINCS.
         --dry-run és --submit úton is lefut;
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

ANALYZER_SHA256 = "6458a64d616d28436429c06075f0ebdaabc482e1d72d405c3f45ce4871636e3d"  # keresztellenőrzve a v1.2 manifesttel
MANIFEST_SHA256 = "94048f35ab7012f8027170adbc17b7f783e8b738abb1b17f7113d299cdcaf962"  # keresztellenőrzve
PAYLOAD_SHA256 = "6194ef7adbc74901c57682408b9d421b373c148d67c9389c7de467487dacdb4e"  # keresztellenőrzve
CANONICAL_DEFAULT = HERE / "submit_manifest_v1.3.json"
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


def load_canonical(path: Path) -> dict:
    """A v1.2 submit-manifest betöltése fail-closed módon."""
    c = load_json(path)
    required = ["shuffle_seed_sha256", "job_meta_draft_sha256", "analyzer_sha256",
                "circuits_manifest_sha256", "payload_sha256",
                "expected_backend", "expected_initial_layout",
                "expected_optimization_level", "seed_transpiler"]
    missing = [k for k in required if k not in c]
    if missing:
        raise Halt(f"a submit-manifest ({path.name}) hiányzó mezői: {missing} — HALT")
    if c["expected_backend"] != EXPECTED_BACKEND:
        raise Halt("a submit-manifest expected_backend nem ibm_kingston — HALT")
    if list(c["expected_initial_layout"]) != EXPECTED_LAYOUT:
        raise Halt("a submit-manifest expected_initial_layout nem [117,124,125,126] — HALT")
    if int(c["expected_optimization_level"]) != EXPECTED_OPT_LEVEL:
        raise Halt("a submit-manifest expected_optimization_level nem 0 — HALT")
    if int(c["seed_transpiler"]) != SEED_TRANSPILER:
        raise Halt("a submit-manifest seed_transpiler nem 1234 — HALT")
    if c["analyzer_sha256"] != ANALYZER_SHA256:
        raise Halt("a submit-manifest analyzer_sha256 nem a fagyasztott elemző-hash — HALT")
    if c["circuits_manifest_sha256"] != MANIFEST_SHA256:
        raise Halt("a submit-manifest circuits_manifest_sha256 nem 94048f35… — HALT")
    if c["payload_sha256"] != PAYLOAD_SHA256:
        raise Halt("a submit-manifest payload_sha256 nem 6194ef7a… — HALT")
    return c


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
def gate_draft_and_analyzer(draft_path: Path, canonical: dict):
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
    # a DRAFT fájl-hash-e a v1.2 manifest szerinti értékkel egyezzen
    actual_draft = sha256_file(draft_path)
    if actual_draft != canonical["job_meta_draft_sha256"]:
        raise Halt(f"a draft hash-e ({actual_draft[:12]}…) nem a v1.2 manifest szerinti érték — HALT")
    # a seed-hash a manifest és a draft között keresztellenőrzve
    draft_seed = (draft.get("shuffle") or {}).get("seed_sha256")
    if draft_seed != canonical["shuffle_seed_sha256"]:
        raise Halt("a draft és a v1.2 manifest shuffle seed hash-e eltér — HALT")
    # elemző: fájl-hash == draft-érték == manifest-érték == fagyasztott érték
    analyzer = HERE / "analyze_kuszob.py"
    actual = sha256_file(analyzer)
    pinned = (draft.get("analysis_freeze") or {}).get("sha256")
    if pinned != ANALYZER_SHA256 or pinned != canonical["analyzer_sha256"]:
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
def gate_manifest(manifest_path: Path, canonical: dict):
    man = load_json(manifest_path)
    actual = sha256_file(manifest_path)
    if actual != canonical["circuits_manifest_sha256"]:
        raise Halt(f"circuits_manifest.json hash-e ({actual[:12]}…) != a v1.2 manifest szerinti 94048f35… — HALT")
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
def read_seed(args, canonical: dict) -> str:
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
    expected = canonical["shuffle_seed_sha256"]
    if digest != expected:
        # FIGYELEM: a seed értéket SOHA nem írjuk ki — csak a hash-eltérést jelezzük.
        raise Halt(f"shuffle seed hash mismatch ({origin}); elvárt {expected[:12]}… (a v1.2 manifest szerinti) — HALT")
    ok(f"G5 seed-kapu zöld ({origin}; hash {expected[:12]}… egyezik; a seed értéke NEM kerül kiírásra)")
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
    """A TÉNYLEGESEN beküldendő áramkörök alapja — a manifesttel azonos
    pipeline-nal (build → transpile(opt=0) → prune). A prune-olt q0..q3 =
    a használt fizikai qubitek növekvő sorrendje — pontosan ezekre
    vonatkozik a beküldési initial_layout. v1.3: a final_layout-ot is
    továbbadjuk (a mérés-huzalozáshoz a with_measurements()-nek kell)."""
    import submission.kuszob.build_kuszob as bk  # noqa: PLC0415
    out = {}
    for arm, ks in bk.ARMS.items():
        for k in ks:
            cid = f"kuszob_{arm}_k{k}"
            qc_unit = bk.build_logical(arm, k)
            sub, used, fl, _t0 = bk.transpile_pruned(qc_unit)
            out[cid] = (sub, used, fl)
    return out


def _payload_circuits(strip_measurements: bool = False):
    """A payload-áramkörök: prune-olt áramkör + a build_kuszob saját
    with_measurements() mérés-huzalozása (c0 <- R3, c1 <- R2, c2 <- R1
    rekordlajstrom balról jobbra 'R1R2R3') — a fagyasztott QASM-okéval
    AZONOS (17/17 byte-azonos újraépítéssel igazolva).

    strip_measurements=True CSAK NEGATÍV TESZT: eltávolítja a méréseket
    (a 2026-11-12-i 1515 hiba reprodukciója) — a G8-nak MEG KELL bukania."""
    import submission.kuszob.build_kuszob as bk  # noqa: PLC0415
    out = {}
    for cid, (sub, used, fl) in _pruned_circuits().items():
        measured = bk.with_measurements(sub, used, fl)
        if strip_measurements:
            measured = measured.remove_final_measurements(inplace=False)
        out[cid] = measured
    return out


def transpile_circuits(layout, coupling_map=None, backend=None, strip_measurements: bool = False):
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
    payload = _payload_circuits(strip_measurements=strip_measurements)
    for cid, measured in payload.items():
        try:
            if backend is not None:
                t = transpile(measured, backend=backend, initial_layout=layout,
                              optimization_level=EXPECTED_OPT_LEVEL,
                              seed_transpiler=SEED_TRANSPILER)
            else:
                t = transpile(measured, basis_gates=BASIS, coupling_map=snap_coupling,
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


# ---------- G8: mérés-kapu (v1.3) — run() ELŐTT; bukás ⇒ HALT ----------
def gate_measurements(transpiled) -> None:
    """MINDEN payload-áramkör PONTOSAN 3 mérést tartalmazzon, a c0/c1/c2
    clbit-ekre egy-egy — a 2026-11-12-i 1515 ('Circuits without
    measurements are not allowed') hiba előfordulása esetén HALT."""
    bad = []
    for cid, t in sorted(transpiled.items()):
        clbits = []
        n_meas = 0
        for ins in t.data:
            if ins.operation.name == "measure":
                n_meas += 1
                clbits.append(int(t.find_bit(ins.clbits[0]).index))
        if n_meas != 3 or sorted(clbits) != [0, 1, 2]:
            bad.append(f"{cid}: {n_meas} mérés, clbit-ek={sorted(clbits)} (elvárt: 3 mérés a c0/c1/c2-ön)")
    if bad:
        details = "\n  - " + "\n  - ".join(bad)
        raise Halt(f"G8 MÉRÉS-KAPU BUKOTT — beküldés NINCS, run() NEM HÍVHATÓ:{details}")
    ok("G8 mérés-kapu zöld: 17/17 áramkör pontosan 3 mérést tartalmaz a c0/c1/c2 clbit-ekre")


# ---------- --submit: a valódi beküldési utak (MOST SOSEM FUT LE) ----------
def do_submit(args, draft, manifest, canonical):
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

    seed = read_seed(args, canonical)  # G5
    transpiled = transpile_circuits(EXPECTED_LAYOUT, backend=backend)
    gate_cz(transpiled, manifest)  # G7 — run() ELŐTT; bukás ⇒ HALASZTÁS, beküldés NINCS
    gate_measurements(transpiled)  # G8 — run() ELŐTT; bukás ⇒ HALT, run() NEM HÍVHATÓ

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
    ap = argparse.ArgumentParser(description="Küszöb-job beküldő v1.3 — ELŐKÉSZÍTVE; QPU-t most nem indít")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true",
                      help="minden gate lefut IBM-kapcsolat NÉLKÜL; beküldés NINCS")
    mode.add_argument("--submit", action="store_true",
                      help="VALÓDI beküldés (CSAK külön tulajdonosi döntéssel; interaktív megerősítés; token az IBM_QUANTUM_TOKEN env-ből)")
    ap.add_argument("--draft", default=str(HERE / "job_meta.draft_v1.3.json"))
    ap.add_argument("--submit-manifest", default=str(CANONICAL_DEFAULT),
                    help="a v1.3 submit-manifest (ennek seed/draft/elemző/manifest hash értékei a kanonikusak)")
    ap.add_argument("--manifest", default=str(HERE / "circuits_manifest.json"))
    ap.add_argument("--backend", default=EXPECTED_BACKEND,
                    help="csak ibm_kingston érvényes — bármi más ⇒ HALT (T3 teszt)")
    ap.add_argument("--seed-file", default=None, help="REPÓN KÍVÜLI fájl a shuffle seeddel")
    ap.add_argument("--seed-env", default="KUSZOB_SHUFFLE_SEED", help="a seed környezeti változójának neve")
    ap.add_argument("--test-inject-layout", default=None,
                    help="CSAK NEGATÍV TESZT: felülírja a beküldési initial_layout-ot (pl. 125,117,124,126 — Maya hibája)")
    ap.add_argument("--test-strip-measurements", action="store_true",
                    help="CSAK NEGATÍV TESZT: eltávolítja a payload méréseit (a 2026-11-12 1515 hiba reprodukciója) — a G8-nak MEG KELL bukania")
    args = ap.parse_args()

    try:
        layout = EXPECTED_LAYOUT
        if args.test_inject_layout is not None:
            layout = [int(x) for x in args.test_inject_layout.split(",")]
            log(f"[TESZT] injected layout: {layout} — a CZ-kapunak MEG KELL bukania")
        if args.backend != EXPECTED_BACKEND:
            raise Halt(f"G6 backend-kapu: {args.backend!r} nem {EXPECTED_BACKEND} — HALT")
        ok(f"G6 backend-kapu zöld (paraméter: {args.backend})" + ("" if not args.submit else " (+ élő ellenőrzés alább)"))

        canonical = load_canonical(Path(args.submit_manifest))  # v1.2 manifest — a várt hashek forrása
        draft = gate_draft_and_analyzer(Path(args.draft), canonical)   # G1
        manifest = gate_manifest(Path(args.manifest), canonical)       # G2
        gate_frozen_wheel()                                 # G4
        seed = read_seed(args, canonical)                              # G5
        order = shuffled_order(draft["order"], seed)        # keverés (seed NEM íródik ki)
        log("[shuffle] 17 áramkör keverve (seed csak memóriában; a nyers sorrend nem kerül kiírásra — csak az order_sha256)")

        if args.dry_run:
            transpiled = transpile_circuits(layout, coupling_map=_load_snapshot_coupling(),
                                            strip_measurements=args.test_strip_measurements)
            # a proxy-transzpilációt NEM írjuk a repóba; csak a CZ-kaput futtatjuk
            gate_cz(transpiled, manifest)                     # G7 (proxy)
            gate_measurements(transpiled)                     # G8 (proxy)
            report = {
                "kind": "KUSZOB v1.3 DRY-RUN — SZIMULÁCIÓ/ELŐKÉSZÍTÉS, NEM HARDWARE; QPU NEM INDULT",
                "submit_manifest": Path(args.submit_manifest).name,
                "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "backend_param": args.backend,
                "layout_used_for_check": layout,
                "layout_note": "dry-run: a CZ-kapu a SNAPSHOT coupling_mapjével transzpilálva fut (proxy; nem élő backend)",
                "gates": {"G1_draft_analyzer": "PASS", "G2_manifest": "PASS", "G4_frozen_wheel": "PASS",
                          "G5_seed": "PASS", "G6_backend": "PASS", "G7_cz_proxy": "PASS",
                          "G8_measurements": "PASS"},
                "shuffled_order_sha256": order_digest(order),
                "note": "a nyers kevert sorrend NEM kerül a repóba — unblindingkor a seedből reprodukálható",
                **versions(),
                "qpu_executed": False,
            }
            out = HERE / "dry_run_report_v1.3.json"  # v1.1-es dry_run_report.json byte-ra változatlan (a submit_manifest_v1.1.json hivatkozása!)
            with open(out, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            ok("DRY-RUN OK — minden gate zöld; beküldés NEM történt; QPU nem indult.")
            log(f"jelentés: {out} (verziók + kapu-eredmények + sorrend-hash; SEED ÉS NYERS SORREND NINCS BENNE)")
            log(f"ROGZUL-jelölés emlékeztető: \"{ROGZUL_MARKING}\" — nem memória-teszt")
            return 0

        # --submit: VALÓDI út — MOST SOSEM FUT LE (külön tulajdonosi döntés, interaktív)
        do_submit(args, draft, manifest, canonical)
        return 0
    except Halt as exc:
        log(f"HALT — a folyamat MEGÁLL, beküldés NÉLKÜL: {exc}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
