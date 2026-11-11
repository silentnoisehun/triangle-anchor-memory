"""Kerék-menet — fagyasztott elemző (a terven változtatni CSAK verziózott
„amended" kiegészítéssel szabad).

KÖTELEZŐ ELLENŐRZÉSEK FUTTATÁS KÖZBEN:
  - preregistration/frozen_wheel_params.json létezik és a .sha256 fájl
    hash-e egyezik;
  - ci_level == 0.99; correction == "holm";
  - claim_family == ["W1", "W2", "W4_secondary", "sotetallapot"] (név szerint);
  - routed variant = "transpiled" (a fagyasztott választás).

Ha bármelyik ellenőrzés buktat, az elemző MEGTAGADJA a futtatást.

Metrikák (fagyasztva):
  R(arm,k) = n1/shots (S |1>-gyel indult);  AUC(arm) = R ellenpontokon átlagolt.
  W1: c1 = AUC(wheel) − 1.25·AUC(static); c2 = AUC(wheel) − 1.25·AUC(ring_only);
      W1-elfogadás: MINDKÉT kontraszt egyoldalú 99%-CI > 0 (Holm után);
      W1 p = max(p_c1, p_c2)  (Bonferroni a W1-en belül — dokumentálva).
  W2: d = AUC(wheel) − AUC(wheel_rev); két oldalú, Holm.
  W4_secondary: d = AUC(pump_dir) − AUC(wheel); egyoldalú, Holm — a W1/W2-be
      NEM számít bele; ha nem választ el, a pumpa megbukott ezen a rendszeren.
  sotetallapot: d1 = AUC(dark_m1) − AUC(dark_m0); d2 = AUC(dark_mm1) − AUC(dark_m0);
      sotetallapot p = max(p1,p2); Holm. A saját cáfolati feltétele: ha egyik
      chirális ág sem válik el 99% CI-vel + Holm után, a "forgás tartja S-t"
      hipotézis ezen a berendezésen cáfolva.

Ítéletek a fő kontrasztra (wheel vs static AUC-újra):
  TEXTBOOK: a mért kontraszt a fagyasztott Aer-sávban van (nem anomália; az
            "effektus" Aer-magyarázott lenne. itt: nincs mérhető előny, de az
            Aer-jóslattal összhangban — tankönyv);
  ANOMALIA: a mért AUC(wheel) az Aer-jóslat 99%-CI FELSŐ határát meghaladja
            (először kalibrációs/modellhibát kell keresni, csak utána bármit!);
  NULL: nincs mérhető előny a kontrollokkal szemben (W1 nem teljesül).

Bootstrap: 2000 újraminta, multinomiális (a shot-okból), seed = frozen
"bootstrap_seed". Az eredmény data/wheel_analysis_report.json-be kerül.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
FROZEN = os.path.join(ROOT, "preregistration", "frozen_wheel_params.json")
FROZEN_SHA = os.path.join(ROOT, "preregistration", "frozen_wheel_params.sha256")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def check_frozen():
    if not (os.path.exists(FROZEN) and os.path.exists(FROZEN_SHA)):
        raise SystemExit("HIBA: frozen_wheel_params.json / .sha256 hiányzik — az elemző nem futhat.")
    actual = sha256_file(FROZEN)
    recorded = None
    for line in open(FROZEN_SHA):
        parts = line.split()
        if len(parts) >= 2 and parts[-1] == "frozen_wheel_params.json":
            recorded = parts[0]
            break
    if recorded is None:
        raise SystemExit("HIBA: a .sha256 fajlban nincs frozen_wheel_params.json bejegyzés.")
    if actual != recorded:
        raise SystemExit(f"HIBA: frozen_wheel_params.json hash eltér ({actual} != {recorded}) — az elemző nem futhat.")
    with open(FROZEN) as f:
        fz = json.load(f)
    if fz.get("ci_level") != 0.99:
        raise SystemExit("HIBA: ci_level != 0.99 — a fagyasztott fajl nem egyezik.")
    if fz.get("correction") != "holm":
        raise SystemExit("HIBA: correction != 'holm' — a fagyasztott fajl nem egyezik.")
    if list(fz.get("claim_family", [])) != ["W1", "W2", "W4_secondary", "sotetallapot"]:
        raise SystemExit("HIBA: claim_family nem [W1, W2, W4_secondary, sotetallapot].")
    if fz.get("routing_choice") != "routed_transpiled":
        raise SystemExit("HIBA: routing_choice != 'routed_transpiled'.")
    return fz


def auc_of(counts: dict, k_list) -> float:
    vals = []
    for k in k_list:
        c = counts[str(k)] if str(k) in counts else counts[k]
        vals.append(c["1"] / c["shots"])
    return float(np.mean(vals))


def bootstrap_aucs(counts, k_list, n_boot: int, seed: int):
    rng = np.random.default_rng(seed)
    arms = counts["_arms"]
    data = {(a, k): counts[a][str(k) if str(k) in counts[a] else k] for a in arms for k in k_list}
    aucs = {a: [] for a in arms}
    for _ in range(n_boot):
        for a in arms:
            vals = []
            for k in k_list:
                c = data[(a, k)]
                n = c["shots"]
                p = c["1"] / n
                draw = rng.binomial(n, p)
                vals.append(draw / n)
            aucs[a].append(float(np.mean(vals)))
    return {a: np.array(v) for a, v in aucs.items()}


def holm_adjust(pvals: dict, alpha: float = 0.01):
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    out = {}
    still_running = True
    for i, (name, p) in enumerate(items):
        thresh = alpha / (m - i)
        passed = (p <= thresh) and still_running
        if not passed:
            still_running = False
        out[name] = {"p_raw": p, "holm_threshold": thresh, "significant": bool(passed)}
    return out


def one_sided_p(boot_diff: np.ndarray) -> float:
    # egyoldalú: a különbség <= 0 aránya (bootstrap-p)
    return float((boot_diff <= 0.0).mean())


def two_sided_p(boot_diff: np.ndarray) -> float:
    return float(2.0 * min((boot_diff <= 0.0).mean(), (boot_diff >= 0.0).mean()))


def analyze(counts: dict, fz: dict, label: str = "observed"):
    k_list = fz["checkpoints"]
    n_boot = fz.get("bootstrap_n", 2000)
    seed = fz.get("bootstrap_seed", 20261111)
    arms = ["wheel", "wheel_rev", "static", "ring_only", "alone", "alone_DD",
            "pump_blind", "pump_dir", "pump_wrong", "cut",
            "dark_m1", "dark_m0", "dark_mm1"]
    flat = {"_arms": arms}
    for a in arms:
        flat[a] = counts[a]
    boot = bootstrap_aucs(flat, k_list, n_boot, seed)
    auc = {a: float(np.mean(boot[a])) for a in arms}

    def diff(a, b, scale=1.0):
        return boot[a] - scale * boot[b]

    res = {"label": label, "aucs": auc}
    # W1: mindkét feltétel (Bonferroni a claim-en belül)
    p_w1_1 = one_sided_p(diff("wheel", "static", 1.25))
    p_w1_2 = one_sided_p(diff("wheel", "ring_only", 1.25))
    p_w1 = max(p_w1_1, p_w1_2)
    # W2
    p_w2 = two_sided_p(diff("wheel", "wheel_rev"))
    # W4 másodlagos
    p_w4 = one_sided_p(diff("pump_dir", "wheel"))
    # sötétállapot-teszt (Bonferroni a claim-en belül)
    p_sd_1 = one_sided_p(diff("dark_m1", "dark_m0"))
    p_sd_2 = one_sided_p(diff("dark_mm1", "dark_m0"))
    p_sd = max(p_sd_1, p_sd_2)

    fam = holm_adjust({"W1": p_w1, "W2": p_w2, "W4_secondary": p_w4, "sotetallapot": p_sd}, alpha=1.0 - fz["ci_level"])
    res["claims"] = {
        "W1": {"p_static": p_w1_1, "p_ring_only": p_w1_2, "holm": fam["W1"]},
        "W2": {"p_raw": p_w2, "holm": fam["W2"]},
        "W4_secondary": {"p_raw": p_w4, "holm": fam["W4_secondary"]},
        "sotetallapot": {"p_m1_vs_m0": p_sd_1, "p_mm1_vs_m0": p_sd_2, "holm": fam["sotetallapot"]},
    }
    # Ítélet a fő kontrasztra (wheel vs static): a fagyasztott Aer-jóslathoz mérve.
    # A sáv a KÜLÖNBSÉG binomial szórásából számol (pred + obs padló): 3.2905*sqrt(p^2+o^2)
    aer = fz.get("aer_prediction", {}).get("wheel")
    verdict = "NULL"
    if aer is not None:
        obs_std = float(np.std(boot["wheel"]))
        band = 3.2905 * math.sqrt(aer["auc_std"] ** 2 + obs_std ** 2)
        d_auc = auc["wheel"] - aer["auc"]
        if auc["wheel"] > aer["auc"] + band:
            verdict = "ANOMALIA"
        elif abs(d_auc) <= band:
            verdict = "TEXTBOOK"
        else:
            verdict = "NULL"
    # W1 nem teljesül sehol -> NULL felülírja (a definíció szerint)
    if not (res["claims"]["W1"]["holm"]["significant"]):
        if verdict == "ANOMALIA":
            pass  # anomália: nem cáfoljuk, a modellt kell először ellenőrizni
        elif verdict == "TEXTBOOK":
            verdict = "TEXTBOOK"  # Aer-magyarázott, nincs kontroll-túlnyúló előny
        else:
            verdict = "NULL"
    res["verdict"] = verdict
    return res


def positive_control_check(pc_counts, main_counts, fz):
    """Az elemző vakság-tesztje: a beépített hatást ki KELL mutatnia."""
    k_list = fz["checkpoints"]
    n_boot = fz.get("bootstrap_n", 2000)
    seed = fz.get("bootstrap_seed", 20261111)
    pc = {"_arms": ["pc_wheel", "plain_wheel"],
          "pc_wheel": pc_counts["wheel"],
          "plain_wheel": main_counts["wheel"]}
    boot = bootstrap_aucs(pc, k_list, n_boot, seed)
    diff = boot["pc_wheel"] - boot["plain_wheel"]
    mean_diff = float(diff.mean())
    se = float(diff.std(ddof=1)) if diff.std() > 0 else 1e-12
    significant = bool(diff.min() > 0) or bool((diff > 0).mean() > 0.99)
    return {"auc_pc": float(boot["pc_wheel"].mean()),
            "auc_plain": float(boot["plain_wheel"].mean()),
            "mean_diff": mean_diff,
            "se_diff": se,
            "z": mean_diff / se if se > 0 else float("inf"),
            "detected": bool(mean_diff > 4 * se),
            "bootstrap_p_le_0": float((diff <= 0).mean()),
            "note": "ha detected == False, az elemző vak a beépített hatásra -> az elemző érvénytelen (nem a fizika)"}


def main():
    fz = check_frozen()
    if len(sys.argv) < 2:
        raise SystemExit("használat: analysis.py <observed_counts.json>")
    with open(sys.argv[1]) as f:
        counts = json.load(f)
    rep = analyze(counts, fz, label=sys.argv[1])
    if "--pc-counts" in sys.argv:
        i = sys.argv.index("--pc-counts") + 1
        with open(sys.argv[i]) as f:
            pc_counts = json.load(f)
        pc_rep = positive_control_check(pc_counts, counts, fz)
        rep["positive_control"] = pc_rep
    out_path = os.path.join(ROOT, "data", "wheel_analysis_report.json")
    with open(out_path, "w") as f:
        json.dump(rep, f, indent=2, ensure_ascii=False, default=float)
    print(json.dumps(rep, indent=2, ensure_ascii=False, default=float))


if __name__ == "__main__":
    main()
