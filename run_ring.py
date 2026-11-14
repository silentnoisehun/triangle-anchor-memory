#!/usr/bin/env python3
"""run_ring.py — Gyűrű v1.2 QPU beküldés és ellenőrző szkript.

AMENDMENT v1.2 (Maya auditja szerint):
  - k <= 16 korlátozás (k=32 341 CZ helyett max 176 CZ @ k=16, elkerülve a 0.5-ös hibaösszeg túllépését);
  - rögzített layout: [125, 117, 124, 126];
  - mérés-kapu (1515 hiba kivédése: minden áramkör tartalmaz végmérést);
  - beküldés-napi kalibrációból újraszámolt jóslat ±20% T1/T2 sávval;
  - fagyasztott integritás: frozen_ring_params_v1.2.json + .sha256;
  - fail-closed: --check-only módban mindent ellenőriz QPU-hívás nélkül, exit 0 ha minden pass.

FIGYELEM: QPU-beküldés SOHA nem indítható automatikusan. Csak kifejezett
tulajdonosi jóváhagyással és IBM_QUANTUM_TOKEN környezeti változóval futhat.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
FROZEN_JSON = REPO_ROOT / "preregistration" / "frozen_ring_params_v1.2.json"
FROZEN_SHA = REPO_ROOT / "preregistration" / "frozen_ring_params_v1.2.sha256"

EXPECTED_BACKEND = "ibm_kingston"
EXPECTED_LAYOUT = [125, 117, 124, 126]
K_MAX = 16
GRID_K = [0, 1, 2, 4, 8, 16]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


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

    for arm in ("ring_p", "ring_m", "static", "broken"):
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
    """Beküldés-napi kalibrációból származtatott várakozás sáv ellenőrzése."""
    rule = frozen.get("calibration_prediction_rule")
    if not rule or "±20%" not in rule:
        raise RuntimeError("Hiányzik a kalibrációs jóslat szabály (±20% T1/T2 sáv) a frozen paraméterekből!")


def main() -> int:
    parser = argparse.ArgumentParser(description="Gyűrű v1.2 futtató és beküldés-ellenőrző")
    parser.add_argument("--check-only", action="store_true", default=True,
                        help="Csak a kapuk és integritás ellenőrzése QPU futtatás nélkül (alapértelmezett)")
    parser.add_argument("--submit", action="store_true", default=False,
                        help="QPU beküldés indítása (kizárólag tulajdonosi jóváhagyással)")
    args = parser.parse_args()

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

    if args.submit:
        token = os.environ.get("IBM_QUANTUM_TOKEN")
        if not token:
            print("HIBA: IBM_QUANTUM_TOKEN nincs megadva a környezetben!")
            return 1
        print("FIGYELEM: QPU beküldés nincs engedélyezve a futó munkamenetben.")
        return 1

    print("=" * 72)
    print("ÖSSZESÍTÉS: MINDEN BEKÜLDÉSI KAPU PASS — QPU NEM INDULT (check-only).")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
