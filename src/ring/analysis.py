"""Gyűrű-menet elemző — a döntési szabályt a FAGYASZTOTT fájlból olvassa.

v1.1 (AMENDED, 2026-11-12; felülírja a v1.0-t — a v1.0 byte-ra változatlan):

FAGYASZTOTT ELLENŐRZÉSEK (fail-closed):
  - preregistration/frozen_ring_params_v1.1.json létezik; a .sha256 egyezik;
  - version == "1.1"; bootstrap.ci_level == 0.99; correction == "holm";
  - claim_family == ["R1", "R2", "pump", "nc"] (név szerint).

Claim-család p-értékei (bootstrap, multinomiális, 2000 minta, seed a frozen
fájlban; egyoldalú; Holm α = 0.01 a családban; "kicsi p ⇒ a claim áll"):
  R1: max(p_star, p_lone) — P_boot(AUC(ret_gyűrű) ≤ AUC(ret_kontroll));
      Bonferroni a claim-en belül (a Kerék W1-mintájára). A részp-értékek a
      details-ben; a család csak R1-et tart.
  R2: AUC(C(k)) bootstrap; p = P_boot(AUC(C) ≤ 0) — a fluxus-mentes referencia
      strukturálisan C ≡ 0 (a Peierls-fázis eltűnik) ⇒ ez a "nem kering" H0.
  PUMP: p = min over a FAGYASZTOTT nem-nulla pump-párok közül
      P_boot(AUC_pump ≤ AUC_ring_p) — best-case a pumpának (parameter-halászat
      tilos); ha még a legjobb pár sem szignifikáns, a pumpa-ötlet megbukott.
  NC: p = P_boot(AUC(ret_ring) ≤ AUC(ret_törött)) — "az elemző megkülönbözteti
      a töröttet" claim; kicsi p ⇒ helyes NC-viselkedés (a törött NEM ad
      irány-előnyt). HA nc NEM szignifikáns Holm után → az elemző vak
      (a törött és a gyűrű megkülönböztethetetlen) → out["nc_violation"] = True.

Ítélet (verdikt):
  ANOMALIA: obs_AUC > aer_AUC + z·√(aer_AUC-var + obs_AUC-var),
            z = Φ⁻¹(0.995) = 2.5758 (kétoldali 99%) — először modell-audit!
  TEXTBOOK: |d_AUC| ≤ sáv;
  NULL:     egyébként; ALSO: ha egyetlen family-claim sem szignifikáns, akkor
            NULL (nincs mérhető előny) — a definíció szerint.

NEM hardware-eredmény, amennyiben a bemenet szimuláció.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
FROZEN = os.path.join(ROOT, "preregistration", "frozen_ring_params_v1.1.json")
FROZEN_SHA = os.path.join(ROOT, "preregistration", "frozen_ring_params_v1.1.sha256")
Z_995 = 2.5758293035489004  # Φ^{-1}(0.995)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def check_frozen():
    if not (os.path.exists(FROZEN) and os.path.exists(FROZEN_SHA)):
        raise SystemExit("HIBA: frozen_ring_params_v1.1.json / .sha256 hiányzik — az elemző nem futhat.")
    actual = sha256_file(FROZEN)
    recorded = None
    for line in open(FROZEN_SHA):
        parts = line.split()
        if len(parts) >= 2 and parts[-1] == "frozen_ring_params_v1.1.json":
            recorded = parts[0]
            break
    if recorded is None:
        raise SystemExit("HIBA: a .sha256 fájlban nincs frozen_ring_params_v1.1.json bejegyzés.")
    if actual != recorded:
        raise SystemExit(f"HIBA: a fagyasztott fájl hash-e eltér!\n rögzített: {recorded}\n tényleges: {actual}")
    with open(FROZEN) as f:
        fz = json.load(f)
    if fz.get("version") != "1.1":
        raise SystemExit("HIBA: version != '1.1' — a v1.0 (95% CI) érvénytelen a v1.1 óta.")
    if fz.get("bootstrap", {}).get("ci_level") != 0.99:
        raise SystemExit("HIBA: ci_level != 0.99 — a fagyasztott fájl nem egyezik.")
    if fz.get("correction") != "holm":
        raise SystemExit("HIBA: correction != 'holm' — a fagyasztott fájl nem egyezik.")
    if list(fz.get("claim_family", [])) != ["R1", "R2", "pump", "nc"]:
        raise SystemExit("HIBA: claim_family nem [R1, R2, pump, nc].")
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


def holm_adjust(pvals, alpha=0.01):
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    out = {}
    still = True
    for i, (name, p) in enumerate(items):
        thr = alpha / (m - i)
        ok = (p <= thr) and still
        if not ok:
            still = False
        out[name] = {"p_raw": float(p), "holm_threshold": thr, "significant": bool(ok)}
    return out


def _retention(arm, counts):
    tot = sum(counts.values())
    if arm == "ring_m":
        return 1.0 - counts.get("000", 0) / tot
    return metric_from_counts(arm, counts)


def _contrast_at(rp, rm):
    return rp - rm


def bootstrap_family(obs, k_list, n_boot, seed):
    """Az összes szükséges bootstrap-eloszlás egy menetben (multinomiális)."""
    rng = np.random.default_rng(seed)

    def draw_curve(arm):
        n = [obs[arm][str(k)]["shots"] for k in k_list]
        p = [metric_from_counts(arm, obs[arm][str(k)]) for k in k_list]
        vals = []
        for _ in range(n_boot):
            pts = [rng.binomial(n[i], p[i]) / n[i] for i in range(len(k_list))]
            vals.append(pts)
        return np.array(vals)  # (n_boot, len(k_list)) nyers ügyesség

    # ret-görbék karéágonként
    curves = {}
    for arm in ("ring_p", "ring_m", "static", "broken", "star", "lone", "delayed"):
        if arm in obs:
            curves[arm] = draw_curve(arm)
    auc = {a: curves[a].mean(axis=1) for a in curves}
    # a ring_m F⁻ görbéje a bootstrapben is 1 − P000
    if "ring_m" in curves:
        # F⁻(k) = 1 − P(000; m−) — a retenció a m− irányban komplementer
        auc["ring_m"] = (1.0 - curves["ring_m"]).mean(axis=1)
    # irány-kontraszt görbéje (csak ring_p/ring_m létezik rá)
    if "ring_p" in curves and "ring_m" in curves:
        C = curves["ring_p"] - curves["ring_m"]
        aucC = C.mean(axis=1)
    else:
        aucC = None
    return {"auc": auc, "aucC": aucC, "curves": curves}


def compare(obs, fz, label="observed", model="routed"):
    """A fő ítélet. obs = {arm: {k: {'000': n|'1': n, 'shots': N}}}.
    model = 'routed' (alapértelmezett, ez dönt a terv §11 szerint) vagy 'native'."""
    grid = fz["step_grid"]
    n_boot = fz["bootstrap"]["resamples"]
    seed = fz["bootstrap"]["seed"]
    out = {"label": label, "model": model, "metrics": {}, "verdict": None,
           "checks": [], "claims": {}, "nc_violation": False}

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
    out["metrics"]["tau_ring_p"] = tau_from_curve(list(grid), [rp[k] for k in grid])
    for arm in ("static", "broken", "star", "lone", "delayed"):
        if arm in obs:
            if arm in ("star", "lone", "delayed"):
                out["metrics"][f"tau_{arm}"] = tau_from_curve(list(grid), [p1(arm, k) for k in grid])
            else:
                out["metrics"][f"tau_{arm}"] = tau_from_curve(list(grid), [p000(arm, k) for k in grid])

    if model not in ("routed", "native"):
        raise ValueError(f"ismeretlen Aer-modell: {model!r}")
    exp_rp = fz["expected_curves"][model]["ring_p"]
    exp_rm = fz["expected_curves"][model]["ring_m"]
    out["metrics"][f"mae_vs_{model}_aer"] = {
        "ring_p": sum(abs(rp[k] - exp_rp[str(k)]) for k in grid) / len(grid),
        "ring_m": sum(abs(rm[k] - exp_rm[str(k)]) for k in grid) / len(grid)}

    # --- v1.1 ANOMALIA-kapu: determinisztikus binomiális-sávos, 99% ---
    aer_shots = fz.get("shots_noisy_sim", fz["shots_phase0"])
    aer_vals = [exp_rp[str(k)] for k in grid]
    m = len(grid)
    aer_auc = sum(aer_vals) / m
    aer_var_auc = sum(p * (1.0 - p) / aer_shots for p in aer_vals) / (m * m)
    obs_vals = [rp[k] for k in grid]
    shots = obs["ring_p"][str(grid[0])]["shots"]
    obs_auc = sum(obs_vals) / m
    var_obs_auc = sum(p * (1.0 - p) / shots for p in obs_vals) / (m * m)
    band = Z_995 * (aer_var_auc + var_obs_auc) ** 0.5
    d_auc = obs_auc - aer_auc
    if d_auc > band:
        verdict = "ANOMALIA"
    elif abs(d_auc) <= band:
        verdict = "TEXTBOOK"
    else:
        verdict = "NULL"
    out["metrics"].update({"aer_auc": aer_auc, "aer_var_auc": aer_var_auc,
                           "obs_auc": obs_auc, "anomaly_band": band,
                           "d_auc": d_auc, "z_995": Z_995})

    # --- claim-család: bootstrap + Holm (α = 0.01) ---
    boot = bootstrap_family(obs, grid, n_boot, seed)
    auc = boot["auc"]
    details = {}
    fam = {}
    if "ring_p" in auc:
        r1_parts = []
        if "star" in auc:
            details["R1_star"] = float((auc["ring_p"] <= auc["star"]).mean())
            r1_parts.append(details["R1_star"])
        if "lone" in auc:
            details["R1_lone"] = float((auc["ring_p"] <= auc["lone"]).mean())
            r1_parts.append(details["R1_lone"])
        fam["R1"] = max(r1_parts) if r1_parts else None
    if boot["aucC"] is not None:
        fam["R2"] = float((boot["aucC"] <= 0.0).mean())
    # pump: best-case az összes fagyasztott nem-nulla páron
    pump_pairs = [k for k in fz.get("pump", {}).get("pair_results_routed", {})
                  if not k.startswith("m0.0_")]
    pump_p = None
    for pair in pump_pairs:
        arm = f"pump:{pair}"
        if arm in obs:
            p_arm = [metric_from_counts("pump", obs[arm][str(k)]) for k in grid]
            rng = np.random.default_rng(seed + 1)
            n = [obs[arm][str(k)]["shots"] for k in grid]
            draws = np.mean(np.array([[rng.binomial(n[i], p_arm[i]) / n[i] for i in range(m)]
                                      for _ in range(n_boot)]), axis=1)
            pr = float((draws <= auc["ring_p"]).mean()) if "ring_p" in auc else None
            pump_p = pr if pump_p is None or (pr is not None and pr < pump_p) else pump_p
    if pump_p is not None:
        fam["pump"] = pump_p
    if "broken" in auc and "ring_p" in auc:
        # "az elemző megkülönbözteti a töröttet" — kicsi p ⇒ jó NC-viselkedés
        fam["nc"] = float((auc["ring_p"] <= auc["broken"]).mean())
    fam["_details"] = details

    details = fam.pop("_details", {})
    present = {k: v for k, v in fam.items() if v is not None}
    holm = holm_adjust(present, alpha=0.01) if present else {}
    out["claims"] = {"family": holm, "details": details}
    nc_sig = holm.get("nc", {}).get("significant", None)
    out["nc_violation"] = (nc_sig is False) if nc_sig is not None else None
    out["any_claim_significant"] = any(v["significant"] for v in holm.values()) if holm else False
    out["verdict"] = verdict
    out["verdict_note"] = ("v1.1: ANOMALIA csak 99% CI + a binomiális-sávos kapu után; "
                           "ha az NC szignifikáns, az elemző vak — a verdikt érvénytelen "
                           "(modell-audit előbb)")
    return out


def summary():
    fz = check_frozen()
    print("frozen OK (v1.1); ci_level =", fz["bootstrap"]["ci_level"],
          "| correction =", fz["correction"],
          "| K =", fz["K"], "| grid =", fz["step_grid"],
          "| Omega =", fz["omega_rad_per_round"])
    return fz


if __name__ == "__main__":
    summary()
