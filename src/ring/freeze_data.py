#!/usr/bin/env python3
"""A 0. fázis szimulációs futtatása + frozen_ring_params.json generálása.

EGYSZERI alkalommal fut (a fagyasztás egyszeri esemény). QPU-t NEM érint.
Kimenetek:
  data/ring_freeze_data.json  — minden görbe (exact + native-Aer + routed-Aer)
  preregistration/frozen_ring_params.json (utána .sha256)
"""
from __future__ import annotations
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.ring.config import (STEP_GRID, SHOTS, BOOTSTRAP_N, BOOTSTRAP_SEED,
                             CI_LEVEL, CORRECTION, CLAIM_FAMILY, PHI, PHI_F,
                             PUMP_M, PUMP_FI_P, PUMP_KICK_P, TAU_CROSS, K)
from src.ring.simulate import (exact_reference, run_noisy, omega_from_round_spectrum)
from src.ring.circuits import build_arm

SEED = 20261111
SMOKE_SHOTS = 2048   # a szimulációs előrejelzések 2048 shottal (a valódi job 4096-tal menne)


def signal_from_counts(counts, arm):
    tot = sum(counts.values())
    if arm in ("lone", "delayed", "star"):
        return counts.get("1", 0) / tot
    return counts.get("000", 0) / tot


def tau_from_curve(grid, values, cross=TAU_CROSS):
    """τ: az első k, ahol a görbe < cross — lineáris interpolációval."""
    prev_k, prev_v = grid[0], values[0]
    for k, v in zip(grid, values):
        if v < cross:
            if k == prev_k:
                return float(k)
            frac = (prev_v - cross) / (prev_v - v)
            return float(prev_k + frac * (k - prev_k))
        prev_k, prev_v = k, v
    return float("inf")


def main():
    print("=== 0. fázis: spektrum (Ω) ===")
    spec = omega_from_round_spectrum(PHI_F)
    OMEGA = spec["omega_rad_per_round"]
    print(f"Omega = {OMEGA:.6f} rad/kör; eigenphases = {spec['eigenphases']}")

    data = {"kind": "RING 0. FAZIS — AER/STATEVECTOR, NEM HARDWARE",
            "omega_rad_per_round": OMEGA, "omega_detail": spec,
            "grid": list(STEP_GRID), "shots_noisy_sim": SMOKE_SHOTS,
            "exact": {}, "native": {}, "routed": {}, "pump": {}}

    ARMS_BASE = ["ring_p", "ring_m", "ring_0", "static", "broken",
                 "star", "lone", "delayed"]
    for arm in ARMS_BASE:
        data["exact"][arm] = {str(k): exact_reference(arm, k)["p_measure_exact"] for k in STEP_GRID}
        print("exact", arm, {k: round(v, 4) for k, v in data["exact"][arm].items()}, flush=True)

    print("\n=== zajos (native) ===")
    for arm in ARMS_BASE:
        data["native"][arm] = {}
        for k in STEP_GRID:
            r = run_noisy(arm, k, "native", SMOKE_SHOTS, SEED)
            data["native"][arm][str(k)] = signal_from_counts(r["counts"], arm)
        print("native", arm, {k: round(v, 4) for k, v in data["native"][arm].items()}, flush=True)

    print("\n=== zajos (routed) ===")
    for arm in ["ring_p", "ring_m", "ring_0", "static", "broken", "star"]:
        data["routed"][arm] = {}
        for k in STEP_GRID:
            r = run_noisy(arm, k, "routed", SMOKE_SHOTS, SEED)
            data["routed"][arm][str(k)] = signal_from_counts(r["counts"], arm)
        print("routed", arm, {k: round(v, 4) for k, v in data["routed"][arm].items()}, flush=True)

    print("\n=== pump scan (native + routed) ===")
    for m in PUMP_M:
        for fi in PUMP_FI_P:
            key = f"m{m}_fi{fi:.4f}"
            data["pump"][key] = {"m": m, "fi_p": fi, "native": {}, "routed": {},
                                  "exact": {}, "kick_error_total": 3 * K * PUMP_KICK_P * (1 if m > 0 else 0)}
            for k in STEP_GRID:
                data["pump"][key]["exact"][str(k)] = exact_reference("pump", k, pump_m=m, pump_fi=fi, omega=OMEGA)["p_measure_exact"]
            for k in STEP_GRID:
                r = run_noisy("pump", k, "native", SMOKE_SHOTS, SEED, pump_m=m, pump_fi=fi, omega=OMEGA)
                data["pump"][key]["native"][str(k)] = signal_from_counts(r["counts"], "pump")
            for k in STEP_GRID:
                r = run_noisy("pump", k, "routed", SMOKE_SHOTS, SEED, pump_m=m, pump_fi=fi, omega=OMEGA)
                data["pump"][key]["routed"][str(k)] = signal_from_counts(r["counts"], "pump")
            print("pump", key,
                  "native", {k: round(v, 3) for k, v in data["pump"][key]["native"].items()},
                  flush=True)

    # τ becslések — kizárólag a "nagyobb = jobb" görbékre:
    def curve(section, arm):
        return [section[arm][str(k)] for k in STEP_GRID]

    def retention_curve(section, arm):
        vals = curve(section, arm)
        if arm == "ring_m":
            return [1.0 - v for v in vals]   # F− = 1 − P000
        if arm == "ring_0":
            return None                       # report-only, nincs τ
        return vals

    data["tau"] = {}
    for section in ("exact", "native", "routed"):
        data["tau"][section] = {}
        for arm in ARMS_BASE:
            if arm in data[section]:
                vals = retention_curve(data[section], arm)
                if vals is None:
                    continue
                data["tau"][section][arm] = tau_from_curve(list(STEP_GRID), vals)
    # C(k) a ± ágból
    data["contrast"] = {}
    for section in ("exact", "native", "routed"):
        rp = data[section].get("ring_p"); rm = data[section].get("ring_m")
        if rp and rm:
            data["contrast"][section] = {str(k): rp[str(k)] - rm[str(k)] for k in STEP_GRID}
            vals = [data["contrast"][section][str(k)] for k in STEP_GRID]
            data["tau"][section]["contrast"] = tau_from_curve(list(STEP_GRID), vals)

    out_json = os.path.join(os.path.dirname(__file__), "..", "..", "data", "ring_freeze_data.json")
    with open(out_json, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\nAdatmentve: {out_json}")
    print("τ (kör):", json.dumps(data["tau"], indent=1))
    return data


if __name__ == "__main__":
    main()
