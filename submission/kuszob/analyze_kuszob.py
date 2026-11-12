#!/usr/bin/env python3
"""Küszöb-job (Ring-Ramsey fáziszár-teszt) — LEFAGYASZTOTT elemző (v1.1).

A döntési szabály a PLAN_KUSZOB §5 (a)–(d) pontja, PONTOSAN — a TLS-szintű
formalizálás ebben a fájlban van befagyasztva (PLAN_KUSZOB_v1.1.md).
Ez a fájl fagyasztott: a PLAN_KUSZOB_v1.1.md a sha256-ját rögzíti; minden
módosítás új verziót és új hash-t igényel (külön commit, külön amended terv).

FORMÁLIS DÖNTÉSI SZABÁLY (egyoldalú 99% Wilson CI, z = Φ⁻¹(0.99) = 2.3263478740408408):

  Wilson-határok (pontbecslés p, n lövés):
      den    = 1 + z²/n
      center = p + z²/(2n)
      fél    = z·sqrt(p(1−p)/n + z²/(4n²))
      L(p,n) = (center − fél)/den        (egyoldalú alsó határ)
      U(p,n) = (center + fél)/den        (egyoldalú felső határ)

  (a) GÉP-EGÉSZSÉG — ELŐKAPU (pontbecslések):
      P(m+1,k=0) ≥ 0.70  ÉS  a három k=0 kar (m+1, m−1, m0) pairwise
      spread ≤ 0.10.  Bukás ⇒ ítélet = HALASZTAS (automatikus; nincs elsődleges döntés).

  (d) SZÉTESŐ-VEZÉRLŐK (ha (a) átment, de bármelyik kivált):
      (i)  PC-láthatóság: PC KIMUTATHATÓ ⇔ L(p_m1k0) − U(p_pc_k0) > 0
           (a pc k=0 99%-osan m+1 k=0 ALATT marad).
           Ha NEM mutatható ki ⇒ SZÉTESŐ.
      (ii) Negatív kontroll: P(cut,k=8) ≥ P(m+1,k=8) (pontbecslések) ⇒ SZÉTESŐ.
      Bármely kivált ⇒ ítélet = SZETESO (csomag HALASZTOTT + modell-audit; FELVÉTEL NINCS).

  (b) ELSŐDLEGES (ROGZUL-ág):
      L(p_m1k8) ≥ 0.5  ÉS  L(p_m1k8) − U(p_cutk8) > 0   (Wilson-differenciál,
      SPAM-robust: L₁ − U₂).  Mindkettő ⇒ ítélet = ROGZUL.

  (c) egyébként ⇒ ítélet = NULL  (a fáziszár nem mutatható ki ezen a
      négyesen/routingon; NULL-t NULL-ként jelentünk).

  precedencia (fail-closed sorrend, FAGYASZTVA):
      ERVENYTELEN  →  HALASZTAS (a)  →  SZETESO (d)  →  ROGZUL (b)  →  NULL (c)

  ERVENYTELEN (fail-closed): a 17 áramkör bármelyikének hiánya, nulla/összegtelen
  számlálója, negatív/nem egész/ NaN számlálója, vagy az '000' P_return nem
  értelmezhető ⇒ ITÉLET = ERVENYTELEN; semmilyen fizikai állítás nem készül.

  KÖTELEZŐ JELÖLÉS (ROGZUL esetén): "gep-alkalmassagi kapu, tankonyvi varakozas"
  — ez NEM memória-teszt és nem a Kerék-állítás.

Bemenet (counts JSON):
  {
    "shots": 4096,                      # információs; NEM dönti el az n-t
    "counts": { "<17 darab áramkör-id>": {"000": k, ...}, ... }
  }
  P_return(áramkör) = counts[id].get("000", 0) / sum(counts[id].values())
  (a mérés-huzalozás miatt a '000' kulcs a jel — lásd PLAN_KUSZOB_v1.1.)
  Ha a "shots" mező adott (egész): minden áramkör számláló-összegének
  PONTOSAN egyeznie kell vele — eltérés ⇒ ERVENYTELEN (fail-closed; a job
  fagyasztva 4096 shot/áramkörre).

Futtatás:
  elemzés:           analyze_kuszob.py counts.json          (kimenet: JSON a stdoutra)
  határ-null próba:  analyze_kuszob.py --null-probe 2000    (hamis-ROGZUL ≤ 1.5%?)
Kilépési kódok: 0 = ítélet elkészült (ROGZUL/NULL/SZETESO/HALASZTAS) · 3 = ERVENYTELEN ·
                2 = használati/IO hiba · --null-probe: 0 = PASS, 1 = FAIL (>1.5%)

QPU-hoz semmi köze; a token SEMMILYEN formában nem kerül elő.
"""
from __future__ import annotations

import argparse
import json
import math
import sys

Z_99 = 2.3263478740408408  # Φ⁻¹(0.99), egyoldalú 99%

# a 17 TÉNYLEGES áramkör-id (v1.0 manifest; sorrend: id-rendezve)
IDS = [
    "kuszob_cut_k2", "kuszob_cut_k4", "kuszob_cut_k8",
    "kuszob_m+1_k0", "kuszob_m+1_k2", "kuszob_m+1_k4", "kuszob_m+1_k8",
    "kuszob_m-1_k0", "kuszob_m-1_k2", "kuszob_m-1_k4", "kuszob_m-1_k8",
    "kuszob_m0_k0", "kuszob_m0_k2", "kuszob_m0_k4", "kuszob_m0_k8",
    "kuszob_pc_k0", "kuszob_pc_k4",
]

# zajtalan (Statevector-exact) referenciák a v1.0 manifestből — CSAK a null-próbához
EXACT = {
    "kuszob_cut_k2": 0.9029, "kuszob_cut_k4": 0.6935, "kuszob_cut_k8": 0.2460,
    "kuszob_m+1_k0": 1.0, "kuszob_m+1_k2": 0.9509, "kuszob_m+1_k4": 0.8628, "kuszob_m+1_k8": 0.8384,
    "kuszob_m-1_k0": 1.0, "kuszob_m-1_k2": 0.9475, "kuszob_m-1_k4": 0.8702, "kuszob_m-1_k8": 0.9208,
    "kuszob_m0_k0": 1.0, "kuszob_m0_k2": 0.8999, "kuszob_m0_k4": 0.7539, "kuszob_m0_k8": 0.8693,
    "kuszob_pc_k0": 7 / 9, "kuszob_pc_k4": 0.8501,
}
CUT_K8_EXACT = 0.2460
SHOTS = 4096

VERDICT_ROGZUL = "ROGZUL"
VERDICT_NULL = "NULL"
VERDICT_SZETESO = "SZETESO"
VERDICT_HALASZTAS = "HALASZTAS"
VERDICT_ERVENYTELEN = "ERVENYTELEN"

ROGZUL_MARKING = "gep-alkalmassagi kapu, tankonyvi varakozas"


def wilson_lower(p: float, n: int, z: float = Z_99) -> float:
    if n <= 0:
        return math.nan
    den = 1.0 + z * z / n
    center = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1.0 - p) / n + z * z / (4 * n * n))
    return (center - half) / den


def wilson_upper(p: float, n: int, z: float = Z_99) -> float:
    if n <= 0:
        return math.nan
    den = 1.0 + z * z / n
    center = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1.0 - p) / n + z * z / (4 * n * n))
    return (center + half) / den


def parse_counts(obj):
    """counts JSON → {id: (p000, n)}; bármi hiba ⇒ (None, [hibák])."""
    errors = []
    counts = obj.get("counts") if isinstance(obj, dict) else None
    if not isinstance(counts, dict):
        return None, ["hiányzik/érvénytelen a 'counts' objektum"]
    parsed = {}
    for cid in IDS:
        rec = counts.get(cid)
        if rec is None:
            errors.append(f"hiányzó áramkör: {cid}")
            continue
        if not isinstance(rec, dict) or not rec:
            errors.append(f"{cid}: üres/érvénytelen számláló")
            continue
        total = 0
        ok = True
        for v in rec.values():
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                errors.append(f"{cid}: nem numerikus számláló"); ok = False; break
            f = float(v)
            if not math.isfinite(f) or f < 0 or f != math.floor(f):
                errors.append(f"{cid}: érvénytelen számláló ({v!r})"); ok = False; break
            total += int(f)
        if not ok:
            continue
        if total <= 0:
            errors.append(f"{cid}: nulla összes shot")
            continue
        c000 = rec.get("000", 0)
        try:
            p000 = float(c000) / total
        except (TypeError, ZeroDivisionError):
            errors.append(f"{cid}: az '000' kulcs nem értelmezhető"); continue
        if not math.isfinite(p000):
            errors.append(f"{cid}: P000 nem véges"); continue
        parsed[cid] = (p000, total)
    # fail-closed: ha 'shots' adott, minden áramkörnek pontosan annyit kell hoznia
    declared = obj.get("shots") if isinstance(obj, dict) else None
    if isinstance(declared, bool) or not isinstance(declared, (int, float)) or not math.isfinite(float(declared)) or float(declared) != math.floor(float(declared)):
        if declared is not None:
            errors.append(f"a 'shots' mező érvénytelen: {declared!r}")
    else:
        declared_i = int(declared)
        if declared_i <= 0:
            errors.append(f"a 'shots' mező nem pozitív: {declared_i}")
        else:
            for cid, (_, total) in parsed.items():
                if total != declared_i:
                    errors.append(f"{cid}: összes shot = {total} ≠ deklarált {declared_i}")
    if errors:
        return None, errors
    return parsed, []


def decide(parsed):
    """A lefagyasztott szabály; parsed: {id: (p000, n)} (hiba nélkül)."""
    p = {cid: parsed[cid][0] for cid in IDS}
    n = {cid: parsed[cid][1] for cid in IDS}

    details = {
        "p_m+1_k0": p["kuszob_m+1_k0"], "p_m-1_k0": p["kuszob_m-1_k0"], "p_m0_k0": p["kuszob_m0_k0"],
        "p_pc_k0": p["kuszob_pc_k0"], "p_cut_k8": p["kuszob_cut_k8"], "p_m+1_k8": p["kuszob_m+1_k8"],
        "n_m+1_k8": n["kuszob_m+1_k8"], "n_cut_k8": n["kuszob_cut_k8"],
    }

    # (a) ELŐKAPU — gép-egészség (pontbecslések)
    k0_vals = [p["kuszob_m+1_k0"], p["kuszob_m-1_k0"], p["kuszob_m0_k0"]]
    spread = max(k0_vals) - min(k0_vals)
    details["k0_spread"] = spread
    if not (p["kuszob_m+1_k0"] >= 0.70):
        return VERDICT_HALASZTAS, [f"(a) gép-egészség bukott: P(m+1,k=0) = {p['kuszob_m+1_k0']:.4f} < 0.70"], details
    if spread > 0.10:
        return VERDICT_HALASZTAS, [f"(a) gép-egészség bukott: a három k=0 kar spread = {spread:.4f} > 0.10"], details

    # (d) SZÉTESŐ-vezérlők
    pc_L = wilson_lower(p["kuszob_m+1_k0"], n["kuszob_m+1_k0"])
    pc_U = wilson_upper(p["kuszob_pc_k0"], n["kuszob_pc_k0"])
    pc_detectable = (pc_L - pc_U) > 0.0
    details["wilson99_m+1_k0_lower"] = pc_L
    details["wilson99_pc_k0_upper"] = pc_U
    details["pc_detectable"] = bool(pc_detectable)
    if not pc_detectable:
        return VERDICT_SZETESO, ["(d)(i) a PC pozitív kontroll NEM mutatható ki "
                                 f"(99% Wilson: L(m+1,k=0) − U(pc,k=0) = {pc_L - pc_U:+.4f} ≤ 0)"], details
    if p["kuszob_cut_k8"] >= p["kuszob_m+1_k8"]:
        return VERDICT_SZETESO, [f"(d)(ii) negatív kontroll bukott: P(cut,k=8) = {p['kuszob_cut_k8']:.4f} "
                                 f"≥ P(m+1,k=8) = {p['kuszob_m+1_k8']:.4f}"], details

    # (b) ELSŐDLEGES — ROGZUL-ág (Wilson 99%, egyoldalú)
    Lb = wilson_lower(p["kuszob_m+1_k8"], n["kuszob_m+1_k8"])
    Uc = wilson_upper(p["kuszob_cut_k8"], n["kuszob_cut_k8"])
    diff_L = Lb - Uc
    details["wilson99_m+1_k8_lower"] = Lb
    details["wilson99_cut_k8_upper"] = Uc
    details["diff_lower"] = diff_L
    if (Lb >= 0.5) and (diff_L > 0.0):
        return VERDICT_ROGZUL, [f"(b) teljesül: L₉₉(P(m+1,k=8)) = {Lb:.4f} ≥ 0.5 ÉS "
                                f"L₉₉(P(m+1,k=8)) − U₉₉(P(cut,k=8)) = {diff_L:+.4f} > 0"], details

    # (c) NULL
    reasons = []
    if not (Lb >= 0.5):
        reasons.append(f"(b)(i) nem teljesül: L₉₉(P(m+1,k=8)) = {Lb:.4f} < 0.5")
    if not (diff_L > 0.0):
        reasons.append(f"(b)(ii) nem teljesül: a differenciál 99% Wilson alsó határa "
                       f"= {diff_L:+.4f} ≤ 0")
    return VERDICT_NULL, reasons, details


def analyze(obj):
    parsed, errors = parse_counts(obj)
    if parsed is None:
        return {"verdict": VERDICT_ERVENYTELEN,
                "reasons": ["fail-closed: " + e for e in errors],
                "marking": None}
    verdict, reasons, details = decide(parsed)
    out = {"verdict": verdict, "reasons": reasons, "details": details}
    if verdict == VERDICT_ROGZUL:
        out["marking"] = ROGZUL_MARKING
        out["note"] = ("ROGZUL = gépi alkalmassági kapu tankönyvi várakozáshoz; "
                       "NEM memória-teszt és NEM a Kerék-állítás.")
    elif verdict == VERDICT_NULL:
        out["note"] = "NULL — NULL-ként jelentjük; a fáziszár ezen a négyesen nem mutatható ki."
    else:
        out["note"] = ("nincs fizikai állítás; HALASZTÁS esetén a csomag státusza automatikusan "
                       "HALASZTOTT, SZÉTESŐ esetén modell-audit kötelező.")
    return out


def _synth_counts(p_map, shots, rng):
    counts = {}
    for cid, p in p_map.items():
        k = int(rng.binomial(shots, p))
        counts[cid] = {"000": k, "else": shots - k}
    return {"shots": shots, "counts": counts}


def null_probe(n_runs: int) -> int:
    import numpy as np

    probes = {
        "A (szimmetrikus határ: P(m+1,k=8) = P(cut,k=8) = 0.5)":
            {**EXACT, "kuszob_m+1_k8": 0.5, "kuszob_cut_k8": 0.5},
        "B (differenciál-legkedvezőbb határ: P(m+1,k=8) = 0.5, cut = exact 0.2460)":
            {**EXACT, "kuszob_m+1_k8": 0.5, "kuszob_cut_k8": CUT_K8_EXACT},
    }
    print(f"határ-null próba: {n_runs} szintetikus tankönyvi-null replay / próba, {SHOTS} shot, seedelt")
    worst = 0
    all_pass = True
    for probe_idx, (name, p_map) in enumerate(probes.items()):
        from collections import Counter
        verdicts = Counter()
        seed_base = 20261112000 + 10**9 * probe_idx
        for i in range(n_runs):
            counts = _synth_counts(p_map, SHOTS, np.random.default_rng(seed_base + i))
            verdicts[analyze(counts)["verdict"]] += 1
        n_rogzul = verdicts.get(VERDICT_ROGZUL, 0)
        rate = n_rogzul / n_runs
        ok = rate <= 0.015
        all_pass = all_pass and ok
        worst = max(worst, n_rogzul)
        print(f"  próba {name}")
        print(f"    ítéletek: {dict(verdicts)}")
        print(f"    hamis ROGZUL: {n_rogzul}/{n_runs} = {rate:.2%}  (elvárt ≤ 1.5%)  {'OK' if ok else 'NEM OK!'}")
    print(f"  legrosszabb: {worst}/{n_runs} — minden eredmény SZIMULÁCIÓ, nem HARDWARE")
    print("NULL-PRÓBA:", "PASS" if all_pass else "FAIL — ÁLLJ MEG ÉS JELENTSD")
    return 0 if all_pass else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Küszöb-job lefagyasztott elemző (v1.1)")
    ap.add_argument("counts_json", nargs="?", help="számláló-JSON (a mérés kimenete)")
    ap.add_argument("--null-probe", type=int, metavar="N", nargs="?", const=2000,
                    help="határ-null próba N futással (alapértelmezés 2000)")
    args = ap.parse_args()

    if args.null_probe is not None:
        return null_probe(args.null_probe)

    if not args.counts_json:
        ap.error("counts_json argumentum hiányzik (vagy --null-probe N)")
    try:
        with open(args.counts_json, "rb") as f:
            obj = json.load(f)
    except FileNotFoundError:
        print(f"HIBA: nem található a fájl: {args.counts_json}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"HIBA: érvénytelen JSON: {exc}", file=sys.stderr)
        return 2

    out = analyze(obj)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    if out.get("verdict") == VERDICT_ROGZUL:
        print()
        print(f"ROGZUL — KÖTELEZŐ JELÖLÉS: {ROGZUL_MARKING}")
        print("(ez nem memória-teszt; a Kerék-állításra nincs hatással)")
        return 0
    if out.get("verdict") == VERDICT_ERVENYTELEN:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
