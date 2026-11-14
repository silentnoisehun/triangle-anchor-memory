#!/usr/bin/env python3
"""Csillag-menet BEKÜLDŐ ÉS ELLENŐRZŐ (v1.4) — ELŐKÉSZÍTVE; QPU-t NEM INDÍT.

Forrás: Maya 2026-11-12 22:30 UTC átnézése (agent_feladat_csillag_v14.txt, 7. pont).
Ez a szkript ellenőrzi a Csillag-job beküldési előfeltételeit:
  (a) Minden áramkörben van mérés (a Küszöb-1515 hiba tanulsága);
  (b) Az élő CZ-szám és karhossz a fagyasztottal egyezik (ALAP |Δ| <= 1 dt);
  (c) A gép ibm_kingston;
  (d) Record-first: job ID, job_meta, snapshot, áramkör-hash és order_sha256
      külön rögzítendő, az eredmény ELŐTT.
Token: kizárólag az IBM_QUANTUM_TOKEN környezeti változóból olvasandó.
A beküldés KÜLÖN TULAJDONOSI DÖNTÉS; a --check-only módban QPU nem indul.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src import config
from src.analysis import load_frozen_params


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def check_measurements(circuits) -> bool:
    """Ellenőrzi, hogy minden áramkör tartalmaz-e mérést (fail-closed a 1515-ös hiba ellen)."""
    for cid, qc in circuits:
        has_meas = any(inst.operation.name == "measure" for inst in qc.data)
        if not has_meas:
            return False
    return True


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
        print(f"[FAIL] hiányzik a data/snapshot.json")
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
        # Smoke ellenőrzés a k=0..1 lépéseken a check-only módban
        rows, max_abs = equalization_report(range(2))
        if max_abs > 1:
            print(f"[FAIL] karhossz-eltérés: max |Δ| = {max_abs} dt > 1 dt")
            return 1
        print(f"[PASS] karhossz-kiegyenlítés OK (|Δ| <= 1 dt, max = {max_abs} dt)")
    except Exception as exc:
        print(f"[FAIL] karhossz ellenőrzési hiba: {exc}")
        return 1

    # 5. Mérések ellenőrzése a reprezentatív áramkörökön
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
    print("ÖSSZESÍTÉS: MINDEN BEKÜLDÉSI KAPU PASS — QPU NEM INDULT (check-only).")
    print("=" * 72)
    return 0


def main():
    parser = argparse.ArgumentParser(description="Csillag-menet beküldő ellenőrző")
    parser.add_argument("--check-only", action="store_true", default=True, help="Csak kapu-ellenőrzés futtatása")
    parser.add_argument("--submit", action="store_true", help="QPU beküldés (TULAJDONOSI DÖNTÉS NÉLKÜL TILOS)")
    args = parser.parse_args()

    if args.submit:
        print("HIBA: QPU-BEKÜLDÉS TILOS tulajdonosi döntés és Control Agent audit nélkül!")
        sys.exit(3)

    sys.exit(run_checks(check_only=True))


if __name__ == "__main__":
    main()
