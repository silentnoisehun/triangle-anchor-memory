#!/usr/bin/env python3
"""src/mesh/simulate_mesh.py — 7-qubites Kettős Kerék Kvantum-szinkronizáció szimulációja."""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.mesh.circuits_mesh import build_dual_wheel_circuit
from qiskit_aer import AerSimulator

sim = AerSimulator()
checkpoints = [0, 4, 8, 12, 16, 20, 24, 28, 32]

print("=" * 72)
print("DUAL-WHEEL SYNCHRONOUS QUANTUM MESH — SZIMULÁCIÓ")
print("=" * 72)
print(f"{'k':>3} | {'P(S1=1)':>10} | {'P(S2=1)':>10} | {'P(S1+S2 > 0)':>14} | {'Szinkron fázis'}")
print("-" * 72)

for k in checkpoints:
    qc = build_dual_wheel_circuit(k, init_s1=True, init_s2=False, sync_coupling=True)
    res = sim.run(qc, shots=2048, seed_simulator=20261111).result()
    counts = res.get_counts()
    total = sum(counts.values())

    # little endian: bit0=S1, bit1=S2
    p_s1 = sum(c for bits, c in counts.items() if bits[-1] == "1") / total
    p_s2 = sum(c for bits, c in counts.items() if bits[-2] == "1") / total
    p_any = sum(c for bits, c in counts.items() if "1" in bits) / total

    status = "Injektálás" if k == 0 else ("Koherens áramlás" if p_s2 > 0.05 else "Fáziszárt plató")
    print(f"{k:3d} | {p_s1:10.4f} | {p_s2:10.4f} | {p_any:14.4f} | {status}")

print("=" * 72)
