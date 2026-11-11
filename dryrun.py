#!/usr/bin/env python3
"""dryrun.py — QPU NÉLKÜL mindent végigfuttat (0. fázis).

A feladat 4. lépése. Lépések:
  0. frozen_params.json integritás-ellenőrzés (hash a preregistration/ mappában);
  1. ZAJTALAN szimuláció (Aer, lövés-zaj, seedelt) minden karra — az elvárt
     preregisztrált ítélet: TEXTBOOK-MEGEROSITVE;
  2. ZAJOS szimuláció MINTA paraméterekkel (config.SNAPSHOT_SAMPLE) — NEM
     chip-pillanatkép, NEM hardver; az eredményt őszintén, címkézve írjuk ki;
  3. POZITÍV KONTROLL: csatolások kikapcsolva (coupling_scale = 0.0) — az
     elemzőnek NULL ítéletet KELL adnia;
  4. Összesítés. Kilépési kód: 0, ha (1) TEXTBOOK-MEGEROSITVE ÉS (3) NULL;
     egyébként 1, és a szkript üzenete: ÁLLJ MEG ÉS JELENTSD.

FONTOS: ez a szkript NEM ír a data/ mappába (a raw_counts.json a QPU-futtatás
1. fázisának kimenete, sosem származhat szimulációból), és semmilyen IBM-ellenes
vagy hálózati hívást nem tartalmaz.
"""
from __future__ import annotations

import sys
import time

from src import analysis, config, sim


def main() -> int:
    t_start = time.time()
    print("=" * 72)
    print("triangle-anchor-memory — DRY RUN (QPU nélkül, 0. fázis)")
    print("=" * 72)

    # --- 0. lépés: a befagyasztott paraméterfájl integritása ---
    try:
        frozen, frozen_hash = analysis.load_frozen_params()
    except RuntimeError as exc:
        print(f"\nHIBA a befagyasztott paraméterfájl ellenőrzésekor:\n{exc}")
        print("ÁLLJ MEG ÉS JELENTSD — a döntési szabály forrása érvénytelen.")
        return 2
    print(f"\n[0/4] Integritás OK — frozen_params.json SHA-256: {frozen_hash}")
    print(f"      φ = π/16 ({frozen['phi']:.6f} rad), K = {frozen['K']}, "
          f"bootstrap = {frozen['bootstrap']['resamples']}× (seed {frozen['bootstrap']['seed']})")

    # --- 1. lépés: ZAJTALAN szimuláció → elvárt ítélet: TEXTBOOK-MEGEROSITVE ---
    print("\n[1/4] Zajtalan szimuláció minden karra (Aer qasm, lövés-zaj, "
          f"shots={config.SHOTS}, seed={config.SEED})...")
    t0 = time.time()
    ds_ideal = sim.sweep_counts(snapshot=None, coupling_scale=1.0, shots=config.SHOTS, seed=config.SEED)
    res_ideal = analysis.analyze_dataset(ds_ideal, frozen)
    print(analysis.format_report(
        res_ideal, frozen_hash,
        f"zajtalan szimuláció (Aer, lövés-zaj; {time.time() - t0:.1f} s)",
    ))

    # --- 2. lépés: ZAJOS szimuláció MINTA paraméterekkel (nem hardver!) ---
    print("\n[2/4] Zajos szimuláció — MINTA T1/T2/ε paraméterekkel "
          "(config.SNAPSHOT_SAMPLE, NEM chip-pillanatkép, NEM hardver)...")
    t0 = time.time()
    snapshot = sim.load_noise_snapshot(None)
    assert snapshot.get("is_sample") is True, "a mintának is_sample=True-nak kell lennie"
    print(f"      forrás: {snapshot['source']}")
    ds_noisy = sim.sweep_counts(snapshot=snapshot, coupling_scale=1.0, shots=config.SHOTS, seed=config.SEED)
    res_noisy = analysis.analyze_dataset(ds_noisy, frozen)
    print(analysis.format_report(
        res_noisy, frozen_hash,
        f"zajos szimuláció, MINTA paraméterek ({time.time() - t0:.1f} s) — NEM hardver-eredmény",
    ))

    # --- 3. lépés: POZITÍV KONTROLL — csatolások kikapcsolva → elvárt: NULL ---
    print("\n[3/4] Pozitív kontroll: csatolások KIKAPCSOLVA (coupling_scale = 0.0)...")
    t0 = time.time()
    ds_broken = sim.sweep_counts(snapshot=None, coupling_scale=0.0, shots=config.SHOTS, seed=config.SEED)
    res_broken = analysis.analyze_dataset(ds_broken, frozen)
    print(analysis.format_report(
        res_broken, frozen_hash,
        f"POZITÍV KONTROLL (φ=0), {time.time() - t0:.1f} s — ennek NULL-t KELL adnia",
    ))

    # --- 4. lépés: összesítés és kilépési kód ---
    print("\n[4/4] Összesítés")
    v_ideal = res_ideal["verdict"]
    v_control = res_broken["verdict"]
    ok_ideal = v_ideal == analysis.VERDICT_TEXTBOOK
    ok_control = v_control == analysis.VERDICT_NULL
    print(f"  zajtalan szimuláció     → {v_ideal:<22} (elvárt: TEXTBOOK-MEGEROSITVE) {'OK' if ok_ideal else 'NEM OK!'}")
    print(f"  pozitív kontroll (φ=0)  → {v_control:<22} (elvárt: NULL)                 {'OK' if ok_control else 'NEM OK!'}")
    print(f"  zajos (MINTA) eredmény  → {res_noisy['verdict']:<22} (referenciaként közöljük; NEM hardver)")
    print(f"\n  teljes futásidő: {time.time() - t_start:.1f} s")

    if ok_ideal and ok_control:
        print("\nDRY RUN OK — a száraz futás teljesíti a feladat 4. lépésének elvárásait.")
        print("A QPU-futtatás NINCS elindítva; azt a Control Agent végzi audit után.")
        return 0
    print("\nDRY RUN NEM OK — az elvárt ítéletek nem jöttek ki.")
    print("ÁLLJ MEG ÉS JELENTSD AZ ELTERÉST — ne javítsd át a szimulációt vagy a szabályokat csendben!")
    return 1


if __name__ == "__main__":
    sys.exit(main())
