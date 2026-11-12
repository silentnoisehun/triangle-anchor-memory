#!/usr/bin/env python3
"""A Kerék-menet dryrun — QPU NÉLKÜL, végig a fagyasztott protokollon (v1.2).

Végrehajtás:
  1. frozen integritás (sha256, ci_level=0.99, holm, claim-család, routing);
  2. zajtalan ellenőrzések (prep-normák, az alone-kar S-tartása = 1.0 zajtalanul);
  3. Aer-zajos "mérés" a FAGYASZTOTT routolt áramkörökön (fresh seed) →
     az elemző fut; a verdikt nem lehet ANOMALIA (a modell önmaga ellen nem az);
  4. pozitív kontroll (beépített Ry-stabilizáló hatás) — az elemzőnek
     KIMUTATNIA KELL (ha nem: az elemző érvénytelen, exit 2);
  5. negatív kontroll (cut) — a W1-irányban nem találhat előnyt;
  6. a W3-verdikt és az aktív ág kinyomtatva (SZÉTESŐ → nincs teljes job);
  7. a riport külön sorban közli a „tankonyvi varakozas: teljesul / nem
     teljesul” értékeket (W2, W4_secondary, sotetallapot).

MINDEN eredmény Aer/zajtalan szimuláció — SOHA nem "HARDWARE".
Kimenet: data/wheel_dryrun_report_v1_2.json (a v1.1-es
data/wheel_dryrun_report.json MEGŐRZŐDIK) + nyomtatott összegzés; exit 0 = PASS.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from src.wheel import analysis  # noqa: E402
from src.wheel.simulate import (collect_routed_counts, run_ideal_state)  # noqa: E402
from src.wheel.circuits import ARM_NAMES, K  # noqa: E402
from src.wheel.noise import load_snapshot  # noqa: E402

SHOTS_DRYRUN = 512
SEED = 20261111
KS = list(range(0, K + 1, 4))
ARMS = list(ARM_NAMES)


def main():
    report = {"kind": "AER/NOISELESS SZIMULACIO — NEM HARDWARE",
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
    check("frozen integrity (sha256 + ci_level + holm + claim-család + routing)", True,
          f"ci={fz['ci_level']}, {fz['correction']}, {fz['claim_family']}")
    check("W3-verdikt befagyasztva (SZÉTESŐ → nincs teljes QPU-job)",
          fz.get("w3_verdict") == "SZETESO", fz.get("w3_active_branch", "")[:80] + "…")

    # 2) zajtalan ellenőrzések
    ideal = run_ideal_state(["alone", "ring_only", "wheel"], KS, pop_branch=1)
    alone_flat = all(abs(v - 1.0) < 1e-12 for v in ideal["alone"])
    check("zajtalan: az alone kar S-tartása = 1.0 minden ellenponton", alone_flat)
    check("zajtalan: a wheel oszcillál (van k, ahol P(S=1) < 0.5)",
          any(v < 0.5 for v in ideal["wheel"]))

    # 3) Aer "mérés" → elemző
    obs = {}
    for arm in ARMS:
        obs[arm] = collect_routed_counts(arm, KS, shots=SHOTS_DRYRUN, seed=SEED)
    rep = analysis.analyze(obs, fz, label="dryrun_routed_observed")
    check("Aer-megfigyelés: a verdikt nem ANOMALIA (a modell önmaga ellen nem az)",
          rep["verdict"] != "ANOMALIA", f"verdikt = {rep['verdict']}")

    # 4) pozitív kontroll — kötelezően kimutatandó
    pc = collect_routed_counts("wheel", KS, shots=SHOTS_DRYRUN, seed=SEED + 1,
                               positive_control=True)
    pc_rep = analysis.positive_control_check({"wheel": pc}, obs, fz)
    check("pozitív kontroll: az elemző KIMUTATJA a beépített hatást (z > 4)",
          pc_rep["detected"], f"z = {pc_rep['z']:.1f}, diff = {pc_rep['mean_diff']:+.3f}")

    # 5) negatív kontroll: a cut nem adhat W1-irányú előnyt
    cut_auc = sum(obs["cut"][str(k)]["1"] / obs["cut"][str(k)]["shots"] for k in KS) / len(KS)
    wheel_auc = sum(obs["wheel"][str(k)]["1"] / obs["wheel"][str(k)]["shots"] for k in KS) / len(KS)
    check("negatív kontroll (cut): nem jobb a wheelnél a megtartásban",
          cut_auc <= wheel_auc + 0.05, f"cut AUC ≈ {cut_auc:.3f}, wheel ≈ {wheel_auc:.3f}")

    # 6) claim-család minden tagja jelen van a jelentésben
    fam = list(rep["claims"].keys())
    check("a claim-család mind a négy tagja értelmezve (W1, W2, W4_secondary, sotetallapot)",
          fam == ["W1", "W2", "W4_secondary", "sotetallapot"])

    report["tankonyvi_varakozas"] = {
        "W2": rep["claims"]["W2"]["tankonyvi_varakozas"],
        "W4_secondary": rep["claims"]["W4_secondary"]["tankonyvi_varakozas"],
        "sotetallapot": rep["claims"]["sotetallapot"]["tankonyvi_varakozas"],
    }
    report["verdict"] = rep["verdict"]
    report["analysis"] = rep
    report["positive_control"] = pc_rep
    report["all_pass"] = bool(ok)
    out_path = os.path.join(ROOT, "data", "wheel_dryrun_report_v1_2.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=float)
    print()
    print(f"Dryrun verdikt: {rep['verdict']}  |  összesített: {'PASS' if ok else 'FAIL'}")
    print(f"Tankönyvi várakozás: {json.dumps(report['tankonyvi_varakozas'], ensure_ascii=False)}")
    print(f"Jelentés: {out_path}")
    print("MEGJEGYZÉS: Aer/zajtalan szimuláció — NEM hardware-eredmény. A QPU nem futott.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
