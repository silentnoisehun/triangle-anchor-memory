#!/usr/bin/env python3
"""scripts/audit_excitation_and_aer.py — Ruthless Physical and Noise Audit.

Checks:
1. Excitation conservation (Hamming weight distribution) in multi-qubit readout phases.
2. Direct comparison between Hardware measured populations and Aer predictions.
3. Identifies the origin of the Z=13.63 metric (differential artifact vs textbook noise).
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"

def analyze_hamming_weights(counts_dict: dict[str, int]):
    total = sum(counts_dict.values())
    if total == 0:
        return {}
    hw = {}
    for bitstr, c in counts_dict.items():
        clean_bits = bitstr.replace(" ", "")
        n_ones = clean_bits.count("1")
        hw[n_ones] = hw.get(n_ones, 0) + c
    return {k: {"shots": hw[k], "pct": hw[k] / total * 100.0} for k in sorted(hw.keys())}

def audit_phase9():
    path = DATA_DIR / "dist_mesh_raw_counts.json"
    if not path.exists():
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print("\n=======================================================")
    print("AUDIT: Phase 9 (Distributed Mesh, 4 Qubits: S0, S1, S2, S3)")
    print("Injected state: exactly 1 excitation (X gate on injection qubit)")
    print("=======================================================")
    for mode in ["hold_idle", "hold_mesh", "continuous"]:
        for k in ["8", "32"]:
            if k in data[mode]:
                counts = data[mode][k]["counts"]
                hw = analyze_hamming_weights(counts)
                tot = sum(counts.values())
                n_ge_2 = sum(hw[n]["shots"] for n in hw if n >= 2)
                p_ge_2 = n_ge_2 / tot * 100.0
                print(f"Mode: {mode:<12} k={k:<2} | N=0: {hw.get(0,{}).get('pct',0):.1f}% | "
                      f"N=1: {hw.get(1,{}).get('pct',0):.1f}% | N>=2: {p_ge_2:.1f}% (shots: {n_ge_2}/{tot})")

def audit_phase7():
    path = DATA_DIR / "tri_wheel_raw_counts.json"
    if not path.exists():
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print("\n=======================================================")
    print("AUDIT: Phase 7 (Tri-Wheel, 3 Satellite Cores: S1, S2, S3)")
    print("Injected state: exactly 1 excitation")
    print("=======================================================")
    for mode in ["nosync", "sync"]:
        for k in ["8", "32"]:
            if mode in data and k in data[mode]:
                counts = data[mode][k]["counts"]
                hw = analyze_hamming_weights(counts)
                tot = sum(counts.values())
                n_ge_2 = sum(hw[n]["shots"] for n in hw if n >= 2)
                p_ge_2 = n_ge_2 / tot * 100.0
                print(f"Mode: {mode:<12} k={k:<2} | N=0: {hw.get(0,{}).get('pct',0):.1f}% | "
                      f"N=1: {hw.get(1,{}).get('pct',0):.1f}% | N>=2: {p_ge_2:.1f}% (shots: {n_ge_2}/{tot})")

def audit_phase6():
    path = DATA_DIR / "dual_wheel_decouple_raw_counts.json"
    if not path.exists():
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print("\n=======================================================")
    print("AUDIT: Phase 6 (Dual-Wheel Decouple, S1 & S2)")
    print("Injected state: exactly 1 excitation")
    print("=======================================================")
    for mode in ["decouple", "continuous", "idle"]:
        if mode in data:
            for k in ["8", "32"]:
                if k in data[mode]:
                    counts = data[mode][k].get("counts", {})
                    if counts:
                        hw = analyze_hamming_weights(counts)
                        tot = sum(counts.values())
                        n_ge_2 = sum(hw[n]["shots"] for n in hw if n >= 2)
                        p_ge_2 = n_ge_2 / tot * 100.0
                        print(f"Mode: {mode:<12} k={k:<2} | N=0: {hw.get(0,{}).get('pct',0):.1f}% | "
                              f"N=1: {hw.get(1,{}).get('pct',0):.1f}% | N>=2: {p_ge_2:.1f}% (shots: {n_ge_2}/{tot})")

def audit_kerek_aer():
    fz_path = DATA_DIR / "wheel_freeze_data.json"
    hw_path = DATA_DIR / "wheel_raw_counts.json"
    if not (fz_path.exists() and hw_path.exists()):
        return
    with open(fz_path, "r", encoding="utf-8") as f:
        fz = json.load(f)
    with open(hw_path, "r", encoding="utf-8") as f:
        hw = json.load(f)
    
    print("\n=======================================================")
    print("AUDIT: Phase 4 (Kerék) Hardware vs Aer Noisy Simulation")
    print("=======================================================")
    checkpoints = [0, 4, 8, 12, 16, 20, 24, 28, 32]
    aer_wheel = fz["aer_prediction"]["wheel"]["curve"]
    
    print(f"{'k':<4} | {'Aer P(1)':<12} | {'HW P(1)':<12} | {'HW counts (1/total)':<22} | {'Diff (HW - Aer)':<15}")
    print("-" * 75)
    for idx, k in enumerate(checkpoints):
        k_str = str(k)
        hw_counts = hw["wheel"][k_str]
        tot = hw_counts["shots"]
        n1 = hw_counts["1"]
        hw_p1 = n1 / tot
        aer_p1 = aer_wheel[idx]
        diff = hw_p1 - aer_p1
        print(f"{k:<4} | {aer_p1*100:>10.2f}% | {hw_p1*100:>10.2f}% | {n1:>4}/{tot} ({hw_p1*100:>5.2f}%)       | {diff*100:>+10.2f}%")

if __name__ == "__main__":
    audit_phase9()
    audit_phase7()
    audit_phase6()
    audit_kerek_aer()
