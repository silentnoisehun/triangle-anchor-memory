"""W3 — flux-locking küszöb (fáziszár-kuszöb) számítása a TÉNYLEGES layouton.

A terv előre rögzített, fagyasztott W3-tesztje (PLAN_WHEEL_v1.1, javítás #2 +
kiegészítés #2 SZETESESO-forgatókönyv): a 0. fázis számolja ki; ha a
szeteso tartomany jön ki, a teljes QPU-job NEM mehet ki — csak a kis
kuszöb-job (gyűrű önmagában, néhány lépés) tervezhető; a kerék-állitas a
következő, erősebb csatolasu qubit-negyesre vár.

A számitas a snapshot (data/snapshot.json) MERT paramétereit használja:
  - S–A1/A2/A3 él-hibák (mértek);
  - A1/A2/A3 eps_2q (a gyűrű-élek NINCSENEK mérve — eps_2q összegek);
  - T1/T2 minden qubitre; 1Q hiba;
  - a transzpilált (routed) áramkör TÉNYLEGES kapuszámai páronként
    (K=32, optimization_level=3, seed_transpiler=1234, initial_layout
    S=125,R1=117,R2=124,R3=126, basis cz/rz/sx/x/delay/id).

Három feltétel (mindháromnak teljesülnie kell a ROGZUL-hoz):
  (a) flux-lock: J/2π (a szintetizált PHI=π/16 per t2q gateidő → Hz)
      meghaladja a ringqubitek szórását, a Ramsey-kötéssel
      δf_i ≤ 1/(π·T2_i*);
  (b) kapuhiba-költséglet: a teljes K=32 áramkörben a kétqubites
      hibákból származó várható hibaszám ≤ 0.5;
  (c) tárolási költséglet: a teljes idő (t ≈ K·(5 µs + 6·68 ns) ≈ 173 µs)
      alatt a ringqubitek T1-megtartása ≥ 0.5 (e^{-t/T1} ≥ 0.5).

Eredmény: data/wheel_w3_report.json + nyomtatott verdikt.
"""
from __future__ import annotations

import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from src.wheel.noise import load_snapshot
from src.wheel.circuits import K, PHI

T2Q_US = 0.068
T_HOLD_US = 5.0
N_2Q_PER_ROUND = 6


def compute():
    snap = load_snapshot()
    qb = snap["qubits"]
    T_CIRCUIT_US = K * (T_HOLD_US + N_2Q_PER_ROUND * T2Q_US)

    # --- (a) flux-lock
    J_Hz = (PHI / (2 * math.pi)) / (T2Q_US * 1e-6)
    scatter_Hz = {k: 1.0 / (math.pi * qb[k]["T2_us"] * 1e-6) for k in ("A1", "A2", "A3")}
    flux_lock_ok = J_Hz > max(scatter_Hz.values())
    flux_ratio = J_Hz / max(scatter_Hz.values())

    # --- (b) kapuhiba-költség (a noise modellel AZONOS számvitel:
    #          unitary/CZ kapunként EGY depolarizáló, e = él-hiba vagy eps_2q-összeg)
    # ideal (logikai XY-kapuk, K=32):
    e = {"A1A2": min(qb["A1"]["eps_2q"] + qb["A2"]["eps_2q"], 1),
         "A2A3": min(qb["A2"]["eps_2q"] + qb["A3"]["eps_2q"], 1),
         "A3A1": min(qb["A3"]["eps_2q"] + qb["A1"]["eps_2q"], 1),
         "SA1": snap["two_qubit_edges"][0]["error"],
         "SA2": snap["two_qubit_edges"][1]["error"],
         "SA3": snap["two_qubit_edges"][2]["error"]}
    # per kör: gyűrű-élek (mindegyik 1 unitary) + küllők
    ideal_per_round = K and (e["A1A2"] + e["A2A3"] + e["A3A1"]) + (e["SA1"] + e["SA2"] + e["SA3"])
    ideal_total = K * ideal_per_round
    # routed (TÉNYLEGES transzpilált számok, páronként, K=32):
    routed_pairs = {"117-125": 236, "124-125": 232, "125-126": 232}  # opt_level=0 (fagyasztott)
    pair_err = {"117-125": e["SA1"], "124-125": e["SA2"], "125-126": e["SA3"]}
    routed_total = sum(routed_pairs[p] * pair_err[p] for p in routed_pairs)
    ideal_native = 2.0 * ideal_total  # minden XY ≈ 2 natív CZ — a realisztikus ideal-számvitel
    native_note = ("ideal-XY: minden XY ≈ 2 natív CZ (ideal_native = 2×ideal); routed: a CZ-k közvetlenül számolva (nincs szorzás). KÜSZÖB: 0.5 várható 2Q-hiba / teljes áramkör")

    # --- (c) tárolási költséglet
    storage = {k: math.exp(-T_CIRCUIT_US / qb[k]["T1_us"]) for k in ("S", "A1", "A2", "A3")}
    storage_ok = min(storage.values()) >= 0.5

    budget_ok_ideal = ideal_total <= 0.5
    budget_ok_routed = routed_total <= 0.5
    # a döntő számvitel a ROUTED (a chipen ez futna); az ideal_native becslés is bukik — mindkettő kimondva
    verdict = "ROGZUL" if (flux_lock_ok and budget_ok_routed and storage_ok) else "SZETESO"

    report = {
        "kind": "W3 flux-locking kuszob — AER/SNAPSHOT-szamolas, NEM hardver-eredmeny",
        "k_steps": K,
        "t_circuit_us": T_CIRCUIT_US,
        "flux_lock": {
            "J_per_2pi_Hz": J_Hz,
            "ramsey_bound_Hz": scatter_Hz,
            "ratio": flux_ratio,
            "pass": bool(flux_lock_ok),
            "note": "a Ramsey-szórás KÖTÖTT érték (frequency_hz nincs a snapshotban) — a valódi szórás lehet kisebb",
        },
        "gate_error_budget": {
            "ideal_per_circuit_xy_accounting": ideal_total,
            "ideal_native_estimate": ideal_native,
            "routed_per_circuit_cz_accounting": routed_total,
            "routed_pairs": routed_pairs,
            "pass_ideal": bool(budget_ok_ideal),
            "pass_ideal_native": bool(ideal_native <= 0.5),
            "pass_routed": bool(budget_ok_routed),
            "note": native_note + "; a küszöb 0.5 várható 2Q-hiba / teljes áramkör",
        },
        "storage_floor": {q: storage[q] for q in storage},
        "pass_storage": bool(storage_ok),
        "verdict": verdict,
        "active_branch": ("W3 ROGZUL — a teljes QPU-job tervezhető" if verdict == "ROGZUL"
                          else "W3 SZETESO — a teljes QPU-job NEM tervezhető; csak a kis kuszöb-job (gyuru onmagaban, nehany lepes) johet szoba; a kerek-allitas a kovetkezo, erosebb csatolasu qubit-negyesre vagy javitott routingra var"),
    }
    return report


if __name__ == "__main__":
    rep = compute()
    out = os.path.join(os.path.dirname(__file__), "..", "..", "data", "wheel_w3_report.json")
    with open(out, "w") as f:
        json.dump(rep, f, indent=2, ensure_ascii=False)
    print(json.dumps(rep, indent=2, ensure_ascii=False))
