"""Kerék-menet — fagyasztott elemző **v1.2** (a terven változtatni CSAK verziózott
„amended” kiegészítéssel szabad).

KÖTELEZŐ ELLENŐRZÉSEK FUTTATÁS KÖZBEN:
  - preregistration/frozen_wheel_params_v1.2.json létezik és a .sha256 fájl
    hash-e egyezik;
  - ci_level == 0.99; correction == "holm";
  - claim_family == ["W1", "W2", "W4_secondary", "sotetallapot"] (név szerint);
  - routed variant = "routed_transpiled" (a fagyasztott választás);
  - a frozen JSON „file_hashes” blokkjában felsorolt fájlok sha256-ja egyezik
    (PLAN_WHEEL_v1.2.md, src/wheel/analysis.py, dryrun_wheel.py) — ha bármelyik
    eltér vagy hiányzik, az elemző MEGTAGADJA a futtatást.

Ha bármelyik ellenőrzés bukik, az elemző MEGTAGADJA a futtatást.

Metrikák (fagyasztva):
  R(arm,k) = n1/shots (S |1>-gyel indult);  AUC(arm) = R ellenpontokon átlagolt.
  W1: c1 = AUC(wheel) − 1.25·AUC(static); c2 = AUC(wheel) − 1.25·AUC(ring_only);
      W1-elfogadás: MINDKÉT kontraszt egyoldalú 99%-CI > 0 (Holm után);
      W1 p = max(p_c1, p_c2)  (Bonferroni a W1-en belül — dokumentálva).
      A W1 nullhipotézise a NULLA MARAD (előny-küszöb, változatlan).
  W2: d = AUC(wheel) − AUC(wheel_rev); két oldalú; NULLHIPOTÉZIS az Aer-jósolt
      különbség: d_Aer = AUC_Aer(wheel) − AUC_Aer(wheel_rev) = −0.0114 (a
      lefagyasztott görbékből) — NEM a nulla. A tankönyvi fizika is
      „szignifikánsnak” látszódna a nulla ellen (Maya mérése: 199/300 ≈ 66%),
      mert a wheel/wheel_rev között kapusorrendi tankönyvi különbség van;
      99% CI + Holm.
  W4_secondary: d = AUC(pump_dir) − AUC(wheel); NULLHIPOTÉZIS az Aer-jósolt
      különbség (d_Aer = +0.0098); két oldalú; Holm — a W1/W2-be NEM számít
      bele; ha nem választ el, a pumpa megbukott ezen a rendszeren.
  sotetallapot: d1 = AUC(dark_m1) − AUC(dark_m0); d2 = AUC(dark_mm1) − AUC(dark_m0);
      NULLHIPOTÉZISEK az Aer-jósolt különbségek (d1_Aer = −0.0210;
      d2_Aer = −0.00966); két oldalúak; sotetallapot p = max(p1, p2); Holm.
      A cáfolati feltétel (Maya/tulajdonos vita döntőbírája): a mérce a
      tankönyvi baseline-tól való ELTARODÁS, nem a nulla — ha egyik chirális
      ág sem TÉR EL szignifikánsan az Aer-jóslttól 99% CI + Holm után, a
      "forgás tartja S-t" hipotézis ezen a berendezésen cáfolva (Maya-ág
      igazolva); ha MINDKÉT chirális ág mérhetően JOBB megtartást ad, mint az
      Aer-modell, a tulajdonos-ág kap támogatást (először kalibrációs/modell-
      audit!).
  A riportban MINDENHOL külön: „tankonyvi varakozas: teljesul / nem teljesul”
  (W2, W4_secondary — külön-külön; sotetallapot — d1 és d2 külön, claim-szinten
  a kettő AND-je). „teljesul” akkor, ha a kontraszt 99% CI-je tartalmazza az
  Aer-jósolt értéket; egyébként „nem teljesul”. Ez a sor NEM azonos a Holm
  családi döntéssel — a riportban egymás mellett, név szerint szerepel mindkettő.

Ítéletek — KONTRASZT-ALAPÚ (v1.2; a v1.1 abszolút-AUC(wheel) összevetése
leváltva — a v1.1 kód és a korábbi docstring („wheel vs static”) nem volt
összhangban, és kalibráció-eltérésnél az ítélet NULL-ba csúszott):
  d_static = AUC(wheel) − AUC(static);   d_ring = AUC(wheel) − AUC(ring_only).
  Mindkettőt az Aer-jósolt kontrasztokhoz (d_static,Aer = −0.0050;
  d_ring,Aer = −0.2598; a lefagyasztott görbék különbségei) mérve. Az
  alkalmazandó Aer-referencia a BEKÜLDÉS NAPI kalibrációból ÚJRASZÁMOLT
  jóslat; a frozen aer_prediction a preregisztrált alap (PLAN_WHEEL_v1.2,
  3. pont; a v1.1-es jóslattal való eltérés a beküldéskori kalibráció- audit
  része).
  TEXTBOOK:  mindkét |d_obs − d_Aer| a hibrid 99% CI-sávon belül;
  ANOMALIA:  bármelyik d_obs > d_Aer + sáv (az Aer ALÁBECSÜLI a megtartást) —
             ELŐSZÖR kalibrációs/modellhibát kell keresni (T1/T2 drift,
             readout, csatolás-kalibráció), és csak utána bármilyen
             értelmezés; a claim NEM kerül kikiáltásra az anomália-feloldás
             előtt;
  NULL:      különben (beleértve az Aer-sáv ALATTi eltérést, és a nem
             teljesülő W1-et) — NULL-t NULL-ként közöljük.
  Sáv: 3.2905·sqrt(σ²_Aer,kontraszt + σ²_obs,kontraszt), ahol
       σ²_Aer,kontraszt = σ²_arm1 + σ²_arm2 (a lefagyasztott Aer-std-k
       kovarianciája nincs rögzítve → függetlenséget feltételezünk); a 99% a
       ci_level-lel azonos.

Bootstrap: 2000 újraminta, multinomiális (a shot-okból), seed = frozen
"bootstrap_seed". Az eredmény data/wheel_analysis_report_v1_2.json-be kerül
(a v1.1-es jelentés megőrződik); a dryrun a saját jelentését a
data/wheel_dryrun_report_v1_2.json-ba írja.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
FROZEN = os.path.join(ROOT, "preregistration", "frozen_wheel_params_v1.2.json")
FROZEN_SHA = os.path.join(ROOT, "preregistration", "frozen_wheel_params_v1.2.json.sha256")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def check_frozen():
    if not (os.path.exists(FROZEN) and os.path.exists(FROZEN_SHA)):
        raise SystemExit("HIBA: frozen_wheel_params_v1.2.json / .sha256 hiányzik — az elemző nem futhat.")
    actual = sha256_file(FROZEN)
    recorded = None
    for line in open(FROZEN_SHA):
        parts = line.split()
        if len(parts) >= 2 and parts[-1] == "frozen_wheel_params_v1.2.json":
            recorded = parts[0]
            break
    if recorded is None:
        raise SystemExit("HIBA: a .sha256 fajlban nincs frozen_wheel_params_v1.2.json bejegyzés.")
    if actual != recorded:
        raise SystemExit(f"HIBA: frozen_wheel_params_v1.2.json hash eltér ({actual} != {recorded}) — az elemző nem futhat.")
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
    fh = fz.get("file_hashes") or {}
    if not fh:
        raise SystemExit("HIBA: a v1.2 frozen JSON-ban nincs \"file_hashes\" blokk — az elemző nem futhat.")
    for rel, expected in fh.items():
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            raise SystemExit(f"HIBA: {rel} hiányzik — a v1.2 fagyasztott integritás megsérült; az elemző nem futhat.")
        actual = sha256_file(path)
        if actual != expected:
            raise SystemExit(f"HIBA: {rel} hash eltér ({actual} != {expected}) — a v1.2 fagyasztott integritás megsérült; az elemző nem futhat.")
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


def two_sided_p_vs(boot_diff: np.ndarray, null: float) -> float:
    # két oldalú p egy NEM NULLA nullhipotézissel szemben (Aer-jósolt érték)
    return float(min(1.0, 2.0 * min((boot_diff <= null).mean(), (boot_diff >= null).mean())))


def ci99(boot_diff: np.ndarray):
    lo, hi = np.quantile(boot_diff, [0.005, 0.995])
    return float(lo), float(hi)


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

    aer = fz.get("aer_prediction", {})
    ap = {arm: float(v["auc"]) for arm, v in aer.items()}
    a_std = {arm: float(v.get("auc_std", 0.0)) for arm, v in aer.items()}

    def expectation_block(d_boot, aer_null):
        lo, hi = ci99(d_boot)
        inside = bool(lo <= aer_null <= hi)
        return {"aer_null": float(aer_null),
                "measured_diff": float(d_boot.mean()),
                "ci99_lo": float(lo),
                "ci99_hi": float(hi),
                "tankonyvi_varakozas": "teljesul" if inside else "nem teljesul"}

    res = {"label": label, "aucs": auc}
    # W1: mindkét feltétel (Bonferroni a claim-en belül) — nullhipotézis: ZERO
    p_w1_1 = one_sided_p(diff("wheel", "static", 1.25))
    p_w1_2 = one_sided_p(diff("wheel", "ring_only", 1.25))
    p_w1 = max(p_w1_1, p_w1_2)
    # W2 — nullhipotézis az Aer-jósolt különbség (NEM a nulla)
    d_w2 = diff("wheel", "wheel_rev")
    null_w2 = ap["wheel"] - ap["wheel_rev"]
    p_w2 = two_sided_p_vs(d_w2, null_w2)
    # W4 másodlagos — nullhipotézis az Aer-jósolt különbség (NEM a nulla)
    d_w4 = diff("pump_dir", "wheel")
    null_w4 = ap["pump_dir"] - ap["wheel"]
    p_w4 = two_sided_p_vs(d_w4, null_w4)
    # sötétállapot-teszt (Bonferroni a claim-en belül) — nullhipotézisek: Aer
    d_sd1 = diff("dark_m1", "dark_m0")
    d_sd2 = diff("dark_mm1", "dark_m0")
    null_d1 = ap["dark_m1"] - ap["dark_m0"]
    null_d2 = ap["dark_mm1"] - ap["dark_m0"]
    p_sd_1 = two_sided_p_vs(d_sd1, null_d1)
    p_sd_2 = two_sided_p_vs(d_sd2, null_d2)
    p_sd = max(p_sd_1, p_sd_2)

    fam = holm_adjust({"W1": p_w1, "W2": p_w2, "W4_secondary": p_w4, "sotetallapot": p_sd}, alpha=1.0 - fz["ci_level"])
    sd1_blk = expectation_block(d_sd1, null_d1)
    sd2_blk = expectation_block(d_sd2, null_d2)
    res["claims"] = {
        "W1": {"p_static": p_w1_1, "p_ring_only": p_w1_2, "holm": fam["W1"],
               "note": "a W1 nullhipotézise továbbra is a nulla (1.25-ös előny-küszöb); az Aer-jóslat szerinti tankönyvi várakozás: AUC(wheel)≈AUC(static) és AUC(wheel)≪AUC(ring_only) — a tankönyv W1-et NULL-nak várja (szimuláció: 0.471 vs 0.730)"},
        "W2": {"p_raw": p_w2, "holm": fam["W2"], **expectation_block(d_w2, null_w2)},
        "W4_secondary": {"p_raw": p_w4, "holm": fam["W4_secondary"], **expectation_block(d_w4, null_w4)},
        "sotetallapot": {"p_m1_vs_m0": p_sd_1, "p_mm1_vs_m0": p_sd_2, "holm": fam["sotetallapot"],
                         "d1": sd1_blk, "d2": sd2_blk,
                         "tankonyvi_varakozas": "teljesul" if (sd1_blk["tankonyvi_varakozas"] == "teljesul"
                                                                and sd2_blk["tankonyvi_varakozas"] == "teljesul")
                                                else "nem teljesul"},
    }
    # Ítélet — KONTRASZT-ALAPÚ (v1.2); a beküldés napi kalibrációból újraszámolt
    # Aer-jóslat az alkalmazandó referencia (a frozen aer_prediction a
    # preregisztrált alap) — lásd a docstringet és PLAN_WHEEL_v1.2 3. pontot.
    ds = boot["wheel"] - boot["static"]
    dr = boot["wheel"] - boot["ring_only"]
    aer_ds = ap["wheel"] - ap["static"]
    aer_dr = ap["wheel"] - ap["ring_only"]
    aer_ds_std2 = a_std["wheel"] ** 2 + a_std["static"] ** 2
    aer_dr_std2 = a_std["wheel"] ** 2 + a_std["ring_only"] ** 2
    band_ds = 3.2905 * math.sqrt(aer_ds_std2 + float(np.std(ds)) ** 2)
    band_dr = 3.2905 * math.sqrt(aer_dr_std2 + float(np.std(dr)) ** 2)
    obs_ds, obs_dr = float(np.mean(ds)), float(np.mean(dr))
    res["contrasts"] = {
        "wheel_minus_static": {"observed": obs_ds, "aer_predicted": float(aer_ds),
                               "band_99": float(band_ds),
                               "z": float((obs_ds - aer_ds) / band_ds) if band_ds > 0 else 0.0},
        "wheel_minus_ring_only": {"observed": obs_dr, "aer_predicted": float(aer_dr),
                                  "band_99": float(band_dr),
                                  "z": float((obs_dr - aer_dr) / band_dr) if band_dr > 0 else 0.0},
    }
    if obs_ds > aer_ds + band_ds or obs_dr > aer_dr + band_dr:
        verdict = "ANOMALIA"
    elif abs(obs_ds - aer_ds) <= band_ds and abs(obs_dr - aer_dr) <= band_dr:
        verdict = "TEXTBOOK"
    else:
        verdict = "NULL"
    # W1 nem teljesül sehol -> NULL felülírja (a definíció szerint; ANOMALIA-t
    # W1 bukással sosem bírálunk felül — először a modellt/kalibrációt kell
    # ellenőrizni)
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
    out_path = os.path.join(ROOT, "data", "wheel_analysis_report_v1_2.json")
    with open(out_path, "w") as f:
        json.dump(rep, f, indent=2, ensure_ascii=False, default=float)
    print(json.dumps(rep, indent=2, ensure_ascii=False, default=float))


if __name__ == "__main__":
    main()
