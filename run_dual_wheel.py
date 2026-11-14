#!/usr/bin/env python3
"""run_dual_wheel.py — 7-qubites Kettős Kerék (Dual-Wheel Mesh) QPU beküldő szkript.

A preregisztrált protokoll (PLAN_DUAL_WHEEL_v1.0.md) alapján:
  - 2 kar: sync, nosync
  - 9 checkpoint: [0, 4, 8, 12, 16, 20, 24, 28, 32] -> 18 áramkör
  - rögzített layout (7 qubit): [125, 117, 126, 124, 123, 122, 136]
  - cél backend: ibm_marrakesh (Heron r2)
  - mérés-kapu: S1 (q0) és S2 (q4) végmérése classical registerbe
  - record-first: job_meta.json rögzítése a futás előtt
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from src.mesh.circuits_mesh import build_dual_wheel_circuit

EXPECTED_BACKEND = os.environ.get("IBM_QUANTUM_BACKEND", "ibm_marrakesh")
EXPECTED_LAYOUT = [125, 117, 126, 124, 123, 122, 136]
CHECKPOINTS = [0, 4, 8, 12, 16, 20, 24, 28, 32]
ARMS = ["sync", "nosync"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


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


def run_checks() -> int:
    print("=" * 72)
    print("triangle-anchor-memory — DUAL-WHEEL MESH BEKÜLDŐ ELLENŐRZŐ (v1.0, check-only)")
    print("=" * 72)

    frozen_json = REPO_ROOT / "preregistration" / "frozen_dual_wheel_params.json"
    frozen_sha = REPO_ROOT / "preregistration" / "frozen_dual_wheel_params.sha256"
    if not (frozen_json.exists() and frozen_sha.exists()):
        print(f"[FAIL] hiányzik a fagyasztott fájl!")
        return 1

    actual_h = sha256_file(frozen_json)
    recorded_h = None
    for line in frozen_sha.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1] == "frozen_dual_wheel_params.json":
            recorded_h = parts[0]
            break

    if actual_h != recorded_h:
        print(f"[FAIL] hash eltérés: {actual_h} != {recorded_h}")
        return 1
    print(f"[PASS] frozen integritás OK — SHA-256: {actual_h}")
    print(f"[PASS] cél backend: {EXPECTED_BACKEND}, layout (7Q): {EXPECTED_LAYOUT}")

    # Áramkörök mérés-kapu ellenőrzése
    for arm in ARMS:
        for k in CHECKPOINTS:
            qc = build_dual_wheel_circuit(k, init_s1=True, init_s2=False, sync_coupling=(arm == "sync"))
            meas_count = sum(1 for inst in qc.data if inst.operation.name == "measure")
            if meas_count < 2:
                print(f"[FAIL] hiányzó mérés az áramkörben: {arm} k={k}")
                return 1

    print(f"[PASS] mérés-kapu OK: mind a 18 áramkör tartalmaz 2 végmérést (S1, S2)")
    print("=" * 72)
    print("ÖSSZESÍTÉS: MINDEN BEKÜLDÉSI KAPU PASS — QPU NEM INDULT (check-only).")
    print("=" * 72)
    return 0


def do_submit(confirmed: bool = False, shots: int = 512) -> int:
    token = get_token()
    if not token:
        print("LEÁLL: nincs token!")
        return 1

    rc = run_checks()
    if rc != 0:
        print("LEÁLL: kapuk nem zöldek!")
        return rc

    print(f"FIGYELEM: Ez a parancs VALÓDI {shots} lövéses QPU-futtatást indít a Dual-Wheel Mesh-re a(z) {EXPECTED_BACKEND} chipen!")
    if not confirmed:
        if not sys.stdin.isatty():
            print("LEÁLL: Nem interaktív terminál — használd a --confirm kapcsolót!")
            return 1
        ans = input("A beküldés megerősítéséhez írd be pontosan: DUAL WHEEL BEKULDES → ").strip()
        if ans != "DUAL WHEEL BEKULDES":
            print("Megszakítva.")
            return 1

    print("Qiskit Runtime Service inicializálása...")
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    from qiskit import transpile

    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token, instance="open-instance")
    backend = service.backend(EXPECTED_BACKEND)
    status = backend.status()
    print(f"Élő backend csatlakozva: {backend.name} (operational: {status.operational}, pending: {status.pending_jobs})")

    print(f"18 Dual-Wheel áramkör transzpilálása az élő backendhez ({backend.name})...")
    circuits_to_run = []
    order = []
    for arm in ARMS:
        for k in CHECKPOINTS:
            cid = f"{arm}|k{k}"
            qc = build_dual_wheel_circuit(k, init_s1=True, init_s2=False, sync_coupling=(arm == "sync"))
            t_qc = transpile(qc, backend=backend, initial_layout=EXPECTED_LAYOUT, optimization_level=0)
            circuits_to_run.append(t_qc)
            order.append(cid)

    sampler = SamplerV2(mode=backend)
    submitted_at = datetime.now(timezone.utc).isoformat()
    print(f"Beküldés az IBM sorba ({len(circuits_to_run)} áramkör, {shots} shot)...", flush=True)
    job = sampler.run(circuits_to_run, shots=shots)
    jid = job.job_id()
    print(f"Sikeres beküldés! Job ID: {jid}")

    # RECORD-FIRST
    meta = {
        "status": "BEKÜLDVE — FUTÁSRA VÁR",
        "job_id": jid,
        "backend": backend.name,
        "submitted_at": submitted_at,
        "shots": shots,
        "circuit_count": len(circuits_to_run),
        "layout": EXPECTED_LAYOUT,
        "order": order,
        "arms": ARMS,
        "checkpoints": CHECKPOINTS,
        "frozen_file": "preregistration/frozen_dual_wheel_params.json",
        "note": f"Dual-Wheel Mesh beküldve az {backend.name}-ra ({len(circuits_to_run)} áramkör, {shots} shot)."
    }

    Path("data/dual_wheel_job_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    rec_dir = Path("submission/dual_wheel")
    rec_dir.mkdir(parents=True, exist_ok=True)
    (rec_dir / "job_id_record.json").write_text(json.dumps({"job_id": jid, "submitted_at": submitted_at, "backend": backend.name}, indent=2), encoding="utf-8")

    print("=" * 72)
    print("RECORD-FIRST RÖGZÍTVE: data/dual_wheel_job_meta.json")
    print(f"JOB ID: {jid}")
    print(f"A job a sorban áll az {backend.name}-on.")
    print("=" * 72)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Dual-Wheel Mesh beküldő")
    parser.add_argument("--check-only", action="store_true", help="Csak ellenőrzés")
    parser.add_argument("--submit", action="store_true", help="QPU beküldés")
    parser.add_argument("--confirm", action="store_true", help="Megerősítés")
    parser.add_argument("--shots", type=int, default=512, help="Lövések száma (alapértelmezett: 512)")
    args = parser.parse_args()

    if args.submit:
        return do_submit(confirmed=args.confirm, shots=args.shots)
    return run_checks()


if __name__ == "__main__":
    raise SystemExit(main())
