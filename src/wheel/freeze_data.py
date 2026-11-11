"""A frozen_wheel_params.json számszerű tartalmának (re)generálása.

A 0. fázis eredményei — Aer/noiseless számok (NEM hardver). A fagyasztott
fájl ezekkel a számokkal jön létre; a script dokumentálja, hogyan.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, ROOT)

from src.wheel.circuits import (ARM_NAMES, ARM_DEFS, K, PHI, PHI_F, THETA_SP,
                                T_HOLD_NS, SPOKE_PHASES, k_checkpoints,
                                logical_two_qubit_count)
from src.wheel.prep import prep_angles, CIRCULATION
from src.wheel.simulate import transpile_routed, run_noisy_counts, run_ideal_state

SHOTS = 4096
SEED_AER = 2026
POSITIVE_CONTROL_EPS = 0.15


def main():
    t0 = time.time()
    ks = k_checkpoints()
    out = {"checkpoints": ks}

    # 1) kaputilus-tábla karonként (logikai slot + CX-ekvivalens + routolt CZ)
    table = {}
    for arm in ARM_NAMES:
        qc_stats = None
        try:
            _, used, stats = transpile_routed(arm, K)
            two_q_routed = stats["two_q"]
            s_final = stats["s_final_phys"]
            routed_depth = stats["depth"]
        except Exception as exc:  # routolás sikertelen (pl. alone — triviális)
            two_q_routed, s_final, routed_depth = None, None, None
        logical = logical_two_qubit_count(arm, K)
        table[arm] = {
            "logical_2q_slots": logical,
            "cx_equivalent": logical * 2,
            "routed_cz": two_q_routed,
            "routed_depth": routed_depth,
            "s_final_phys": s_final,
        }
        print(f"  {arm:12s} routed CZ={two_q_routed}  depth={routed_depth}", flush=True)
    out["gate_count_table"] = table

    # 2) Aer zajos jóslat a ROUTED áramkörökre (shots=4096, seed=2026) — minden kar pop=1 ágon
    from qiskit_aer import AerSimulator
    from qiskit import ClassicalRegister, transpile
    from src.wheel.noise import build_noise_model_physical
    pred = {}
    for arm in ARM_NAMES:
        sub, used, stats = transpile_routed(arm, K)
        s_idx = used.index(stats["s_final_phys"])
        # a teljes görbe: ellenpontonként újra transzpilálva (a P(S=1) k-függő)
        curve = []
        for k in ks:
            sub, used, stats = transpile_routed(arm, k, pop_branch=1)
            nm = build_noise_model_physical(used)
            sim = AerSimulator(noise_model=nm)
            m = sub.copy()
            cr = ClassicalRegister(1, "c")
            m.add_register(cr)
            m.measure(used.index(stats["s_final_phys"]), cr)
            r = sim.run(m, shots=SHOTS, seed_simulator=SEED_AER).result()
            c = r.get_counts()
            curve.append({"k": k, "p_s1": c.get("1", 0) / SHOTS})
        auc = float(np.mean([p["p_s1"] for p in curve]))
        var_auc = float(np.mean([p["p_s1"] * (1 - p["p_s1"]) / SHOTS for p in curve]) / len(curve))
        pred[arm] = {"curve": [p["p_s1"] for p in curve],
                     "auc": auc,
                     "auc_std": math.sqrt(var_auc)}
        print(f"  Aer(routed) {arm:12s} AUC={auc:.4f} ± {math.sqrt(var_auc):.4f}", flush=True)
    out["aer_prediction"] = pred

    # 3) noiseless görbék (referenciaként; a döntésbe nem számít)
    ideal = run_ideal_state(ARM_NAMES, ks, pop_branch=1)
    out["noiseless_curves_population"] = ideal

    # 4) pozitív kontroll (EPS_RESTORE=0.15 Ry/lépés) — szimulációs diagnosztika
    pc = {}
    for k in ks:
        from src.wheel.circuits import build_circuit
        from src.wheel.simulate import measure_circuit
        from src.wheel.noise import build_noise_model
        qc = build_circuit("wheel", k, pop_branch=1, positive_control=True)
        m = measure_circuit(qc, 0)
        nm = build_noise_model()
        sim = AerSimulator(noise_model=nm)
        r = sim.run(m, shots=SHOTS, seed_simulator=SEED_AER + 7).result().get_counts()
        pc[k] = r.get("1", 0) / SHOTS
    out["positive_control_curve"] = [pc[k] for k in ks]
    out["positive_control_auc"] = float(np.mean(list(pc.values())))

    # 5) prep-szögek és circulation-normalizálás (dokumentálva)
    out["prep_angles"] = {str(m): list(prep_angles(m)) for m in (1, 0, -1)}
    out["circulation_norms"] = {str(m): float(np.linalg.norm(CIRCULATION[m])) for m in (1, 0, -1)}

    print(f"kész ({time.time()-t0:.1f}s)")
    path = os.path.join(ROOT, "data", "wheel_freeze_data.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print("mentve:", path)


if __name__ == "__main__":
    main()
