#!/usr/bin/env python3
"""Küszöb-job — ÜGYNÖK-OLDALI (nem független!) ellenőrző (v1.1: + CZ-kapu).

Ez NEM helyettesíti a tulajdonosi/Control Agent felülvizsgálatot; a
beküldés előtti kötelező ellenőrzések előszűrése. Ha BÁRMELYIK kapu bukik,
a csomag státusza automatikusan HARASZTOTT lesz (lásd README).

Futtatás: .venv/bin/python submission/kuszob/verify_kuszob.py [--aer]
QPU-hoz semmi köze; az Aer opcionális zaj-próba (rögzített mag).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from qiskit import qasm2  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST_PATH = os.path.join(HERE, "circuits_manifest.json")
RESULTS = {"checks": [], "all_pass": True}


def check(name, cond, detail=""):
    RESULTS["checks"].append({"check": name, "pass": bool(cond), "detail": str(detail)})
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""), flush=True)
    if not cond:
        RESULTS["all_pass"] = False


def main():
    man = json.load(open(MANIFEST_PATH))
    circuits = {c["id"]: c for c in man["circuits"]}
    check("circuit_count == 17", man["circuit_count"] == 17 and len(circuits) == 17, man["circuit_count"])

    # --- 1) QASM fájlok: parse + hash-egyezés
    for cid, entry in sorted(circuits.items()):
        path = os.path.join(HERE, entry["qasm_file"])
        raw = open(path, "rb").read()
        h = hashlib.sha256(raw).hexdigest()
        check(f"{cid} qasm sha256", h == entry["qasm_sha256"], "fajl-hosszak hashelve")

    # --- 2) determinisztikus újraépítés: hash-ek egyezése
    import submission.kuszob.build_kuszob as bk  # noqa: PLC0415
    for arm, ks in bk.ARMS.items():
        for k in ks:
            cid = f"kuszob_{arm}_k{k}"
            qc_unit = bk.build_logical(arm, k)
            sub, used, fl, t = bk.transpile_pruned(qc_unit)
            measured = bk.with_measurements(sub, used, fl)
            qasm = qasm2.dumps(measured)
            h = hashlib.sha256(qasm.encode()).hexdigest()
            check(f"{cid} rebuild deterministic", h == circuits[cid]["qasm_sha256"])

    # --- 3) zajtalan referencia: k=0 == 1.0 a fizikai karokban; PC == 7/9; cut csökken
    for arm in ("m+1", "m-1", "m0"):
        c = circuits[f"kuszob_{arm}_k0"]
        check(f"{arm} k=0 exact == 1.0", abs(c["p000_exact"] - 1.0) < 1e-9, c["p000_exact"])
    pc0 = circuits["kuszob_pc_k0"]["p000_exact"]
    check("pc k=0 exact == 7/9 (analitikus)", abs(pc0 - 7 / 9) < 1e-9, pc0)
    cut8 = circuits["kuszob_cut_k8"]["p000_exact"]
    m18 = circuits["kuszob_m+1_k8"]["p000_exact"]
    check("cut k=8 << m+1 k=8 (exact)", cut8 < m18 - 0.3, f"cut={cut8:.4f} vs m+1={m18:.4f}")

    # --- 4) kapuhiba-költséglet (a W3 számvitellel azonos): max ≤ 0.5
    worst = max(c["exp_2q_error"] for c in circuits.values())
    check("max exp_2q_error ≤ 0.5 (a W3-küszöb)", worst <= 0.5, worst)
    pairs_used = set()
    for c in circuits.values():
        pairs_used |= set(c["cz_pairs"].keys())
    allowed = {"125-117", "125-124", "125-126", "117-125", "124-125", "126-125"}
    check("minden CZ a három snapshot-élen fut", pairs_used <= allowed, sorted(pairs_used))

    # --- 4b) v1.1 CZ-kapu: minden QASM CZ-száma és CZ-párjai PONTOSAN a manifesttel
    # (Maya 2026-11-12 09:05 review: az initial_layout a QASM q0..q3 sorrendjének
    # megfelelő [117,124,125,126] kell legyen — lásd PLAN_KUSZOB_v1.1.md. Bármely
    # eltérés ⇒ FAIL ⇒ kilépési kód 1 ⇒ automatikus HALASZTÁS.)
    for cid, entry in sorted(circuits.items()):
        path = os.path.join(HERE, entry["qasm_file"])
        raw = open(path, encoding="utf-8").read()
        used = entry["used_physical_ids"]
        pairs = {}
        n_cz = 0
        for m in re.finditer(r"cz\s+q\[(\d+)\]\s*,\s*q\[(\d+)\]\s*;", raw):
            idxs = sorted((int(m.group(1)), int(m.group(2))))
            pa, pb = int(used[idxs[0]]), int(used[idxs[1]])
            key = f"{pa}-{pb}"
            pairs[key] = pairs.get(key, 0) + 1
            n_cz += 1
        check(f"{cid} CZ-szám == manifest (n_cz={entry['n_cz']})",
              n_cz == entry["n_cz"], f"qasm={n_cz}")
        same = pairs == entry["cz_pairs"]
        check(f"{cid} CZ-párok == manifest ({entry['cz_pairs']})",
              same, f"qasm={pairs}")

    # --- 5) tárolási padló (T1): min faktor ≥ 0.9 az összes áramkörre
    worst_storage = min(c["storage_min_factor"] for c in circuits.values())
    check("storage_min_factor ≥ 0.9", worst_storage >= 0.9, worst_storage)

    # --- 6) snapshot integritás a csillag job_meta.json-jéhez képest
    snap_sha = hashlib.sha256(open(os.path.join(ROOT, "data", "snapshot.json"), "rb").read()).hexdigest()
    meta = json.load(open(os.path.join(ROOT, "data", "job_meta.json")))
    check("snapshot sha256 == job_meta.json snapshot_sha256", snap_sha == meta["snapshot_sha256"], snap_sha)

    # --- 7) a Kerék-fagyasztás érintetlen
    sha_lines = open(os.path.join(ROOT, "preregistration", "frozen_wheel_params.sha256")).read().splitlines()
    fz_hash = None
    for line in sha_lines:
        parts = line.split()
        if len(parts) >= 2 and parts[-1] == "frozen_wheel_params.json":
            fz_hash = parts[0]
    actual_fz = hashlib.sha256(open(os.path.join(ROOT, "preregistration", "frozen_wheel_params.json"), "rb").read()).hexdigest()
    check("frozen_wheel_params.json hash érintetlen", fz_hash == actual_fz, actual_fz)

    # --- 8) opcionális Aer zaj-próba (rögzített mag, 2048 shot): hierarchia
    if "--aer" in sys.argv:
        from qiskit_aer import AerSimulator  # noqa: E402
        from src.wheel.noise import build_noise_model_physical  # noqa: E402
        import submission.kuszob.build_kuszob as bk  # noqa: E402
        for cid in ("kuszob_m+1_k0", "kuszob_pc_k0", "kuszob_cut_k8"):
            arm, k_s = cid[len("kuszob_"):].rsplit("_k", 1)
            qc_unit = bk.build_logical(arm, int(k_s))
            sub, used, fl, t = bk.transpile_pruned(qc_unit)
            measured = bk.with_measurements(sub, used, fl)
            nm = build_noise_model_physical(used)
            r = AerSimulator(noise_model=nm).run(measured, shots=2048, seed_simulator=20261111).result()
            cnt = r.get_counts()
            p000 = cnt.get("000", 0) / 2048
            print(f"   Aer({cid}): P000 = {p000:.4f}", flush=True)
            if cid == "kuszob_m+1_k0":
                check("Aer m+1 k=0 ≥ 0.70 (gép-egészség)", p000 >= 0.70, p000)
            elif cid == "kuszob_pc_k0":
                check("Aer pc k=0 < m+1 k=0 (PC kimutatható)", p000 < 0.85, p000)
            else:
                check("Aer cut k=8 < 0.70 (a negatív kontroll irányt tart)", p000 < 0.70, p000)

    print()
    print("ÖSSZESÍTÉS:", "PASS" if RESULTS["all_pass"] else "FAIL")
    RESULTS["summary"] = "PASS" if RESULTS["all_pass"] else "FAIL"
    with open(os.path.join(HERE, "verification_last.json"), "w") as f:
        json.dump(RESULTS, f, indent=2, ensure_ascii=False)
    return 0 if RESULTS["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
