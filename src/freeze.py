"""0. fázis — paraméter-fagyasztás (QPU-beküldés ELŐTT, EGYSZER fut le).

Feladata (a feladat 3. lépése): a szimuláció alapján rögzíti
  - φ (részleges SWAP szög), K (lépésszám),
  - a csúcs-keresési ablakok ARMONKÉNT,
  - a várt görbéket (zajtalan, pontos, k = 0..K) a populációs és a
    koherencia-ágban (a koherencia-ág MÁSODLAGOS),
  - az ANOMÁLIA-referenciát (a teljesen unitér, zajtalan görbe maximuma),
  - bootstrap/CI/toleranciákat a terv 4. fejezetéből, változtatás nélkül.

Kötés: preregistration/frozen_params.json — EGYSZER hozható létre; ha már
létezik, a szkript LEÁLL (a fagyasztott fájl utólag nem módosítható; a
módosítás csak verziószámozott, „amended" kiegészítéssel lehetséges).

A létrehozott fájlt SHA-256-mal zárjuk: a hash a
preregistration/frozen_params.sha256 fájlba kerül (a PLAN_v1.0.md hashével együtt);
integrity: src/analysis.py:verify_frozen_params.

FIGYELEM (2026-11-12, v1.2 AMENDED): ez a szkript a v1.0 fagyasztó — NEM
újrafuttatható a v1.2 döntési paramétereinek előállítására; a jelenleg irányadó,
99% CI + Holm-ot tartalmazó fagyasztott fájl a frozen_params_v1.2.json
(PLAN_v1.2.md AMENDED; a módosítás a döntési szabályt érintette, nem a várt
görbéket — a szimuláció-alapú cellák változatlanok). A v1.0 fájlok byte-ra
változatlanok; új fagyasztás csak verziószámozott, „amended” kiegészítéssel,
külön committal lehetséges.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import config
from .analysis import sha256_file, find_return_peak
from .sim import exact_D_curves, sweep_exact

REPO_ROOT = Path(__file__).resolve().parents[1]
FROZEN_PATH = REPO_ROOT / "preregistration" / "frozen_params.json"
SHA_PATH = REPO_ROOT / "preregistration" / "frozen_params.sha256"
PLAN_PATH = REPO_ROOT / "preregistration" / "PLAN_v1.0.md"

# A 0. fázis szimulációja alapján (zajtalan, pontos) KIJELÖLT ablakok.
# Indoklás (zajtalan első visszatérési csúcsok: n1→16, n2→11, n3→9, cut→11):
#   n1:  [4, 19]  (első csúcs 16; a 2. visszatérés ~32, kívül esik)
#   n2:  [3, 14]  (első csúcs 11; a 2. visszatérés ~23, kívül esik)
#   n3:  [3, 12]  (első csúcs 9;  a 2. visszatérés ~19, kívül esik)
#   cut: [3, 14]  (a cut az n2-vel azonos effektív szabadsági fokú; első csúcs 11)
#   noisy:[6, 12] (kontrollkar — a háromszög-idejű első visszatérés körzete)
#   n0:  null     (alapvonal: nincs visszatérési csúcs — csúcskeresés NINCS)
# Az ablakok a populációs ÉS a koherencia-ágra egységesen értendők
# (a két ág csúcsai a zajtalan szimulációban egyeznek).
WINDOWS = {"n0": None, "n1": [4, 19], "n2": [3, 14], "n3": [3, 12], "cut": [3, 14], "noisy": [6, 12]}
EXPECTED_T = {"n1": 16, "n2": 11, "n3": 9, "cut": 11}


def main() -> int:
    if FROZEN_PATH.exists():
        print(
            f"LEÁLL: {FROZEN_PATH} már létezik.\n"
            "A fagyasztott paraméterfájl utólag NEM módosítható (a feladat 3. lépése).\n"
            "Módosítás csak verziószámozott, „amended” megjelölésű kiegészítéssel lehetséges."
        )
        return 1

    print("0. fázis — zajtalan, pontos szimuláció (statevector), k = 0..K minden karra...")
    exact = sweep_exact(snapshot=None)
    curves = exact_D_curves(exact)

    dip_frac = float(config.DECISION_REFERENCE["dip_frac"])
    # Csúcsok a kijelölt ablakokban — konzisztencia-ellenőrzés a befagyasztás előtt
    found = {}
    for arm in config.ARM_NAMES:
        d = curves[arm]["population"]
        w = WINDOWS[arm]
        window = (w[0], w[1]) if w else None
        t, peak = find_return_peak(d, window, dip_frac)
        found[arm] = t
        print(f"  {arm:>5}: D0={d[0]:.4f}, első csúcs t={t}")
    for arm, exp in EXPECTED_T.items():
        if found[arm] != exp:
            print(
                f"LEÁLL: {arm} első csúcsa t={found[arm]}, a várt {exp} lenne.\n"
                "Ne erőltesd az ablakot vagy a jóslatot — vizsgáld ki és jelentsd."
            )
            return 1

    import numpy as np

    def metrics_block(arm: str) -> dict:
        d = curves[arm]["population"]
        d_c = curves[arm]["coherence"]
        w = WINDOWS[arm]
        window = (w[0], w[1]) if w else None
        t_pop, peak_pop = find_return_peak(d, window, dip_frac)
        t_coh, peak_coh = find_return_peak(d_c, window, dip_frac)
        return {
            "population": {
                "t_vissza": t_pop,
                "A_vissza": (peak_pop / d[0]) if peak_pop is not None else None,
                "BLP": float(np.sum(np.maximum(0.0, np.diff(d)))),
            },
            "coherence": {
                "t_vissza": t_coh,
                "A_vissza": (peak_coh / d_c[0]) if peak_coh is not None else None,
                "BLP": float(np.sum(np.maximum(0.0, np.diff(d_c)))),
            },
        }

    expected_metrics = {arm: metrics_block(arm) for arm in config.ARM_NAMES}

    # ANOMÁLIA-referencia: a teljesen unitér, zajtalan szimuláció által megengedett
    # maximális normált visszatérés (max_k D_exact(k)/D_exact(0)) a populációs ágban.
    anomaly_population = {
        arm: float(max(curves[arm]["population"]) / curves[arm]["population"][0])
        for arm in config.ARM_NAMES
    }

    frozen = {
        "schema": "triangle-anchor-memory/frozen_params@1",
        "version": "1.0",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": (
            "QPU-beküldés ELŐTT rögzítve (a terv 4. fejezetének megfelelően). "
            "Ez a fájl a döntési szabály forrása; integritását a frozen_params.sha256 védi. "
            "Módosítás csak verziószámozott, „amended” kiegészítéssel lehetséges."
        ),
        "phi": config.PHI,
        "phi_exact": "pi/16",
        "K": config.K,
        "shots_phase0": config.SHOTS,
        "windows": WINDOWS,
        "windows_note": (
            "Keresési ablakok (k-lépés indexek, inkluzív) a zajtalan szimuláció első visszatérési "
            "csúcsai köré, a 2. visszatérés kizárásával; n0 alapvonal — nincs csúcskeresés; "
            "noisy kontrollkar — csak az első (háromszög-idejű) visszatérés ablakja. Az ablakok "
            "a populációs és a koherencia-ágra egyaránt értendők."
        ),
        "t_vissza_expected": EXPECTED_T,
        "tolerances": {
            "p1_expected_ratios": {"n1": 1.0, "n2": 0.71, "n3": 0.58},
            "p1_ratio_tol_rel": 0.20,
            "ci_level": 0.95,
            "p2_require_ci_lower_ge_0": True,
            "p3_height_rel": 0.20,
            "p3_shift_min_steps": 2,
            "dip_frac": 0.95,
        },
        "bootstrap": {
            "resamples": config.BOOTSTRAP_N,
            "seed": config.BOOTSTRAP_SEED,
            "method": "marginal_binomial_of_multinomial",
            "ci_level": 0.95,
        },
        "expected_curves": {
            branch: {
                arm: [float(v) for v in curves[arm][branch]]
                for arm in config.ARM_NAMES
            }
            for branch in ("population", "coherence")
        },
        "expected_metrics": expected_metrics,
        "anomaly_reference": {
            "population": anomaly_population,
            "note": (
                "A teljesen unitér, zajtalan szimuláció által megengedett maximális normált "
                "visszatérés (max_k D_exact(k)/D_exact(0)) a populációs ágban. A koherencia-ág "
                "nem része az anomália-ítéletnek (terv 3.2)."
            ),
        },
        "positive_control": {
            "coupling_scale": 0.0,
            "description": "csatolások kikapcsolva (minden PSWAP helyén kitöltő 'id' marad)",
            "expected_verdict": "NULL",
        },
        "noise_model_note": (
            "A zajos paraméterek a 0. fázisban MINTAÉRTÉKEK (config.SNAPSHOT_SAMPLE); "
            "a zajmodell sémája a config.SNAPSHOT_SCHEMA_DOC-ban rögzített, így a leendő "
            "chip-pillanatkép (snapshot.json) egy az egyben behelyettesíthető. "
            "A zajtalan várt görbék a befagyasztás alapját képezik."
        ),
        "history": [],
    }

    FROZEN_PATH.write_text(json.dumps(frozen, ensure_ascii=False, indent=2), encoding="utf-8")

    frozen_hash = sha256_file(FROZEN_PATH)
    plan_hash = sha256_file(PLAN_PATH)
    SHA_PATH.write_text(
        "# triangle-anchor-memory — preregisztrált hashek\n"
        f"# létrehozva (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
        "# integritás-ellenőrzés: src/analysis.py:verify_frozen_params\n"
        "# (A döntési szabály forrása a frozen_params.json — módosítás csak 'amended' verzióval!)\n"
        f"{frozen_hash}  frozen_params.json\n"
        f"{plan_hash}  PLAN_v1.0.md\n",
        encoding="utf-8",
    )

    print("")
    print(f"frozen_params.json írva: {FROZEN_PATH}")
    print(f"  SHA-256: {frozen_hash}")
    print(f"  PLAN_v1.0.md SHA-256: {plan_hash}")
    print(f"  hash-fájl: {SHA_PATH}")
    print("A fájl később NEM módosítható; a dryrun és az elemzés integritást ellenőriz.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
