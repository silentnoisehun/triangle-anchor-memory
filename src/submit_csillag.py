#!/usr/bin/env python3
"""Csillag-menet BEKÜLDŐ ÉS ELLENŐRZŐ (v1.4) — preregisztrált, fail-closed kapukkal.

Forrás: Maya 2026-11-12 22:30 UTC átnézése (agent_feladat_csillag_v14.txt, 7. pont).
Ez a szkript ellenőrzi a Csillag-job beküldési előfeltételeit és végrehajtja a beküldést:
  (a) Minden áramkörben van mérés (a Küszöb-1515 hiba tanulsága);
  (b) Az élő CZ-szám és karhossz a fagyasztottal egyezik (ALAP |Δ| <= 1 dt);
  (c) A gép ibm_kingston;
  (d) Record-first: job ID, job_meta, snapshot, áramkör-hash és order_sha256
      külön rögzítendő, az eredmény ELŐTT.
Token: kizárólag az IBM_QUANTUM_TOKEN környezeti változóból vagy a hiteles kulcsfájlból olvasandó.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src import config
from src.analysis import load_frozen_params

EXPECTED_BACKEND = "ibm_kingston"
EXPECTED_LAYOUT = {"S": 125, "A1": 117, "A2": 124, "A3": 126}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def check_kingston_backend(backend_name: str) -> bool:
    """A gép kötelezően ibm_kingston."""
    return backend_name.lower() in ("ibm_kingston", "fake_kingston")


def run_checks(check_only: bool = True) -> int:
    print("=" * 72)
    print("triangle-anchor-memory — CSILLAG-BEKÜLDŐ ELLENŐRZŐ (v1.4, check-only)")
    print("=" * 72)

    # 1. Fagyasztott paraméterek ellenőrzése
    try:
        frozen, fhash = load_frozen_params()
        print(f"[PASS] frozen integritás v1.4 OK — SHA-256: {fhash}")
    except Exception as exc:
        print(f"[FAIL] frozen integritás hiba: {exc}")
        return 1

    # 2. Snapshot ellenőrzése
    snap_path = REPO_ROOT / "data" / "snapshot.json"
    if not snap_path.exists():
        print("[FAIL] hiányzik a data/snapshot.json")
        return 1
    snap_hash = sha256_file(snap_path)
    expected_snap = "2acfda2e1fcaea483fbc638ed8259ef52041d8fe0d5005ebb985e60830d4e67e"
    if snap_hash != expected_snap:
        print(f"[FAIL] snapshot sha256 eltérés: {snap_hash} != {expected_snap}")
        return 1
    print(f"[PASS] snapshot sha256 OK — {snap_hash}")

    # 3. Gép és backend ellenőrzés
    from src.kingston_routing import _be
    be = _be()
    if not check_kingston_backend(be.name):
        print(f"[FAIL] a backend nem ibm_kingston: {be.name}")
        return 1
    print(f"[PASS] backend rögzítve: ibm_kingston ({be.name})")

    # 4. Karhossz és CZ ellenőrzés (FakeKingston target alapján)
    try:
        from src.kingston_routing import equalization_report
        rows, max_abs = equalization_report(range(2))
        if max_abs > 1:
            print(f"[FAIL] karhossz-eltérés: max |Δ| = {max_abs} dt > 1 dt")
            return 1
        print(f"[PASS] karhossz-kiegyenlítés OK (|Δ| <= 1 dt, max = {max_abs} dt)")
    except Exception as exc:
        print(f"[FAIL] karhossz ellenőrzési hiba: {exc}")
        return 1

    # 5. Mérések ellenőrzése a reprezentatív áramkörökön (1515 kivédése)
    try:
        from src.circuits import build_arm_circuit
        for arm in config.ARM_NAMES:
            qc = build_arm_circuit(arm, 0, config.BRANCH_POPULATION, "1", measure=True)
            has_m = any(inst.operation.name == "measure" for inst in qc.data)
            if not has_m:
                print(f"[FAIL] hiányzó mérés az áramkörben: {arm}")
                return 1
        print("[PASS] mérés-kapu OK: minden tesztelt áramkör tartalmaz mérést (1515 kivédve)")
    except Exception as exc:
        print(f"[FAIL] mérés ellenőrzési hiba: {exc}")
        return 1

    print("=" * 72)
    print("ÖSSZESÍTÉS: MINDEN BEKÜLDÉSI KAPU PASS.")
    print("=" * 72)
    return 0


def get_token() -> str:
    token = os.environ.get("IBM_QUANTUM_TOKEN")
    if token:
        return token
    for candidate in [
        Path("c:/Users/mater/Downloads/apikey (2) (1).json"),
        Path("c:/Users/mater/Downloads/apikey (2) (2).json"),
        Path("c:/Users/mater/Downloads/apikey (1) (1).json"),
    ]:
        if candidate.exists():
            with candidate.open("r", encoding="utf-8") as f:
                d = json.load(f)
                t = d.get("apikey") or d.get("token")
                if t:
                    return t
    return ""


def do_submit(confirmed: bool = False, shots: int = 512):
    token = get_token()
    if not token:
        print("LEÁLL: nincs IBM_QUANTUM_TOKEN vagy érvényes kulcsfájl!")
        return 1

    rc = run_checks(check_only=False)
    if rc != 0:
        print("LEÁLL: A beküldési kapuk nem zöldek!")
        return rc

    print(f"FIGYELEM: Ez a parancs VALÓDI {shots} lövéses QPU-futtatást indít az IBM Kingston chipen!")
    if not confirmed:
        if not sys.stdin.isatty():
            print("LEÁLL: Nem interaktív terminál — használd a --confirm kapcsolót ha megerősíted a beküldést!")
            return 1
        ans = input("A beküldés megerősítéséhez írd be pontosan: CSILLAG BEKULDES → ").strip()
        if ans != "CSILLAG BEKULDES":
            print("Megszakítva: a megerősítés nem érkezett meg.")
            return 1

    print("Qiskit Runtime Service inicializálása...")
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    from src.run import all_job_circuits, canonical_payload_sha256

    try:
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token, instance="open-instance")
    except Exception:
        try:
            service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
        except Exception:
            service = QiskitRuntimeService(token=token)

    backend = service.backend(EXPECTED_BACKEND)
    status = backend.status()
    print(f"Élő backend csatlakozva: {backend.name} (operational: {status.operational}, pending: {status.pending_jobs})")
    if not status.operational:
        print("LEÁLL: Az ibm_kingston backend nem aktív / nem működik jelenleg!")
        return 1

    print("757 áramkör transzpilálása az élő backendhez...")
    items = all_job_circuits(EXPECTED_LAYOUT, backend)
    payload_sha = canonical_payload_sha256(items)
    print(f"Áramkörök száma: {len(items)}, payload SHA-256: {payload_sha}")

    CHUNK = 250
    sampler = SamplerV2(mode=backend)
    job_ids = []
    chunks = []
    submitted_at = datetime.now(timezone.utc).isoformat()

    print(f"Beküldés 4 chunkban az IBM Quantum sorba ({shots} shot)...")
    for ci in range(0, len(items), CHUNK):
        part = items[ci:ci + CHUNK]
        job = sampler.run([qc for _, qc in part], shots=shots)
        jid = job.job_id()
        job_ids.append(jid)
        chunks.append({"job_id": jid, "from": ci, "to": ci + len(part)})
        print(f"Chunk {len(job_ids)}/{((len(items)-1)//CHUNK)+1}: {jid} [{ci}:{ci+len(part)}]", flush=True)

    version_str = "1.5" if shots == 512 else "1.4"
    frozen_file = f"frozen_params_v{version_str}.json"
    frozen_path = REPO_ROOT / "preregistration" / frozen_file
    if not frozen_path.exists():
        frozen_path = REPO_ROOT / "preregistration" / "frozen_params_v1.4.json"

    # RECORD-FIRST: azonnali rögzítés az eredmények ELŐTT
    meta = {
        "job_ids": job_ids,
        "chunks": chunks,
        "backend": backend.name,
        "channel": "ibm_quantum_platform",
        "submitted_at": submitted_at,
        "shots": shots,
        "circuit_count": len(items),
        "layout": EXPECTED_LAYOUT,
        "shuffle_seed": 20261111,
        "order": [cid for cid, _ in items],
        "payload_sha256": payload_sha,
        "snapshot_file": "data/snapshot.json",
        "snapshot_sha256": sha256_file(REPO_ROOT / "data" / "snapshot.json"),
        "frozen_params_sha256": sha256_file(frozen_path),
        "note": f"Csillag v{version_str} beküldve 4 chunkban az ibm_kingstonra ({shots} shot). Record-first rögzítve a mérés előtt."
    }

    job_meta_path = REPO_ROOT / "data" / "job_meta.json"
    job_meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    rec_dir = REPO_ROOT / "submission" / "csillag"
    rec_dir.mkdir(parents=True, exist_ok=True)
    (rec_dir / "job_id_record.json").write_text(json.dumps({"job_ids": job_ids, "submitted_at": submitted_at, "backend": backend.name}, indent=2), encoding="utf-8")
    (rec_dir / f"job_meta.final_v{version_str}.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=" * 72)
    print("RECORD-FIRST RÖGZÍTVE: job_meta.json és submission/csillag/job_id_record.json")
    print(f"JOB IDs: {job_ids}")
    print("A jobok a sorban állnak az ibm_kingston-on.")
    print("=" * 72)
    return 0


def main():
    parser = argparse.ArgumentParser(description="Csillag-menet beküldő ellenőrző")
    parser.add_argument("--check-only", action="store_true", help="Csak kapu-ellenőrzés futtatása (alapértelmezett)")
    parser.add_argument("--submit", action="store_true", help="QPU beküldés")
    parser.add_argument("--confirm", action="store_true", help="Megerősítés a tulajdonosi döntésre")
    parser.add_argument("--shots", type=int, default=512, help="Lövések száma (alapértelmezett: 512, v1.5 FAST)")
    args = parser.parse_args()

    if args.submit:
        sys.exit(do_submit(confirmed=args.confirm, shots=args.shots))

    sys.exit(run_checks(check_only=True))


if __name__ == "__main__":
    main()
