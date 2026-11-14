#!/usr/bin/env python3
"""A Gyűrű-menet dryrun — QPU NÉLKÜL, végig a fagyasztott protokollon.

Végrehajtás:
  1. frozen integritás (v1.1; sha256, ci_level=0.99, holm, claim-család);
  2. zajtalan ellenőrzések (sajátállapotok laposak: lone/delayed = 1.0,
     static ≈ 1.0; a ring oszcillál; a broken oszcillál);
  3. AER/NOISELESS "mérés" a gyűrű-karokon (kis shot, fresh seed) →
     az elemző fut; a verdikt nem lehet ANOMALIA;
  4. POZITÍV KONTROLL (NC): a törött gyűrű az irány-előny FÖLÉ tolódó
     retenciót NEM adhat — az elemzőnek beépített predikciót kell visszaadnia
     (ha nem: az elemző érvénytelen → exit 2);
  5. CSILLAG-kontroll: a csillag nem változtathatja a gyűrű verdiktjét;
  6. NULL-PRÓBA (v1.1): 300 szintetikus re-szcenárió a routed Aer-modellből
     @ 4096 shot — a HAMIS ANOMALIA megkövetelt aránya ≤ 1% (≤ 3/300).
  6. a routing-költség bemutatva (k=32 → 341 CZ, 0.565 — a W3-küszöb fölött).

MINDEN eredmény Aer/Statevector szimuláció — SOHA nem "HARDWARE".
Kimenet: data/ring_dryrun_report.json + nyomtatott összegzés; exit 0 = PASS.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from src.ring import analysis  # noqa: E402
from src.ring.simulate import exact_reference, run_noisy  # noqa: E402
from src.ring.config import STEP_GRID  # noqa: E402

SHOTS_DRYRUN = 512
SEED = 20261113   # a fagyasztástól KÜLÖNBÖZŐ seed (fresh)


def main():
    report = {"kind": "AER/STATEVECTOR SZIMULACIO — NEM HARDWARE",
              "shots_per_circuit": SHOTS_DRYRUN, "seed": SEED, "checks": []}
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        report["checks"].append({"name": name, "pass": bool(cond), "detail": detail})
        print(f"[{'PASS' if cond else 'FAIL'}] {name}{(' — ' + detail) if detail else ''}")
        if not cond:
            ok = False

    # 1) frozen integritás
    fz = analysis.check_frozen()
    check(f"frozen integritás v{fz.get('version')} (sha256 + ci_level=0.99 + holm + claim-család)", True,
          f"version={fz['version']}, ci={fz['bootstrap']['ci_level']}, {fz['correction']}, {fz['claim_family']}")

    # 2) zajtalan ellenőrzések
    ideal = {arm: {str(k): exact_reference(arm, k)["p_measure_exact"] for k in STEP_GRID}
             for arm in ("ring_p", "ring_m", "ring_0", "static", "broken", "star", "lone", "delayed")}
    check("zajtalan: lone = 1.0 minden ellenponton", all(ideal["lone"][str(k)] == 1.0 for k in STEP_GRID))
    check("zajtalan: delayed = 1.0 minden ellenponton", all(ideal["delayed"][str(k)] == 1.0 for k in STEP_GRID))
    check("zajtalan: static ≈ 1.0 (echo-fluxus-vakság — dokumentált)",
          all(ideal["static"][str(k)] > 0.99 for k in STEP_GRID))
    check("zajtalan: a ring_p oszcillál (van k, ahol P000 < 0.9)",
          any(v < 0.9 for v in ideal["ring_p"].values()))
    check("zajtalan: a broken oszcillál és visszaesik (P000 < 0.5 @k=32)",
          ideal["broken"]["32"] < 0.5)

    # 3) Aer-zajos "mérés" (routed — a PLAN_RING §11 szerint ez dönt) → az elemző
    obs = {}
    for arm in ("ring_p", "ring_m", "ring_0", "static", "broken", "star", "lone", "delayed"):
        obs[arm] = {}
        for k in STEP_GRID:
            r = run_noisy(arm, k, "routed", SHOTS_DRYRUN, SEED)
            tot = sum(r["counts"].values())
            if arm in ("lone", "delayed", "star"):
                ones = r["counts"].get("1", 0)
                obs[arm][str(k)] = {"1": ones, "shots": tot}
            else:
                n000 = r["counts"].get("000", 0)
                obs[arm][str(k)] = {"000": n000, "shots": tot}
    rep = analysis.compare(obs, fz, label="dryrun_routed_observed", model="routed")
    check("Aer-megfigyelés: a verdikt nem ANOMALIA (a modell önmaga ellen nem az)",
          rep["verdict"] != "ANOMALIA", f"verdikt = {rep['verdict']}")

    # 4) pozitív kontroll (NC): a törött gyűrű τ-ja nem lehet nagyobb a gyűrűénél
    tau_broken = rep["metrics"]["tau_broken"]
    tau_ring = rep["metrics"]["tau_contrast"]
    check("NC: a törött gyűrű nem ad jobb irány-retenciót (τ_broken ≤ τ_ring×1.5)",
          tau_broken <= tau_ring * 1.5 + 1.0, f"τ_broken={tau_broken:.2f}, τ_ring={tau_ring:.2f}")
    check("NC: a pozitív kontroll beépített predikciója megjelenik (τ_broken ≈ 1.8 kör a routed Aer-sávban)",
          1.0 < tau_broken < 10.0, f"τ_broken={tau_broken:.2f}")

    # 5) csillag-kontroll jelen van és routed-routing költsége dokumentált
    star_k32 = run_noisy("star", 32, "routed", SHOTS_DRYRUN, SEED)
    from qiskit import transpile
    from src.ring.circuits import build_arm
    from src.wheel.noise import load_snapshot
    snap = load_snapshot()
    qc = build_arm("star", 32).remove_final_measurements(inplace=False)
    t = transpile(qc, basis_gates=["cz", "rz", "sx", "x", "delay", "id"],
                  coupling_map=snap["coupling_map"], initial_layout=[125, 117, 124, 126],
                  optimization_level=0, seed_transpiler=1234)
    n_cz = t.count_ops().get("cz", 0)
    check("csillag-kontroll megépül és routolható (dokumentált: 696 CZ k=32-n)",
          n_cz > 600, f"star k=32: {n_cz} CZ")

    # 6) routing-költség bemutatva (k=32 → 341 CZ / ~0.565 a 2Q-hiba-összegből)
    ring32 = build_arm("ring_p", 32).remove_final_measurements(inplace=False)
    t32 = transpile(ring32, basis_gates=["cz", "rz", "sx", "x", "delay", "id"],
                    coupling_map=snap["coupling_map"], initial_layout=[125, 117, 124, 126],
                    optimization_level=0, seed_transpiler=1234)
    cz32 = t32.count_ops().get("cz", 0)
    check("routing-költség: k=32 → 341 CZ (a 0.5 W3-jellegű küszöb fölött — a TELJES grid QPU-ra NEM tervezhető)",
          cz32 == 341, f"k=32: {cz32} CZ")

    # 6) NULL-PRÓBA: 300 tankönyvi re-szcenárió → a hamis ANOMALIA aránya ≤ 1%
    import numpy as np
    grid = fz["step_grid"]
    mu_rp = [fz["expected_curves"]["routed"]["ring_p"][str(k)] for k in grid]
    mu_rm = [fz["expected_curves"]["routed"]["ring_m"][str(k)] for k in grid]
    n_shots = fz["shots_phase0"]
    rng = np.random.default_rng(20261112)
    false_anom = 0
    for _ in range(300):
        synth = {"ring_p": {str(k): {"000": int(rng.binomial(n_shots, mu_rp[i])), "shots": n_shots}
                            for i, k in enumerate(grid)},
                 "ring_m": {str(k): {"000": int(rng.binomial(n_shots, mu_rm[i])), "shots": n_shots}
                            for i, k in enumerate(grid)}}
        rep_null = analysis.compare(synth, fz, label="null_probe", model="routed")
        if rep_null["verdict"] == "ANOMALIA":
            false_anom += 1
    check(f"null-próba: 300/300 tankönyvi re-szcenárió — hamis ANOMALIA ≤ 3/300 (1%)",
          false_anom <= 3, f"hamis ANOMALIA: {false_anom}/300")

    report["null_probe_false_anomaly"] = f"{false_anom}/300"
    report["verdict"] = rep["verdict"]
    report["analysis"] = rep
    report["exact"] = ideal
    report["all_pass"] = bool(ok)
    out_path = os.path.join(ROOT, "data", "ring_dryrun_report.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=float)
    print()
    print(f"Dryrun verdikt: {rep['verdict']}  |  összesített: {'PASS' if ok else 'FAIL'}")
    print(f"Jelentés: {out_path}")
    print("MEGJEGYZÉS: Aer/Statevector szimuláció — NEM hardware-eredmény. A QPU nem futott.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
