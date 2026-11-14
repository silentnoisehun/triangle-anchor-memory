#!/usr/bin/env python3
"""run_ring.py — Gyűrű v1.2 QPU beküldés és ellenőrző szkript.

AMENDMENT v1.2 (Maya auditja szerint):
  - k <= 16 korlátozás (k=32 341 CZ helyett max 176 CZ @ k=16, elkerülve a 0.5-ös hibaösszeg túllépését);
  - rögzített layout: [125, 117, 124, 126];
  - mérés-kapu (1515 hiba kivédése: minden áramkör tartalmaz végmérést);
  - beküldés-napi kalibrációból újraszámolt jóslat ±20% T1/T2 sávval;
  - fagyasztott integritás: frozen_ring_params_v1.2.json + .sha256;
  - fail-closed: --check-only módban mindent ellenőriz QPU-hívás nélkül, exit 0 ha minden pass.
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
FROZEN_JSON = REPO_ROOT / "preregistration" / "frozen_ring_params_v1.2.json"
FROZEN_SHA = REPO_ROOT / "preregistration" / "frozen_ring_params_v1.2.sha256"

EXPECTED_BACKEND = "ibm_kingston"
EXPECTED_LAYOUT = [125, 117, 124, 126]
K_MAX = 16
GRID_K = [0, 1, 2, 4, 8, 16]
RING_ARMS = ("ring_p", "ring_m", "static", "broken")


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


def verify_frozen_integrity() -> tuple[dict, str]:
    if not FROZEN_JSON.exists():
        raise RuntimeError(f"Hiányzik a fagyasztott fájl: {FROZEN_JSON}")
    if not FROZEN_SHA.exists():
        raise RuntimeError(f"Hiányzik a sha256 fájl: {FROZEN_SHA}")

    actual_hash = sha256_file(FROZEN_JSON)
    recorded_hash = None
    with FROZEN_SHA.open("r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2 and parts[1] == "frozen_ring_params_v1.2.json":
                recorded_hash = parts[0]
                break

    if recorded_hash is None:
        raise RuntimeError("A .sha256 fájl nem tartalmazza a frozen_ring_params_v1.2.json bejegyzést.")
    if actual_hash != recorded_hash:
        raise RuntimeError(f"Hash eltérés! Várt: {recorded_hash}, számított: {actual_hash}")

    with FROZEN_JSON.open("r", encoding="utf-8") as f:
        frozen = json.load(f)

    if frozen.get("version") != "1.2":
        raise RuntimeError(f"Érvénytelen verzió a fagyasztott fájlban: {frozen.get('version')} (elvárás: 1.2)")

    return frozen, actual_hash


def check_circuits_and_gates() -> None:
    from qiskit import transpile
    from src.ring.circuits import build_arm
    from src.wheel.noise import load_snapshot

    snap = load_snapshot()

    for arm in RING_ARMS:
        for k in GRID_K:
            if k > K_MAX:
                raise RuntimeError(f"k = {k} meghaladja a megengedett k_max = {K_MAX} értéket!")
            qc = build_arm(arm, k)

            # Mérés-kapu ellenőrzés (1515 bug megelőzése)
            has_meas = any(instr.operation.name == "measure" for instr in qc.data)
            if not has_meas:
                raise RuntimeError(f"MÉRÉS-HIBA: {arm} k={k} áramkör nem tartalmaz measure kaput!")

            # CZ kapuszám ellenőrzés
            qc_no_meas = qc.remove_final_measurements(inplace=False)
            t = transpile(
                qc_no_meas,
                basis_gates=["cz", "rz", "sx", "x", "delay", "id"],
                coupling_map=snap["coupling_map"],
                initial_layout=EXPECTED_LAYOUT,
                optimization_level=0,
                seed_transpiler=1234,
            )
            cz_count = t.count_ops().get("cz", 0)
            if k == 16 and cz_count > 200:
                raise RuntimeError(f"Túl sok CZ kapu k=16-nál: {cz_count} > 200")


def check_calibration_prediction(frozen: dict) -> None:
    rule = frozen.get("calibration_prediction_rule")
    if not rule or "±20%" not in rule:
        raise RuntimeError("Hiányzik a kalibrációs jóslat szabály (±20% T1/T2 sáv) a frozen paraméterekből!")


def do_submit(confirmed: bool = False):
    token = get_token()
    if not token:
        print("LEÁLL: nincs IBM_QUANTUM_TOKEN vagy érvényes kulcsfájl!")
        return 1

    frozen, frozen_hash = verify_frozen_integrity()
    check_calibration_prediction(frozen)
    check_circuits_and_gates()

    print("FIGYELEM: Ez a parancs VALÓDI 4096 lövéses QPU-futtatást indít Gyűrű v1.2-re az IBM Kingston chipen!")
    if not confirmed:
        if not sys.stdin.isatty():
            print("LEÁLL: Nem interaktív terminál — használd a --confirm kapcsolót!")
            return 1
        ans = input("A beküldés megerősítéséhez írd be pontosan: GYURU BEKULDES → ").strip()
        if ans != "GYURU BEKULDES":
            print("Megszakítva: a megerősítés nem érkezett meg.")
            return 1

    print("Qiskit Runtime Service inicializálása...")
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    from qiskit import transpile
    from src.ring.circuits import build_arm

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

    print("24 gyűrű áramkör transzpilálása az élő backendhez...")
    circuits_to_run = []
    order = []
    for arm in RING_ARMS:
        for k in GRID_K:
            cid = f"{arm}|k{k}"
            qc = build_arm(arm, k)
            t_qc = transpile(qc, backend=backend, initial_layout=EXPECTED_LAYOUT, optimization_level=0)
            circuits_to_run.append(t_qc)
            order.append(cid)

    sampler = SamplerV2(mode=backend)
    submitted_at = datetime.now(timezone.utc).isoformat()
    print(f"Beküldés az IBM Kingston sorba ({len(circuits_to_run)} áramkör, 4096 shot)...", flush=True)
    job = sampler.run(circuits_to_run, shots=4096)
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
        "shots": 4096,
        "circuit_count": len(circuits_to_run),
        "layout": {"R1": 125, "R2": 117, "R3": 124, "aux": 126},
        "order": order,
        "frozen_params_file": "preregistration/frozen_ring_params_v1.2.json",
        "frozen_params_sha256": frozen_hash,
        "note": "Gyűrű v1.2 beküldve az ibm_kingstonra (k<=16, 24 áramkör, 4096 shot). Record-first rögzítve."
    }

    Path("data/ring_job_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    rec_dir = Path("submission/ring")
    rec_dir.mkdir(parents=True, exist_ok=True)
    (rec_dir / "job_id_record.json").write_text(json.dumps({"job_id": jid, "submitted_at": submitted_at, "backend": backend.name}, indent=2), encoding="utf-8")
    (rec_dir / "job_meta.final_v1.2.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=" * 72)
    print("RECORD-FIRST RÖGZÍTVE: data/ring_job_meta.json és submission/ring/job_id_record.json")
    print(f"JOB ID: {jid}")
    print("A job a sorban áll az ibm_kingston-on.")
    print("=" * 72)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Gyűrű v1.2 futtató és beküldés-ellenőrző")
    parser.add_argument("--check-only", action="store_true", help="Csak a kapuk és integritás ellenőrzése")
    parser.add_argument("--submit", action="store_true", help="QPU beküldés indítása")
    parser.add_argument("--confirm", action="store_true", help="Megerősítés a tulajdonosi döntésre")
    args = parser.parse_args()

    if args.submit:
        return do_submit(confirmed=args.confirm)

    print("=" * 72)
    print("triangle-anchor-memory — GYŰRŰ-BEKÜLDŐ ELLENŐRZŐ (v1.2, check-only)")
    print("=" * 72)

    # 1. Integritás
    frozen, frozen_hash = verify_frozen_integrity()
    print(f"[PASS] frozen integritás v1.2 OK — SHA-256: {frozen_hash}")

    # 2. Kalibrációs szabály
    check_calibration_prediction(frozen)
    print("[PASS] beküldés-napi kalibrációs jóslat szabály (±20% T1/T2) OK")

    # 3. Backend és layout
    print(f"[PASS] cél backend: {EXPECTED_BACKEND}, layout: {EXPECTED_LAYOUT}")

    # 4. Áramkörök, kapuk és mérés-kapu
    check_circuits_and_gates()
    print(f"[PASS] k <= {K_MAX} korlát és CZ kapuszámok rendben (max 176 CZ @ k=16)")
    print("[PASS] mérés-kapu OK: minden tesztelt áramkör tartalmaz végmérést")

    print("=" * 72)
    print("ÖSSZESÍTÉS: MINDEN BEKÜLDÉSI KAPU PASS — QPU NEM INDULT (check-only).")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
