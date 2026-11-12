#!/usr/bin/env python3
"""dryrun.py — QPU NÉLKÜL mindent végigfuttat (0. fázis, Csillag v1.3).

A feladat 5. lépése (agent_feladat_csillag_v13.txt). Lépések:
  0. frozen_params_v1.3.json integritás-ellenőrzés (hash a preregistration/ mappában;
     v1.3 AMENDED: 99% CI + Holm; a file_hashes visszaellenőrzi az elemző és a
     dryrun tényleges sha256-ját a fagyasztott fájl ellen — fail-closed);
  1. ZAJTALAN szimuláció (Aer, lövés-zaj, seedelt, karhosszal kiegyenlített
     áramkörökön) minden karra — az elvárt preregisztrált ítélet: TEXTBOOK-MEGEROSITVE;
  2. ZAJOS szimuláció MINTA paraméterekkel (config.SNAPSHOT_SAMPLE) — NEM
     chip-pillanatkép, NEM hardver; az eredményt őszintén, címkézve írjuk ki;
  3. POZITÍV KONTROLL: csatolások kikapcsolva (coupling_scale = 0.0). A v1.3
     fail-closed szabálya szerint a zajtalan kontroll D(k) ≡ konstans, nincs
     dip, nincs csúcs → a pontbecslés NaN a csúcsot váró karokon → az ítélet
     ``ELEMZO-HIBA / ERVENYTELEN`` (vagy, ha a lövés-zaj véletlen csúcsot ad:
     NULL). A kapu: az ítélet NEM lehet TEXTBOOK és NEM lehet ANOMALIA.
     (v1.2-ben NULL volt el/várva; a fail-closed szabály ezt a kontrollt is
     átminősíti — lásd PLAN_v1.3.md / a jelentésben külön jelezve Maya felé.)
  3b. KARHOSSZ-KAPU (v1.3 4. pont, KÖTELEZŐ PASS-pont): minden kar (6), minden
     (branch, init) csoport (3) és k = 0..32, coupling_scale = 1.0 ÉS 0.0:
     transpile + ALAP után |hossz(arm) − cél| ≤ 1 dt (cél = az n3 kar hossza;
     kivétel: population/init="0", ahol a noisy kar horgony-H szintézise 8 dt-vel
     hosszabb az n3-nál — ott a cél a noisy hossza; dokumentálva). Ha BÁRMELY
     sor > 1 dt: ÁLLJ MEG — kilépési kód 3.
  4. REPLAY (v1.3 5. pont): ≥ 600 null (coupling_scale = 0.0) ÉS ≥ 600 tankönyvi
     újrajátszás (coupling_scale = 1.0), FakeKingston-routolt Aer-valószínűségekből
     (src/kingston_routing.py: transpile+ALAP → 4-qubitos helyi áramkör →
     FakeKingston-kalibrációs zajmodell → density_matrix → analitikus
     kiolvasási-hiba-vetítés), 4096 lövéssel (binomiális szintézés).
     KÖVETELMÉNY: hamis ANOMALIA ≤ 1% (≤ 6/600) ÉS hamis TEXTBOOK ≤ 1% (≤ 6/600)
     a null-replayen. Regressziós seedek kötelezően: 9003, 9022, 9117, 9156,
     9189, 9244, 9489, 9574 — ezekből BÁRMELYIK ANOMALIA vagy TEXTBOOK: ÁLLJ MEG.
     Ha bármely követelmény nem teljesül: NE lazítsd a küszöböt — ÁLLJ MEG és jelentsd.
  5. Összesítés. Kilépési kódok: 0 = minden kapu teljesül; 1 = egy vagy több
     kapu bukott; 2 = a fagyasztott paraméterfájl integritása érvénytelen;
     3 = a karhossz-kapu bukott.

FONTOS: ez a szkript NEM ír a data/ mappába (a raw_counts.json a QPU-futtatás
1. fázisának kimenete, sosem származhat szimulációból), és semmilyen IBM-ellenes
vagy hálózati hívást nem tartalmaz. Minden eredmény SZIMULÁCIÓ — sosem HARDWARE.
"""
from __future__ import annotations

import sys
import time
from collections import Counter

import numpy as np

from src import analysis, config, kingston_routing, sim

N_REPLAYS = 600
REPLAY_TEXTBOOK_SEED_BASE = 20261000
REPLAY_NULL_SEED_BASE = 20262000
REGRESSION_SEEDS = (9003, 9022, 9117, 9156, 9189, 9244, 9489, 9574)
MAX_FALSE = 6  # ≤ 1% of 600
DURATION_GATE_DT = 1


def synth_dataset(exact_curves: dict, coupling_scale: float, seed: int, shots: int = config.SHOTS) -> dict:
    """Binomiális újrajátszás a (routed) pontos valószínűségekből — v1.2-minta."""
    r = np.random.default_rng(seed)
    ds = {
        "population": {arm: {i: {} for i in config.POP_INITS} for arm in config.ARM_NAMES},
        "coherence": {arm: {config.COH_INIT: {}} for arm in config.ARM_NAMES},
        "shots": shots,
        "seed": int(seed),
        "coupling_scale": float(coupling_scale),
        "is_sample_noise": False,
    }
    for arm in config.ARM_NAMES:
        for k in range(config.K + 1):
            for init in config.POP_INITS:
                p1 = float(exact_curves[arm]["population"][init][k]["p1"])
                o = int(r.binomial(shots, np.clip(p1, 0.0, 1.0)))
                ds["population"][arm][init][str(k)] = {"0": shots - o, "1": o}
            pc0 = float(exact_curves[arm]["coherence"][config.COH_INIT][k]["p0"])
            z = int(r.binomial(shots, np.clip(pc0, 0.0, 1.0)))
            ds["coherence"][arm][config.COH_INIT][str(k)] = {"0": z, "1": shots - z}
    return ds


def _verdict_counts(verdicts: list[str]) -> Counter:
    return Counter(verdicts)


def main() -> int:
    t_start = time.time()
    print("=" * 72)
    print("triangle-anchor-memory — DRY RUN (QPU nélkül, 0. fázis, Csillag v1.3)")
    print("=" * 72)

    # --- 0. lépés: a befagyasztott paraméterfájl integritása ---
    try:
        frozen, frozen_hash = analysis.load_frozen_params()
    except RuntimeError as exc:
        print(f"\nHIBA a befagyasztott paraméterfájl ellenőrzésekor:\n{exc}")
        print("ÁLLJ MEG ÉS JELENTSD — a döntési szabály forrása érvénytelen.")
        return 2
    print(f"\n[0/5] Integritás OK — frozen_params_v1.3.json SHA-256: {frozen_hash}")
    print(f"      φ = π/16 ({frozen['phi']:.6f} rad), K = {frozen['K']}, "
          f"bootstrap = {frozen['bootstrap']['resamples']}× (seed {frozen['bootstrap']['seed']})")
    print(f"      version = {frozen['version']}, correction = {frozen['correction']}, "
          f"claim_family = {frozen['claim_family']}, ci_level = {frozen['bootstrap']['ci_level']}")
    for rel, h in sorted(frozen.get("file_hashes", {}).items()):
        print(f"      file_hashes[{rel}] = {h}")

    # --- 1. lépés: ZAJTALAN szimuláció → elvárt ítélet: TEXTBOOK-MEGEROSITVE ---
    print("\n[1/5] Zajtalan szimuláció minden karra (Aer qasm, lövés-zaj, karhosszal")
    print(f"      kiegyenlített áramkörökön, shots={config.SHOTS}, seed={config.SEED})...")
    t0 = time.time()
    ds_ideal = sim.sweep_counts(snapshot=None, coupling_scale=1.0, shots=config.SHOTS, seed=config.SEED)
    try:
        res_ideal = analysis.analyze_dataset(ds_ideal, frozen)
    except FloatingPointError as exc:
        print(f"ELEMZO-HIBA / ERVENYTELEN (fail-closed) a zajtalan ágon: {exc}")
        print("ÁLLJ MEG ÉS JELENTSD.")
        return 1
    print(analysis.format_report(
        res_ideal, frozen_hash,
        f"zajtalan szimuláció (Aer, lövés-zaj; {time.time() - t0:.1f} s)",
    ))

    # --- 2. lépés: ZAJOS szimuláció MINTA paraméterekkel (nem hardver!) ---
    print("\n[2/5] Zajos szimuláció — MINTA T1/T2/ε paraméterekkel "
          "(config.SNAPSHOT_SAMPLE, NEM chip-pillanatkép, NEM hardver)...")
    t0 = time.time()
    snapshot = sim.load_noise_snapshot(None)
    assert snapshot.get("is_sample") is True, "a mintának is_sample=True-nak kell lennie"
    print(f"      forrás: {snapshot['source']}")
    ds_noisy = sim.sweep_counts(snapshot=snapshot, coupling_scale=1.0, shots=config.SHOTS, seed=config.SEED)
    try:
        res_noisy = analysis.analyze_dataset(ds_noisy, frozen)
        noisy_label = f"zajos szimuláció, MINTA paraméterek ({time.time() - t0:.1f} s) — NEM hardver-eredmény"
    except FloatingPointError as exc:
        res_noisy = None
        noisy_label = f"ELEMZO-HIBA / ERVENYTELEN (fail-closed): {exc} — referenciaként közöljük"
    if res_noisy is not None:
        print(analysis.format_report(res_noisy, frozen_hash, noisy_label))
    else:
        print(noisy_label)

    # --- 3. lépés: POZITÍV KONTROLL — csatolások kikapcsolva ---
    print("\n[3/5] Pozitív kontroll: csatolások KIKAPCSOLVA (coupling_scale = 0.0)...")
    t0 = time.time()
    ds_broken = sim.sweep_counts(snapshot=None, coupling_scale=0.0, shots=config.SHOTS, seed=config.SEED)
    try:
        res_broken = analysis.analyze_dataset(ds_broken, frozen)
    except FloatingPointError as exc:
        res_broken = {"verdict": analysis.VERDICT_ANALYSIS_ERROR, "verdict_reason": str(exc)}
    print(analysis.format_report(
        res_broken, frozen_hash,
        f"POZITÍV KONTROLL (φ=0), {time.time() - t0:.1f} s — ennek NEM SZABAD TEXTBOOK vagy ANOMALIA lennie",
    ) if res_broken.get("population") else f"  ítélet: {res_broken['verdict']} ({res_broken.get('verdict_reason')})")

    # --- 3b. lépés: KARHOSSZ-KAPU (kötelező PASS-pont) ---
    print("\n[3b/5] Karhossz-kapu: transpile + ALAP |hossz(arm) − cél| ≤ 1 dt "
          "minden karra, csoportra, k-ra (scale = 1.0 és 0.0)...")
    t0 = time.time()
    try:
        rows, max_abs = kingston_routing.equalization_report(range(config.K + 1))
    except RuntimeError as exc:
        print(f"KARHOSSZ-KAPU HIBA (fail-closed): {exc}")
        print("ÁLLJ MEG ÉS JELENTSD — a kiegyenlítés nem teljesül.")
        return 3
    n_exact = sum(1 for r in rows if r["delta_dt"] == 0)
    n_over_n3 = max(abs(r["delta_vs_n3_dt"]) for r in rows)
    worst = sorted(rows, key=lambda r: -abs(r["delta_dt"]))[:5]
    print(f"      sorok: {len(rows)}, |Δ|≤1 dt: {sum(1 for r in rows if abs(r['delta_dt']) <= DURATION_GATE_DT)}/{len(rows)}, "
          f"max |Δ| = {max_abs} dt, pontosan 0 dt: {n_exact}/{len(rows)}  ({time.time() - t0:.1f} s)")
    print(f"      (diagnosztika: max |hossz − n3| = {n_over_n3} dt — a population/init=0 csoportban a")
    print("       noisy kar horgony-H szintézise 8 dt-vel hosszabb az n3-nál; ott a cél a noisy hossza)")
    for r in worst:
        if abs(r["delta_dt"]) > 0:
            print(f"      legrosszabb: k={r['k']} {r['branch']}/{r['init']} {r['arm']} scale={r['coupling_scale']} "
                  f"target={r['target_dt']} arm={r['arm_dt']} Δ={r['delta_dt']:+d}")
    ok_duration = max_abs <= DURATION_GATE_DT

    # --- 4. lépés: REPLAY — FakeKingston-routolt Aer-valószínűségek ---
    print(f"\n[4/5] Replay: {N_REPLAYS} null (coupling_scale = 0.0) + {N_REPLAYS} tankönyvi "
          f"újrajátszás (coupling_scale = 1.0),")
    print(f"      FakeKingston-routolt Aer-valószínűségekből, {config.SHOTS} lövéssel "
          f"(binomiális szintézés)...")
    t0 = time.time()
    print("      routed valószínűségek számolása (φ = 1.0 és φ = 0.0)...")
    exact_textbook = kingston_routing.sweep_routed_probabilities(1.0, range(config.K + 1))
    exact_zero = kingston_routing.sweep_routed_probabilities(0.0, range(config.K + 1))
    print(f"      kész ({time.time() - t0:.1f} s); replay-szintézés és elemzés fut...")

    t0 = time.time()
    verdicts_null: list[str] = []
    for i in range(N_REPLAYS):
        ds_r = synth_dataset(exact_zero, 0.0, REPLAY_NULL_SEED_BASE + i)
        try:
            verdicts_null.append(analysis.analyze_dataset(ds_r, frozen)["verdict"])
        except FloatingPointError:
            verdicts_null.append(analysis.VERDICT_ANALYSIS_ERROR)
        if (i + 1) % 100 == 0:
            print(f"      null-replay: {i + 1}/{N_REPLAYS} ({time.time() - t0:.1f} s)")
    t_null = time.time() - t0

    t0 = time.time()
    verdicts_textbook: list[str] = []
    for i in range(N_REPLAYS):
        ds_r = synth_dataset(exact_textbook, 1.0, REPLAY_TEXTBOOK_SEED_BASE + i)
        try:
            verdicts_textbook.append(analysis.analyze_dataset(ds_r, frozen)["verdict"])
        except FloatingPointError:
            verdicts_textbook.append(analysis.VERDICT_ANALYSIS_ERROR)
        if (i + 1) % 100 == 0:
            print(f"      tankönyvi replay: {i + 1}/{N_REPLAYS} ({time.time() - t0:.1f} s)")
    t_textbook = time.time() - t0

    vn = _verdict_counts(verdicts_null)
    vt = _verdict_counts(verdicts_textbook)
    n_anom_null = vn.get(analysis.VERDICT_ANOMALIA, 0)
    n_textbook_null = vn.get(analysis.VERDICT_TEXTBOOK, 0)
    n_anom_textbook = vt.get(analysis.VERDICT_ANOMALIA, 0)
    ok_probe_null_anom = n_anom_null <= MAX_FALSE
    ok_probe_null_textbook = n_textbook_null <= MAX_FALSE
    ok_probe_textbook_anom = n_anom_textbook <= MAX_FALSE

    print(f"  tankönyvi replay (600): {dict(vt)}")
    print(f"      hamis ANOMALIA a tankönyvi replayen: {n_anom_textbook}/600 "
          f"(referenciaként közöljük; kapu: csak a null-oldalon él)")
    print(f"  φ=0 replay       (600): {dict(vn)} → hamis ANOMALIA: {n_anom_null}/600 "
          f"(elvárt ≤ {MAX_FALSE}/600, 1%) {'OK' if ok_probe_null_anom else 'NEM OK!'}")
    print(f"                            hamis TEXTBOOK:  {n_textbook_null}/600 "
          f"(elvárt ≤ {MAX_FALSE}/600, 1%) {'OK' if ok_probe_null_textbook else 'NEM OK!'}")

    # Regressziós seedek (a v1.2-ben hamis ANOMALIÁT ado 8 eset) — külön ellenőrzés
    print("  regressziós seedek (null-replay, kötelezően ellenőrzött):")
    regression_rows = []
    for seed in REGRESSION_SEEDS:
        ds_r = synth_dataset(exact_zero, 0.0, seed)
        try:
            verdict = analysis.analyze_dataset(ds_r, frozen)["verdict"]
        except FloatingPointError:
            verdict = analysis.VERDICT_ANALYSIS_ERROR
        ok = verdict not in (analysis.VERDICT_ANOMALIA, analysis.VERDICT_TEXTBOOK)
        regression_rows.append((seed, verdict, ok))
        print(f"    seed {seed}: {verdict} {'OK' if ok else 'NEM OK — hamis ANOMALIA/TEXTBOOK!'}")
    ok_regression = all(ok for _, _, ok in regression_rows)
    print(f"  (replay futásidők: null {t_null:.1f} s, tankönyvi {t_textbook:.1f} s; "
          f"minden eredmény szimuláció — NEM hardver)")

    # --- 5. lépés: összesítés és kilépési kód ---
    print("\n[5/5] Összesítés")
    v_ideal = res_ideal["verdict"]
    v_control = res_broken["verdict"]
    ok_ideal = v_ideal == analysis.VERDICT_TEXTBOOK
    ok_control = v_control not in (analysis.VERDICT_TEXTBOOK, analysis.VERDICT_ANOMALIA)
    print(f"  zajtalan szimuláció     → {v_ideal:<28} (elvárt: TEXTBOOK-MEGEROSITVE) {'OK' if ok_ideal else 'NEM OK!'}")
    print(f"  pozitív kontroll (φ=0)  → {v_control:<28} (elvárt: nem TEXTBOOK és nem ANOMALIA) {'OK' if ok_control else 'NEM OK!'}")
    print(f"  zajos (MINTA) eredmény  → {res_noisy['verdict'] if res_noisy else 'ELEMZO-HIBA / ERVENYTELEN':<28} (referenciaként közöljük; NEM hardver)")
    print(f"  karhossz-kapu           → max |Δ| = {max_abs} dt (elvárt ≤ {DURATION_GATE_DT} dt) {'OK' if ok_duration else 'NEM OK!'}")
    print(f"  replay null oldalon     → hamis ANOMALIA {n_anom_null}/600, hamis TEXTBOOK {n_textbook_null}/600 {'OK' if (ok_probe_null_anom and ok_probe_null_textbook) else 'NEM OK!'}")
    print(f"  regressziós seedek      → {'8/8 OK' if ok_regression else 'BUKOTT — lásd fent'}")
    print(f"\n  teljes futásidő: {time.time() - t_start:.1f} s")

    if not ok_duration:
        print("\nDRY RUN NEM OK — a karhossz-kapu bukott. ÁLLJ MEG ÉS JELENTSD.")
        return 3
    if not ok_ideal:
        print("\nDRY RUN NEM OK — a zajtalan szimuláció nem TEXTBOOK. ÁLLJ MEG ÉS JELENTSD.")
        return 1
    if not ok_control:
        print("\nDRY RUN NEM OK — a pozitív kontroll TEXTBOOK vagy ANOMALIA! ÁLLJ MEG ÉS JELENTSD.")
        return 1
    if not (ok_probe_null_anom and ok_probe_null_textbook and ok_probe_textbook_anom and ok_regression):
        print("\nDRY RUN NEM OK — a replay-követelmények nem teljesültek.")
        print("ÁLLJ MEG ÉS JELENTSD — NE lazíts a küszöbön (feladat 5. pontja).")
        return 1
    print("\nDRY RUN OK — a száraz futás teljesíti a feladat 4-5. pontjának elvárásait (v1.3, 99% CI + Holm).")
    print("A QPU-futtatás NINCS elindítva; azt a Control Agent végzi, külön tulajdonosi döntéssel.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
