"""Elemző — D(k), BLP, csúcskeresés, bootstrap CI, ítélet (terv 4. fejezet).

A DÖNTÉSI SZABÁLY FORRÁSA: ``preregistration/frozen_params_v1.4.json``
(hash: ``preregistration/frozen_params_v1.4.sha256``). A v1.3 AMENDED —
a v1.0/v1.1 (95% CI) és a v1.2 ELÉRVÉNYTELEN; minden döntési küszöb 99% CI + Holm.
A kód NEM tartalmaz az ítéletet befolyásoló küszöböt "beégetve": minden
küszöb (P1 1:0.71:0.58 ±20%, P2/P3/anomália 99% CI + Holm a claim-családon
[P2, P3, anomaly], dip_frac, ablakok, várt görbék, anomália-határ, bootstrap
paraméterek) a fagyasztott fájlból olvasódik. Hash-eltérés esetén az elemzés
NEM fut le (RuntimeError) — FAIL-CLOSED, a v1.3 mezőire (version/correction/
ci_level/claim_family/file_hashes) is.

Változások a v1.2-höz képest (preregistration/PLAN_v1.3.md, Maya beküldés előtti
átnézése, 2026-11-12 09:05 UTC):
- ANOMALIA-ág: a csúcs nélküli (A = NaN) bootstrap-minták "nincs anomalia"
  mintaként számítanak (A := −∞), NEM esnek ki; a 99%-os alsó CI a −∞ mintákkal
  együtt, ``np.quantile(..., method="lower")``-rel számol (sosem interpolál
  végtelenek között); a p-érték ``(samples <= bound).mean()`` az ÖSSZES mintán.
- Ha a pontbecslésben egy csúcsot váró karon (a fagyasztott ablak nem null:
  n1, n2, n3, cut, noisy) nincs csúcs: az ág eredménye "nincs anomalia, ok:
  nincs csúcs" (peak_found: false mező), az ITÉLET pedig fail-closed
  ``ELEMZO-HIBA / ERVENYTELEN`` — soha nem NULL.
- Az elemző ``np.errstate(all="raise")`` alatt fut; lebegőpontos kivétel esetén
  az elemzés NEM fut le (a hívó ELEMZO-HIBA-t kap / a main 3-as kóddal kilép).
- A bootstrap CI-k és a riport mutatják a peak_found / peakless-szám mezőket.

Verdict-értékek: ``TEXTBOOK-MEGEROSITVE`` | ``NULL`` | ``ANOMALIA`` |
``ELEMZO-HIBA / ERVENYTELEN``.
A koherencia-ág SOHA nem része a fő ítéletnek (terv 3.2) — külön blokkban
jelenik meg, "MÁSODLAGOS" jelöléssel.

Türelmes bootstrap: a multinomialis bootstrap marginálonként binomialis
mintavétellel azonos (a 2 kimenetű marginálisra) — ez pont a D(k)-t alkotó
mennyiség. Seedelt, reprodukálható.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from . import config

REPO_ROOT = Path(__file__).resolve().parents[1]
FROZEN_PARAMS_PATH = REPO_ROOT / "preregistration" / "frozen_params_v1.4.json"
FROZEN_SHA256_PATH = REPO_ROOT / "preregistration" / "frozen_params_v1.4.sha256"
RAW_COUNTS_PATH = REPO_ROOT / "data" / "raw_counts.json"

VERDICT_TEXTBOOK = "TEXTBOOK-MEGEROSITVE"
VERDICT_NULL = "NULL"
VERDICT_ANOMALIA = "ANOMALIA"
VERDICT_NO_RETURN = "NINCS-VISSZATERES"
VERDICT_ANALYSIS_ERROR = "ELEMZO-HIBA / ERVENYTELEN"
VERDICTS = (VERDICT_TEXTBOOK, VERDICT_NULL, VERDICT_ANOMALIA, VERDICT_NO_RETURN, VERDICT_ANALYSIS_ERROR)


# ---------------------------------------------------------------------------
# Fagyasztott paraméterek integritása
# ---------------------------------------------------------------------------
def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_sha256_file(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2 and len(parts[0]) == 64:
            out[parts[-1]] = parts[0].lower()
    return out


def verify_frozen_params(frozen_path: Path = FROZEN_PARAMS_PATH, sha_path: Path = FROZEN_SHA256_PATH) -> str:
    """Ellenőrzi a fagyasztott fájl hash-ét; eltérés esetén RuntimeError."""
    if not frozen_path.exists():
        raise RuntimeError(f"hiányzik a fagyasztott paraméterfájl: {frozen_path}")
    if not sha_path.exists():
        raise RuntimeError(f"hiányzik a hash-fájl: {sha_path}")
    known = _parse_sha256_file(sha_path.read_text(encoding="utf-8"))
    recorded = known.get(frozen_path.name)
    if recorded is None:
        raise RuntimeError(f"a hash-fájl nem tartalmaz bejegyzést ehhez: {frozen_path.name}")
    actual = sha256_file(frozen_path)
    if actual != recorded:
        raise RuntimeError(
            "A PREREGISZTRÁLT frozen_params.json MEGVÁLTOZOTT!\n"
            f"  rögzített hash: {recorded}\n  aktuális hash:  {actual}\n"
            "A döntési szabály ilyenkor NEM futtatható — állj meg és jelentsd."
        )
    return actual


def verify_frozen_fields(frozen: dict) -> None:
    """v1.4 módosítás-kötelező mezői — eltérés = RuntimeError (fail-closed)."""
    if frozen.get("version") != "1.4":
        raise RuntimeError("frozen_params_v1.4.json: version != '1.4' — a v1.0/v1.1/v1.2/v1.3 érvénytelen.")
    if frozen.get("correction") != "holm":
        raise RuntimeError("correction != 'holm' — a fagyasztott fájl nem egyezik.")
    if list(frozen.get("claim_family", [])) != ["P2", "P3", "anomaly"]:
        raise RuntimeError("claim_family nem [P2, P3, anomaly].")
    if float(frozen.get("bootstrap", {}).get("ci_level")) != 0.99:
        raise RuntimeError("bootstrap.ci_level != 0.99.")
    if float(frozen.get("tolerances", {}).get("ci_level")) != 0.99:
        raise RuntimeError("tolerances.ci_level != 0.99.")
    # Maya 5. pontja: az elemző ÉS a dryrun sha256-ja a frozen JSON-ben —
    # itt visszaellenőrizzük a munkaprogram fájljait (fail-closed).
    file_hashes = frozen.get("file_hashes")
    if not isinstance(file_hashes, dict) or not file_hashes:
        raise RuntimeError("frozen_params_v1.4.json: hiányzó file_hashes (elemző és dryrun sha256).")
    for rel_path, expected in sorted(file_hashes.items()):
        target = REPO_ROOT / rel_path
        if not target.exists():
            raise RuntimeError(f"file_hashes: hiányzik a fájl: {rel_path} — ÁLLJ MEG és jelentsd.")
        actual = sha256_file(target)
        if actual != str(expected).lower():
            raise RuntimeError(
                f"file_hashes: a(z) {rel_path} megváltozott a fagyasztás óta!\n"
                f"  rögzített hash: {expected}\n  aktuális hash:  {actual}\n"
                "A döntési szabály ilyenkor NEM futtatható — állj meg és jelentsd."
            )


def load_frozen_params(frozen_path: Path = FROZEN_PARAMS_PATH, sha_path: Path = FROZEN_SHA256_PATH) -> tuple[dict, str]:
    actual = verify_frozen_params(frozen_path, sha_path)
    with frozen_path.open("r", encoding="utf-8") as f:
        frozen = json.load(f)
    verify_frozen_fields(frozen)
    return frozen, actual


# ---------------------------------------------------------------------------
# Counts → valószínűségek
# ---------------------------------------------------------------------------
def s_one_count_and_total(counts: dict[str, int]) -> tuple[int, int]:
    total = sum(counts.values())
    ones = sum(n for bits, n in counts.items() if int(bits, 2) & 1)
    return ones, total


def s_zero_count_and_total(counts: dict[str, int]) -> tuple[int, int]:
    total = sum(counts.values())
    zeros = total - sum(n for bits, n in counts.items() if int(bits, 2) & 1)
    return zeros, total


def s_one_fraction(counts: dict[str, int]) -> float:
    ones, total = s_one_count_and_total(counts)
    return ones / total if total else float("nan")


def s_zero_fraction(counts: dict[str, int]) -> float:
    zeros, total = s_zero_count_and_total(counts)
    return zeros / total if total else float("nan")


def k_values(ds: dict) -> list[int]:
    return sorted(int(k) for k in ds)


def p1_curve(arm_counts: dict[str, dict], arm: str, init: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """p1-hat görbe + per-k (ones, total) — a bootstrap újramintavételezéshez."""
    by_k = arm_counts[arm][init]
    ks = k_values(by_k)
    p, ones, tot = [], [], []
    for k in ks:
        o, n = s_one_count_and_total(by_k[str(k)])
        ones.append(o)
        tot.append(n)
        p.append(o / n if n else float("nan"))
    return np.array(ks), np.array(p), (np.array(ones), np.array(tot))


def pplus_curve(arm_counts: dict[str, dict], arm: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    by_k = arm_counts[arm][config.COH_INIT]
    ks = k_values(by_k)
    p, zeros, tot = [], [], []
    for k in ks:
        z, n = s_zero_count_and_total(by_k[str(k)])
        zeros.append(z)
        tot.append(n)
        p.append(z / n if n else float("nan"))
    return np.array(ks), np.array(p), (np.array(zeros), np.array(tot))


# ---------------------------------------------------------------------------
# D(k), BLP, csúcskeresés
# ---------------------------------------------------------------------------
def blp(D: np.ndarray) -> float:
    """BLP-mérték: a pozitív D-növekmények összege (3. fázis szerinti módon)."""
    return float(np.sum(np.maximum(0.0, np.diff(D))))


def find_return_peak(D: np.ndarray, window: tuple[int, int] | None, dip_frac: float):
    """Az ELSŐ visszatérési csúcs lépésindexe a fagyasztott ablakban.

    Visszaad: (t, D[t]) vagy (None, None), ha
      - az ablak None (nem keresendő, pl. n0 alapvonal),
      - D sehol nem esik dip_frac alá (a pozitív kontroll: csatolások kikapcsolva,
        D(k) ≡ konstans → nincs visszatérés → nincs csúcs → verdict NULL).
    """
    if window is None:
        return None, None
    lo, hi = int(window[0]), int(window[1])
    d0 = float(D[0])
    if not np.isfinite(d0) or d0 <= 0.0:
        return None, None
    k_dip = next((k for k in range(0, hi + 1) if D[k] < dip_frac * d0), None)
    if k_dip is None:
        return None, None
    lo = max(lo, k_dip)
    t = int(lo + np.argmax(D[lo:hi + 1]))
    return t, float(D[t])


def analyze_branch_point(D: np.ndarray, windows, dip_frac):
    """Minden karra (point-estimate): BLP, t_vissza, A_vissza (normált), peak_found."""
    metrics = {}
    for arm, d in D.items():
        w = windows.get(arm)
        window = (w[0], w[1]) if w else None
        t, peak = find_return_peak(d, window, dip_frac)
        d0 = float(d[0])
        a = float(peak / d0) if (peak is not None and d0 > 0) else None
        metrics[arm] = {
            "t_vissza": t,
            "A_vissza": a,
            "D_first_peak": peak,
            "D0": d0,
            "BLP": blp(d),
            "peak_found": bool(t is not None),
        }
    return metrics


# ---------------------------------------------------------------------------
# Holm-korrekció (v1.3: claim-család [P2, P3, anomaly], α = 0.01)
# ---------------------------------------------------------------------------
def holm_adjust(pvals: dict, alpha: float = 0.01):
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


def _p_le_or_ge(samples: np.ndarray, bound: float, side: str) -> float:
    """Bootstrap p-érték egy oldalra; samples = bootstrap A-szerű eloszlás."""
    samples = np.asarray(samples, dtype=float)
    samples = samples[np.isfinite(samples)]
    if samples.size == 0:
        return 1.0
    if side == "le":
        return float((samples <= bound).mean())
    return float((samples >= bound).mean())


# ---------------------------------------------------------------------------
# Bootstrap (2000×, seed-elt) — a verdict-CI-k forrása
# ---------------------------------------------------------------------------
def _boot_draws(rng: np.random.Generator, tot: np.ndarray, p_hat: np.ndarray, n: int) -> np.ndarray:
    """Multinomiális marginális = binomiális újramintavételezés a (K+1) pontokon."""
    p_safe = np.clip(p_hat, 0.0, 1.0)
    draws = rng.binomial(tot, p_safe, size=(n, p_safe.shape[0])).astype(float)
    return draws / tot


def _neg_inf_samples(samples) -> np.ndarray:
    """A csúcs nélküli (NaN) bootstrap-minták 'nincs anomalia' mintákká (−∞) válnak."""
    arr = np.array([s for s in samples], dtype=float)
    return np.where(np.isfinite(arr), arr, -np.inf)


def analyze_dataset(dataset: dict, frozen: dict) -> dict:
    """A v1.3 fail-closed kapuja: minden lebegőpontos kivétel RuntimeError helyett
    a hívó felé propagálódó FloatingPointError — az eredmény így SOSEM készül
    csendben hibás számokból (np.errstate(all='raise'))."""
    with np.errstate(all="raise"):
        return _analyze_dataset_impl(dataset, frozen)


def _analyze_dataset_impl(dataset: dict, frozen: dict) -> dict:
    K = int(frozen["K"])
    tol = frozen["tolerances"]
    windows = {arm: (w if w else None) for arm, w in frozen["windows"].items()}
    dip_frac = float(tol["dip_frac"])
    n_boot = int(frozen["bootstrap"]["resamples"])
    boot_seed = int(frozen["bootstrap"]["seed"])
    ci = float(tol["ci_level"])
    alpha = 1.0 - ci

    pop_counts = dataset["population"]
    coh_counts = dataset["coherence"]

    # --- Point-estimate görbék ---
    D_pop, D_coh = {}, {}
    p_hats = {}   # arm → init/branch → (p_hat, total) a bootstraphez
    for arm in config.ARM_NAMES:
        ks, p1_1, (o1, t1) = p1_curve(pop_counts, arm, "1")
        _, p1_0, (o0, t0) = p1_curve(pop_counts, arm, "0")
        D_pop[arm] = np.abs(p1_1 - p1_0)
        _, pplus, (z, tz) = pplus_curve(coh_counts, arm)
        D_coh[arm] = np.abs(2.0 * pplus - 1.0)
        p_hats[arm] = {
            "1": (p1_1, t1), "0": (p1_0, t0), "+": (pplus, tz),
        }

    point_pop = analyze_branch_point(D_pop, windows, dip_frac)
    point_coh = analyze_branch_point(D_coh, windows, dip_frac)

    # --- Bootstrap replikátok ---
    rng = np.random.default_rng(boot_seed)
    boot = {arm: {"t": [], "A": [], "D": []} for arm in config.ARM_NAMES}
    boot_coh_t = {arm: [] for arm in config.ARM_NAMES}
    for arm in config.ARM_NAMES:
        p1_1, tot1 = p_hats[arm]["1"]
        p1_0, tot0 = p_hats[arm]["0"]
        pp, totc = p_hats[arm]["+"]
        d1 = _boot_draws(rng, tot1, p1_1, n_boot)
        d0 = _boot_draws(rng, tot0, p1_0, n_boot)
        dp = np.abs(d1 - d0)
        boot[arm]["D"].append(dp)
        window = windows.get(arm)
        window = (window[0], window[1]) if window else None
        for b in range(n_boot):
            t, peak = find_return_peak(dp[b], window, dip_frac)
            boot[arm]["t"].append(t)
            d0b = dp[b, 0]
            boot[arm]["A"].append(float(peak / d0b) if (peak is not None and d0b > 0) else np.nan)
        # koherencia-ág: csak t_vissza (informatív)
        dplus = _boot_draws(rng, totc, pp, n_boot)
        dc = np.abs(2.0 * dplus - 1.0)
        for b in range(n_boot):
            t, _ = find_return_peak(dc[b], window, dip_frac)
            boot_coh_t[arm].append(t)

    def _ci(samples, lo_q, hi_q):
        arr = np.array([s for s in samples if s is not None], dtype=float)
        arr = arr[np.isfinite(arr)]
        if arr.size == 0:
            return (float("nan"), float("nan"))
        return (float(np.percentile(arr, 100 * lo_q)), float(np.percentile(arr, 100 * hi_q)))

    def _ci_neginf(samples, lo_q, hi_q):
        """Bootstrap CI a 'nincs csúcs' mintákkal együtt — sosem interpolál −∞ között."""
        arr = _neg_inf_samples(samples)
        if arr.size == 0:
            return (float("nan"), float("nan"))
        return (
            float(np.quantile(arr, lo_q, method="lower")),
            float(np.quantile(arr, hi_q, method="lower")),
        )

    def _n_peakless(samples) -> int:
        return int(np.count_nonzero(~np.isfinite(np.array(samples, dtype=float))))

    q = alpha / 2.0
    boot_ci = {}
    for arm in config.ARM_NAMES:
        boot_ci[arm] = {
            "t_vissza_ci99": _ci(boot[arm]["t"], q, 1 - q),
            "A_vissza_ci99": _ci_neginf(boot[arm]["A"], q, 1 - q),
            "n_peakless_bootstrap": _n_peakless(boot[arm]["A"]),
        }

    # --- Fail-closed: a csúcsot váró karokon a pontbecslésnek CSÚCSOT kell adnia ---
    peak_expecting = [arm for arm in config.ARM_NAMES if windows.get(arm)]
    missing_peaks = [arm for arm in peak_expecting if point_pop[arm]["t_vissza"] is None]
    analysis_error = bool(missing_peaks)

    # --- P1: arányok (pontbecslés, ±20% tűrés a fagyasztott fájlból) ---
    esp = tol["p1_expected_ratios"]
    tol_p1 = float(tol["p1_ratio_tol_rel"])
    t1 = point_pop["n1"]["t_vissza"]
    p1_details = {}
    p1_ok = t1 is not None
    for arm in ("n1", "n2", "n3"):
        t = point_pop[arm]["t_vissza"]
        exp = float(esp[arm])
        ratio = (t / t1) if (t is not None and t1) else None
        ok = ratio is not None and abs(ratio - exp) <= tol_p1 * exp
        p1_details[arm] = {"t_vissza": t, "expected_ratio": exp, "ratio_vs_n1": ratio, "ok": ok}
        p1_ok = p1_ok and ok

    # --- P2: A_vissza(n3) ≥ A_vissza(n1) az n3 első csúcsánál, 99% CI ---
    k3_star = point_pop["n3"]["t_vissza"]
    p2_detail = {"k3_star": k3_star}
    p2_p = 1.0
    if k3_star is None:
        p2_ok = False
        p2_detail["reason"] = "n3 t_vissza nem található"
        p2_detail["ci99_diff"] = None
    else:
        d_n3 = boot["n3"]["D"][0]  # (n_boot, K+1)
        d_n1 = boot["n1"]["D"][0]
        d0_3 = d_n3[:, 0]
        d0_1 = d_n1[:, 0]
        a3 = d_n3[:, k3_star] / np.where(d0_3 > 0, d0_3, np.nan)
        a1 = d_n1[:, k3_star] / np.where(d0_1 > 0, d0_1, np.nan)
        diff = a3 - a1
        diff = diff[np.isfinite(diff)]
        ci_lo = float(np.percentile(diff, 100 * q)) if diff.size else float("nan")
        p2_p = float((diff <= 0.0).mean()) if diff.size else 1.0
        p2_detail.update({
            "A_vissza_n3_at_k3": point_pop["n3"]["A_vissza"],
            "A_vissza_n1_at_k3": float(D_pop["n1"][k3_star] / D_pop["n1"][0]),
            "ci99_diff": (ci_lo, float(np.percentile(diff, 100 * (1 - q)))) if diff.size else None,
            "p_boot": p2_p,
        })

    # --- P3: cut vs n3 — vagy ≥20%-kal alacsonyabb (CI), vagy ≥2 lépés eltolódás (CI) ---
    t_cut = point_pop["cut"]["t_vissza"]
    t_n3 = point_pop["n3"]["t_vissza"]
    p3_height_rel = float(tol["p3_height_rel"])
    p3_shift_min = int(tol["p3_shift_min_steps"])
    raw_shift_pairs = list(zip(boot["cut"]["t"], boot["n3"]["t"]))
    raw_height_pairs = list(zip(boot["cut"]["A"], boot["n3"]["A"]))
    p3_discarded_shift = sum(1 for c, n in raw_shift_pairs if c is None or n is None)
    p3_discarded_height = sum(1 for c, n in raw_height_pairs if not (np.isfinite(c) and np.isfinite(n)))
    shift_samples = np.array(
        [c - n for c, n in raw_shift_pairs if (c is not None and n is not None)],
        dtype=float,
    )
    # Maya 3. pont: ha a cut csucsa hianyzik a bootstrap-mintaban, alacsonyabb mintakent (c := 0.0) szamit:
    height_samples = np.array(
        [(c if np.isfinite(c) else 0.0) - (1.0 - p3_height_rel) * n for c, n in raw_height_pairs
         if np.isfinite(n)],
        dtype=float,
    )
    shift_ci = (float(np.percentile(shift_samples, 100 * q)), float(np.percentile(shift_samples, 100 * (1 - q)))) if shift_samples.size else (float("nan"), float("nan"))
    height_ci = (float(np.percentile(height_samples, 100 * q)), float(np.percentile(height_samples, 100 * (1 - q)))) if height_samples.size else (float("nan"), float("nan"))
    shift_ok = bool(shift_samples.size and np.isfinite(shift_ci[0]) and shift_ci[0] >= p3_shift_min)
    height_ok = bool(height_samples.size and np.isfinite(height_ci[1]) and height_ci[1] <= 0.0)
    # a "cut ≥ +2 lépés / ≥ 20%-kal alacsonyabb" esemény bootstrap-p-értéke:
    # kicsi p ⇒ az eltolodás ELÉRI a p3_shift_min-t / a magasság eléri a 0.8·A_n3-at
    p3_p_shift = float((shift_samples < p3_shift_min).mean()) if shift_samples.size else 1.0
    p3_p_height = float((height_samples > 0.0).mean()) if height_samples.size else 1.0
    p3_p = min(1.0, 2.0 * min(p3_p_shift, p3_p_height))  # Bonferroni a 2 ág között
    p3_ok = shift_ok or height_ok  # provisional — a végleges döntés Holm után
    p3_detail = {
        "t_cut": t_cut, "t_n3": t_n3, "shift_steps": (t_cut - t_n3) if (t_cut is not None and t_n3 is not None) else None,
        "shift_ci99": shift_ci, "shift_ok": shift_ok,
        "A_cut": point_pop["cut"]["A_vissza"], "A_n3": point_pop["n3"]["A_vissza"],
        "height_margin_ci99": height_ci, "height_ok": height_ok,
        "p3_min_shift_steps": p3_shift_min, "p3_height_rel": p3_height_rel,
        "p_boot_shift": p3_p_shift, "p_boot_height": p3_p_height, "p_boot": p3_p,
    }

    # --- ANOMÁLIA: a visszatérés túllépi-e a zajtalan unitér maximumot, 99% CI-val ---
    # v1.3 (Maya): a csúcs nélküli (NaN) bootstrap-minták "nincs anomalia" minták
    # (A := −∞), NEM esnek ki; a CI sosem interpolál végtelennel-végtelen közt;
    # a p-érték (samples <= bound).mean() az ÖSSZES mintán.
    anon_ref = frozen.get("anomaly_reference", {}).get("population", {})
    anomaly_details = {}
    anomalia = False
    anom_p_parts = []
    n_checked = 0
    for arm in config.ARM_NAMES:
        bound = anon_ref.get(arm)
        peakless = _n_peakless(boot[arm]["A"])
        point_peak = bool(point_pop[arm]["t_vissza"] is not None)
        if bound is None:
            anomaly_details[arm] = {
                "checked": False,
                "reason": "nincs anomália-referencia a fagyasztott fájlban",
                "peak_found": point_peak,
                "n_peakless_bootstrap": peakless,
            }
            continue
        samples = _neg_inf_samples(boot[arm]["A"])  # az ÖSSZES minta, −∞-nel kitöltve
        ci_lo = float(np.quantile(samples, q, method="lower"))
        over = bool(ci_lo > float(bound))
        p_le = float((samples <= float(bound)).mean())
        anom_p_parts.append(p_le)
        n_checked += 1
        anomaly_details[arm] = {
            "checked": True,
            "bound": float(bound),
            "ci99_lo": ci_lo,
            "anomaly": over,
            "peak_found": point_peak,
            "n_peakless_bootstrap": peakless,
            "p_boot": p_le,
        }
        if not point_peak:
            anomaly_details[arm]["no_peak_in_point_estimate"] = True
        anomalia = anomalia or over
    anom_p = min(1.0, (min(anom_p_parts) if anom_p_parts else 1.0) * max(n_checked, 1))  # Bonferroni a karok között

    # --- Holm a claim-családon [P2, P3, anomaly] (α = 0.01) — v1.3 ---
    holm = holm_adjust({"P2": p2_p, "P3": p3_p, "anomaly": anom_p}, alpha=1.0 - float(tol["ci_level"]))
    p2_ok = bool(holm["P2"]["significant"])
    p3_ok = bool(holm["P3"]["significant"])
    anom_sig = bool(holm["anomaly"]["significant"])

    # --- Ítélet (csak a populációs ág!) — fail-closed: a csúcs nélküli csúcs-váró kar ELEMZO-HIBA ---
    if analysis_error:
        verdict = VERDICT_NO_RETURN
        verdict_reason = (
            "NINCS-VISSZATERES (adatkimenet): a pontbecslésben nincs csúcs a csúcsot váró "
            f"kar(ok)on: {', '.join(missing_peaks)} — az ítélet nem NULL, nem TEXTBOOK és nem ANOMALIA."
        )
    elif anom_sig:
        verdict = VERDICT_ANOMALIA
        verdict_reason = "valamely kar A_vissza-je 99% CI-val túllépi a zajtalan unitér maximumot (Holm után szignifikáns)"
    elif p1_ok and p2_ok and p3_ok:
        verdict = VERDICT_TEXTBOOK
        verdict_reason = "P1, P2 és P3 mind teljesülnek (99% CI + Holm)"
    else:
        verdict = VERDICT_NULL
        missing = [name for name, ok in (("P1", p1_ok), ("P2", p2_ok), ("P3", p3_ok)) if not ok]
        verdict_reason = "nem teljesül: " + ", ".join(missing)

    return {
        "frozen_K": K,
        "dip_frac": dip_frac,
        "population": {
            "D": {arm: D_pop[arm].tolist() for arm in config.ARM_NAMES},
            "metrics": point_pop,
            "bootstrap_ci99": boot_ci,
            "holm": holm,
            "p_P2": p2_p, "p_P3": p3_p, "p_anomaly": anom_p,
            "P1": {"ok": p1_ok, "details": p1_details},
            "P2": {"ok": p2_ok, **p2_detail},
            "P3": {"ok": p3_ok, **p3_detail},
            "anomaly": anomaly_details,
            "analysis_error": analysis_error,
            "missing_peak_arms": missing_peaks,
        },
        "coherence": {
            "note": "MÁSODLAGOS ág (terv 3.2) — a fő ítéletbe NEM számít bele",
            "D": {arm: D_coh[arm].tolist() for arm in config.ARM_NAMES},
            "metrics": point_coh,
            "bootstrap_t_ci99": {
                arm: _ci(boot_coh_t[arm], q, 1 - q) for arm in config.ARM_NAMES
            },
        },
        "verdict": verdict,
        "verdict_reason": verdict_reason,
    }


# ---------------------------------------------------------------------------
# Jelentés (Hungarian szöveg)
# ---------------------------------------------------------------------------
def _fmt(x, nd=4):
    return "—" if x is None else f"{x:.{nd}f}"


def format_report(results: dict, frozen_hash: str, dataset_label: str) -> str:
    lines = []
    lines.append("=" * 72)
    lines.append("triangle-anchor-memory — elemzés (D(k), bootstrap, preregisztrált ítélet)")
    lines.append(f"adatforrás: {dataset_label}")
    lines.append(f"frozen_params_v1.4.json SHA-256: {frozen_hash}")
    lines.append("=" * 72)

    pop = results["population"]
    lines.append("")
    lines.append("POPULÁCIÓS ÁG (fő) — kar / t_vissza [99% CI] / A_vissza [99% CI] / BLP / D(0) / csúcs")
    for arm in config.ARM_NAMES:
        m = pop["metrics"][arm]
        ci = pop["bootstrap_ci99"][arm]
        t = _fmt(m["t_vissza"], 0)
        peak = "igen" if m.get("peak_found") else "NEM"
        ci_a = ci["A_vissza_ci99"]
        lo_a = "-inf" if np.isneginf(ci_a[0]) else _fmt(ci_a[0])
        hi_a = "-inf" if np.isneginf(ci_a[1]) else _fmt(ci_a[1])
        lines.append(
            f"  {arm:>5}: t = {t:>2} [{_fmt(ci['t_vissza_ci99'][0],2)}, {_fmt(ci['t_vissza_ci99'][1],2)}]"
            f"   A = {_fmt(m['A_vissza'])} [{lo_a}, {hi_a}]"
            f"   BLP = {_fmt(m['BLP'])}   D0 = {_fmt(m['D0'])}   csúcs: {peak} (peakless bootstrap: {ci.get('n_peakless_bootstrap', 0)}/2000)"
        )

    p1 = pop["P1"]
    lines.append("")
    lines.append("P1 — t_vissza arányok 1 : 0.71 : 0.58 (±20%):")
    for arm in ("n1", "n2", "n3"):
        d = p1["details"][arm]
        lines.append(
            f"  {arm}: t = {_fmt(d['t_vissza'], 0)}, arány n1-hez = {_fmt(d['ratio_vs_n1'])}"
            f" (elvárt {d['expected_ratio']}) → {'OK' if d['ok'] else 'NEM OK'}"
        )
    lines.append(f"  P1 összességében: {'TELJESÜL' if p1['ok'] else 'NEM TELJESÜL'}")

    p2 = pop["P2"]
    ci2 = p2.get("ci99_diff")
    ci2_s = "—" if ci2 is None else f"[{ci2[0]:.4f}, {ci2[1]:.4f}]"
    lines.append("")
    lines.append(
        "P2 — A_vissza(n3) ≥ A_vissza(n1) az n3 első csúcsánál:"
        f" k3* = {p2.get('k3_star')}, CI(n3−n1) = {ci2_s} → {'TELJESÜL' if p2['ok'] else 'NEM TELJESÜL'}"
    )

    p3 = pop["P3"]
    lines.append("")
    lines.append(
        f"P3 — cut vs n3: shift = {_fmt(p3.get('shift_steps'), 0)} lépés"
        f" CI = [{p3['shift_ci99'][0]:.2f}, {p3['shift_ci99'][1]:.2f}] → {'OK' if p3['shift_ok'] else 'nem'};"
        f"  magasság-CI(A_cut−0.8·A_n3) = [{p3['height_margin_ci99'][0]:.4f}, {p3['height_margin_ci99'][1]:.4f}]"
        f" → {'OK' if p3['height_ok'] else 'nem'}"
        f"  ⇒ P3: {'TELJESÜL' if p3['ok'] else 'NEM TELJESÜL'}"
    )

    lines.append("")
    lines.append("Anomália-ellenőrzés (zajtalan unitér maximum, populációs ág):")
    for arm in config.ARM_NAMES:
        a = pop["anomaly"][arm]
        if a.get("checked"):
            flag = "ANOMÁLIA!" if a["anomaly"] else "ok"
            lo = a["ci99_lo"]
            lo_s = "-inf" if np.isneginf(lo) else f"{lo:.4f}"
            lines.append(
                f"  {arm:>5}: határ = {a['bound']:.4f}, CI alsó = {lo_s} → {flag}"
                f"   (csúcs: {'igen' if a.get('peak_found') else 'NEM'},"
                f" peakless bootstrap minta: {a.get('n_peakless_bootstrap', 0)}/2000)"
            )
        else:
            lines.append(f"  {arm:>5}: nincs ellenőrizve ({a.get('reason')})")

    lines.append("")
    coh = results["coherence"]
    lines.append(f"KOHERENCIA-ÁG (MÁSODLAGOS) — {coh['note']}")
    for arm in config.ARM_NAMES:
        m = coh["metrics"][arm]
        t = _fmt(m["t_vissza"], 0)
        lines.append(
            f"  {arm:>5}: t = {t:>2}   A = {_fmt(m['A_vissza'])}   BLP = {_fmt(m['BLP'])}   D0 = {_fmt(m['D0'])}"
        )

    lines.append("")
    lines.append("=" * 72)
    lines.append(f"ÍTÉLET (populációs ág, preregisztrált szabály): {results['verdict']}")
    lines.append(f"indoklás: {results['verdict_reason']}")
    lines.append("=" * 72)
    return "\n".join(lines)


def load_raw_counts(path: Path = RAW_COUNTS_PATH) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    try:
        frozen, frozen_hash = load_frozen_params()
    except RuntimeError as exc:
        print(f"HIBA: {exc}")
        return 2
    if not RAW_COUNTS_PATH.exists():
        print(
            "NINCS raw_counts.json a data/ mappában — a QPU-futtatás (1. fázis) még\n"
            "nem történt meg, vagy a Control Agent nem mentette el az adatokat.\n"
            "A 0. fázis száraz futásához használd a dryrun.py-t."
        )
        return 1
    dataset = load_raw_counts()
    try:
        results = analyze_dataset(dataset, frozen)
    except FloatingPointError as exc:
        print(f"ELEMZO-HIBA / ERVENYTELEN (fail-closed, np.errstate(all='raise')): {exc}")
        return 3
    print(format_report(results, frozen_hash, str(RAW_COUNTS_PATH)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
