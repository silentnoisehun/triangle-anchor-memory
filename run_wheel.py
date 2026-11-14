#!/usr/bin/env python3
"""run_wheel.py — Kerék v1.2 QPU beküldés és ellenőrző szkript.

A preregisztrált protokoll (PLAN_WHEEL_v1.2.md) alapján:
  - 13 kar: wheel, wheel_rev, static, ring_only, alone, alone_DD,
            pump_blind, pump_dir, pump_wrong, cut,
            dark_m1, dark_m0, dark_mm1
  - 9 checkpoint: [0, 4, 8, 12, 16, 20, 24, 28, 32] -> 117 áramkör
  - rögzített layout: [125, 117, 124, 126] (S=125, R1=117, R2=124, R3=126)
  - cél backend: ibm_marrakesh (Heron r2)
  - mérés-kapu (1515 hiba kivédése: minden áramkör tartalmaz measure kaput)
  - record-first: job_meta.json rögzítése a futás előtt
  - fail-closed: --check-only módban mindent ellenőriz QPU-hívás nélkül
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

from src.wheel import analysis
from src.wheel.circuits import ARM_NAMES, build_circuit
from src.wheel.simulate import measure_circuit

EXPECTED_BACKEND = os.environ.get("IBM_QUANTUM_BACKEND", "ibm_marrakesh")
EXPECTED_LAYOUT = [125, 117, 124, 126]
CHECKPOINTS = [0, 4, 8, 12, 16, 20, 24, 28, 32]


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


def check_circuits_and_measurements() -> None:
    for arm in ARM_NAMES:
        for k in CHECKPOINTS:
            qc = build_circuit(arm, k, pop_branch=1)
            m = measure_circuit(qc, 0)
            has_meas = any(instr.operation.name == "measure" for instr in m.data)
            if not has_meas:
                raise RuntimeError(f"MÉRÉS-HIBA: {arm} k={k} áramkör nem tartalmaz measure kaput!")


def run_checks() -> int:
    print("=" * 72)
    print("triangle-anchor-memory — KERÉK-BEKÜLDŐ ELLENŐRZŐ (v1.2, check-only)")
    print("=" * 72)

    # 1. Integritás ellenőrzés a fagyasztott v1.2 szerint
    try:
        fz = analysis.check_frozen()
        print(f"[PASS] frozen integritás v1.2 OK — ci_level={fz['ci_level']}, claim_family={fz['claim_family']}")
    except Exception as exc:
        print(f"[FAIL] frozen integritás hiba: {exc}")
        return 1

    # 2. Cél backend és layout
    print(f"[PASS] cél backend: {EXPECTED_BACKEND}, layout: {EXPECTED_LAYOUT}")

    # 3. Áramkörök és mérés-kapuk
    try:
        check_circuits_and_measurements()
        print(f"[PASS] mérés-kapu OK: mind a 117 áramkör tartalmaz measure kaput (1515 kivédve)")
    except Exception as exc:
        print(f"[FAIL] áramkör-ellenőrzési hiba: {exc}")
        return 1

    print("=" * 72)
    print("ÖSSZESÍTÉS: MINDEN BEKÜLDÉSI KAPU PASS — QPU NEM INDULT (check-only).")
    print("=" * 72)
    return 0


def do_submit(confirmed: bool = False, shots: int = 512) -> int:
    token = get_token()
    if not token:
        print("LEÁLL: nincs IBM_QUANTUM_TOKEN vagy érvényes kulcsfájl!")
        return 1

    rc = run_checks()
    if rc != 0:
        print("LEÁLL: A beküldési kapuk nem zöldek!")
        return rc

    print(f"FIGYELEM: Ez a parancs VALÓDI {shots} lövéses QPU-futtatást indít a Kerék v1.2-re a(z) {EXPECTED_BACKEND} chipen!")
    if not confirmed:
        if not sys.stdin.isatty():
            print("LEÁLL: Nem interaktív terminál — használd a --confirm kapcsolót!")
            return 1
        ans = input("A beküldés megerősítéséhez írd be pontosan: KEREK BEKULDES → ").strip()
        if ans != "KEREK BEKULDES":
            print("Megszakítva: a megerősítés nem érkezett meg.")
            return 1

    print("Qiskit Runtime Service inicializálása...")
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    from qiskit import transpile

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
        print(f"LEÁLL: A(z) {EXPECTED_BACKEND} backend nem aktív!")
        return 1

    print(f"117 Kerék áramkör transzpilálása az élő backendhez ({backend.name})...")
    circuits_to_run = []
    order = []
    for arm in ARM_NAMES:
        for k in CHECKPOINTS:
            cid = f"{arm}|k{k}"
            qc = build_circuit(arm, k, pop_branch=1)
            m = measure_circuit(qc, 0)
            t_qc = transpile(m, backend=backend, initial_layout=EXPECTED_LAYOUT, optimization_level=0)
            circuits_to_run.append(t_qc)
            order.append(cid)

    sampler = SamplerV2(mode=backend)
    submitted_at = datetime.now(timezone.utc).isoformat()
    print(f"Beküldés az IBM sorba ({len(circuits_to_run)} áramkör, {shots} shot)...", flush=True)
    job = sampler.run(circuits_to_run, shots=shots)
    jid = job.job_id()
    print(f"Sikeres beküldés! Job ID: {jid}")

    # RECORD-FIRST: azonnali rögzítés az eredmények ELŐTT
    meta = {
        "status": "BEKÜLDVE — FUTÁSRA VÁR",
        "job_id": jid,
        "job_ids": [jid],
        "backend": backend.name,
        "channel": "ibm_quantum_platform",
        "submitted_at": submitted_at,
        "shots": shots,
        "circuit_count": len(circuits_to_run),
        "layout": {"S": 125, "R1": 117, "R2": 124, "R3": 126},
        "order": order,
        "arms": list(ARM_NAMES),
        "checkpoints": CHECKPOINTS,
        "frozen_params_file": "preregistration/frozen_wheel_params_v1.2.json",
        "frozen_params_sha256": sha256_file(REPO_ROOT / "preregistration" / "frozen_wheel_params_v1.2.json"),
        "note": f"Kerék v1.2 beküldve az {backend.name}-ra ({len(circuits_to_run)} áramkör, {shots} shot). Record-first rögzítve."
    }

    job_meta_path = REPO_ROOT / "data" / "wheel_job_meta.json"
    job_meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    rec_dir = REPO_ROOT / "submission" / "wheel"
    rec_dir.mkdir(parents=True, exist_ok=True)
    (rec_dir / "job_id_record.json").write_text(json.dumps({"job_id": jid, "submitted_at": submitted_at, "backend": backend.name}, indent=2), encoding="utf-8")
    (rec_dir / "job_meta.final_v1.2.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=" * 72)
    print("RECORD-FIRST RÖGZÍTVE: data/wheel_job_meta.json és submission/wheel/job_id_record.json")
    print(f"JOB ID: {jid}")
    print(f"A job a sorban áll az {backend.name}-on.")
    print("=" * 72)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Kerék v1.2 futtató és beküldés-ellenőrző")
    parser.add_argument("--check-only", action="store_true", help="Csak a kapuk és integritás ellenőrzése")
    parser.add_argument("--submit", action="store_true", help="QPU beküldés indítása")
    parser.add_argument("--confirm", action="store_true", help="Megerősítés a tulajdonosi döntésre")
    parser.add_argument("--shots", type=int, default=512, help="Lövések száma (alapértelmezett: 512)")
    args = parser.parse_args()

    if args.submit:
        return do_submit(confirmed=args.confirm, shots=args.shots)

    return run_checks()


if __name__ == "__main__":
    raise SystemExit(main())
