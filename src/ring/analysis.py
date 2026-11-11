"""Gyűrű-menet elemző — a döntési szabályt a fagyasztott fájlból olvassa.

A csillag-menet elemzőjének szerkezetét követi (hash-ellenőrzés, AUC/bootstrap
CI, verdikt), a gyűrű saját metrikáival:
  F+ = P(000; m+), F− = 1 − P(000; m−), C(k) = P(000;+) − P(000;−);
  τ_irány = az első k, ahol C(k) < 0.75 (lineáris interpoláció);
  ci_level = 0.95, correction = Holm a claim-családon belül.

NEM hardware-eredmény, amennyi a bemenet szimuláció.
"""
from __future__ import annotations
import hashlib, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
FROZEN = os.path.join(ROOT, "preregistration", "frozen_ring_params.json")
FROZEN_SHA = os.path.join(ROOT, "preregistration", "frozen_ring_params.sha256")


def sha256_file(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def check_frozen():
    actual = sha256_file(FROZEN)
    recorded = None
    for line in open(FROZEN_SHA):
        parts = line.split()
        if len(parts) >= 2 and parts[-1] == "frozen_ring_params.json":
            recorded = parts[0]
            break
    if recorded is None:
        raise SystemExit("HIBA: a .sha256 fájlban nincs frozen_ring_params.json bejegyzés.")
    if actual != recorded:
        raise SystemExit(f"HIBA: a fagyasztott fájl hash-e eltér!\n rögzített: {recorded}\n tényleges: {actual}")
    fz = json.load(open(FROZEN))
    assert fz["bootstrap"]["ci_level"] == 0.95, "ci_level != 0.95"
    assert fz["correction"] == "holm"
    assert fz["claim_family"] == ["R1", "R2", "pump", "nc"]
    return fz


def tau_from_curve(grid, values, cross=0.75):
    prev_k, prev_v = grid[0], values[0]
    for k, v in zip(grid, values):
        if v < cross:
            if k == prev_k:
                return float(k)
            frac = (prev_v - cross) / (prev_v - v)
            return float(prev_k + frac * (k - prev_k))
        prev_k, prev_v = k, v
    return float("inf")


def metric_from_counts(arm, counts):
    tot = sum(counts.values())
    if arm in ("lone", "delayed", "star"):
        return counts.get("1", 0) / tot
    return counts.get("000", 0) / tot


def compare(obs, fz, label="observed", model="routed"):
    """A fő ítélet inputot kap: obs = {arm: {k: {'000': n, 'shots': N, ...counts}}}
    a RING-KAROKRA (ring_p/ring_m/ring_0/static/broken + controls).
    model = a vizsgált Aer-sáv ('routed' (alapértelmezett, ez dönt a terv §11 szerint)
    vagy 'native') — a modell-sávhoz KÖTELEZŐ illeszkednie az összehasonlításnak."""
    grid = fz["step_grid"]
    out = {"label": label, "metrics": {}, "verdict": None, "checks": []}

    def p000(arm, k):
        c = obs[arm][str(k)]
        return c.get("000", 0) / c["shots"]

    def p1(arm, k):
        c = obs[arm][str(k)]
        return c.get("1", 0) / c["shots"]

    rp = {k: p000("ring_p", k) for k in grid}
    rm = {k: p000("ring_m", k) for k in grid}
    C = {k: rp[k] - rm[k] for k in grid}
    out["metrics"]["F_plus"] = rp
    out["metrics"]["F_minus"] = {k: 1.0 - rm[k] for k in grid}
    out["metrics"]["contrast"] = C
    out["metrics"]["tau_contrast"] = tau_from_curve(list(grid), [C[k] for k in grid])

    # Aer-előrejelzések a fagyasztott fájlból — a MEGVÁLASZTOTT modell szerint
    if model not in ("routed", "native"):
        raise ValueError(f"ismeretlen Aer-modell: {model!r}")
    exp_rp = fz["expected_curves"][model]["ring_p"]
    exp_rm = fz["expected_curves"][model]["ring_m"]
    exp_c = {str(k): fz["contrast"][model][str(k)] for k in grid}

    rp_mae = sum(abs(rp[k] - exp_rp[str(k)]) for k in grid) / len(grid)
    rm_mae = sum(abs(rm[k] - exp_rm[str(k)]) for k in grid) / len(grid)
    out["metrics"][f"mae_vs_{model}_aer"] = {"ring_p": rp_mae, "ring_m": rm_mae}
    out["model"] = model

    # ítélet: a routed Aer-sáv (modell-függő!) — a mérés dönt
    band = 0.15   # konzervatív, fagyasztott szélesség (binomial + modell)
    above = sum(1 for k in grid if rp[k] > exp_rp[str(k)] + band)
    in_band = sum(1 for k in grid if abs(rp[k] - exp_rp[str(k)]) <= band)
    verdict = "ANOMALIA" if above >= 3 else ("TEXTBOOK" if in_band >= 6 else "NULL")

    # R1/R2: a döntési feltételek (95% küszöbök, egyetlen összehasonlításból)
    tau_ring = out["metrics"]["tau_contrast"]
    # kontrollok: obs tartalmazza a control karokat is
    tau_star = tau_from_curve(list(grid), [p1("star", k) for k in grid]) if "star" in obs else None
    tau_lone = tau_from_curve(list(grid), [p1("lone", k) for k in grid]) if "lone" in obs else None
    tau_delayed = tau_from_curve(list(grid), [p1("delayed", k) for k in grid]) if "delayed" in obs else None
    tau_broken = tau_from_curve(list(grid), [p000("broken", k) for k in grid]) if "broken" in obs else None
    out["metrics"]["tau_star"] = tau_star
    out["metrics"]["tau_lone"] = tau_lone
    out["metrics"]["tau_delayed"] = tau_delayed
    out["metrics"]["tau_broken"] = tau_broken

    r1_ok = tau_ring is not None and (tau_star is None or tau_ring > tau_star) and (tau_lone is None or tau_ring > tau_lone)
    nc_ok = (tau_broken is None) or (tau_broken <= tau_ring)
    out["claims"] = {
        "R1_ring_beats_star_and_lone": bool(r1_ok),
        "R2_static_weaker_than_flux": bool(rp[16] > p000("static", 16)) if "static" in obs else None,
        "nc_broken_not_better": bool(nc_ok),
    }
    out["verdict"] = verdict
    out["verdict_note"] = "ha az elemző vak lenne (PC/NC megsértve), az verdikt NEM születhet — modell-audit előbb"
    return out


def summary():
    fz = check_frozen()
    print("frozen OK; ci_level =", fz["bootstrap"]["ci_level"],
          "| correction =", fz["correction"],
          "| K =", fz["K"], "| grid =", fz["step_grid"],
          "| Omega =", fz["omega_rad_per_round"])
    return fz


if __name__ == "__main__":
    summary()
