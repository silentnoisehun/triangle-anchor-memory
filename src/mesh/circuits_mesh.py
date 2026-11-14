#!/usr/bin/env python3
"""src/mesh/circuits_mesh.py — 7-qubites Kettős Kerék (Dual-Wheel Mesh) áramkörök.

Geometria az IBM Heron heavy-hex rácson:
  - Kerék 1: S1=125, A1=117, A2=126, A_shared=124
  - Kerék 2: S2=123, B1=122, B2=136, A_shared=124
  - Közös híd: 124 (direkt fizikai kapcsolat mindkét központhoz!)

Logikai indexek:
  q0 = S1 (125)
  q1 = A1 (117)
  q2 = A2 (126)
  q3 = A_shared (124)
  q4 = S2 (123)
  q5 = B1 (122)
  q6 = B2 (136)
"""
from __future__ import annotations

import math
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit.library import UnitaryGate

from src.wheel.circuits_base import edge_matrix
from src.wheel.prep import prep_angles

N_QUBITS_MESH = 7
Q_S1 = 0
Q_A1 = 1
Q_A2 = 2
Q_SHARED = 3
Q_S2 = 4
Q_B1 = 5
Q_B2 = 6

PHI = math.pi / 16
PHI_F = math.pi / 6
T_HOLD_NS = 5000

# Küllők mindkét kerékben
SPOKES_W1 = [(Q_S1, Q_A1), (Q_S1, Q_A2), (Q_S1, Q_SHARED)]
SPOKES_W2 = [(Q_S2, Q_B1), (Q_S2, Q_B2), (Q_S2, Q_SHARED)]

# Gyűrű-élek
RING_W1 = [(Q_A1, Q_A2), (Q_A2, Q_SHARED), (Q_SHARED, Q_A1)]
RING_W2 = [(Q_B1, Q_B2), (Q_B2, Q_SHARED), (Q_SHARED, Q_B1)]


def build_dual_wheel_circuit(
    k_rounds: int,
    init_s1: bool = True,
    init_s2: bool = False,
    sync_coupling: bool = True,
    flux_w1: float = PHI_F,
    flux_w2: float = -PHI_F,  # ellentétes fázisforgás a szinkron-reteszeléshez
) -> QuantumCircuit:
    qr = QuantumRegister(N_QUBITS_MESH, "q")
    qc = QuantumCircuit(qr)

    # 1. Állapot-előkészítés
    if init_s1:
        qc.x(Q_S1)
    if init_s2:
        qc.x(Q_S2)

    # Mindkét gyűrű előkészítése m=+1 és m=-1 gerjesztési sajátállapotba
    t1, p1, t2, p2 = prep_angles(+1)
    qc.x(Q_A1)
    qc.append(UnitaryGate(edge_matrix(t1, p1)), [Q_A1, Q_A2])
    qc.append(UnitaryGate(edge_matrix(t2, p2)), [Q_A2, Q_SHARED])

    if sync_coupling:
        t1b, p1b, t2b, p2b = prep_angles(-1)
        qc.x(Q_B1)
        qc.append(UnitaryGate(edge_matrix(t1b, p1b)), [Q_B1, Q_B2])
        qc.append(UnitaryGate(edge_matrix(t2b, p2b)), [Q_B2, Q_SHARED])

    # 2. Időfejlődés k ciklusban
    for r in range(k_rounds):
        # Kerék 1 küllők
        for qa, qb in SPOKES_W1:
            qc.append(UnitaryGate(edge_matrix(PHI, 0.0)), [qa, qb])

        # Kerék 1 gyűrű
        for qa, qb in RING_W1:
            qc.append(UnitaryGate(edge_matrix(PHI, flux_w1)), [qa, qb])

        if sync_coupling:
            # Kerék 2 küllők
            for qa, qb in SPOKES_W2:
                qc.append(UnitaryGate(edge_matrix(PHI, 0.0)), [qa, qb])

            # Kerék 2 gyűrű
            for qa, qb in RING_W2:
                qc.append(UnitaryGate(edge_matrix(PHI, flux_w2)), [qa, qb])

            # Közös csatoló híd fáziszáró kölcsönhatása (Kuramoto swap-link)
            qc.append(UnitaryGate(edge_matrix(PHI / 2.0, 0.0)), [Q_S1, Q_S2])

        qc.delay(T_HOLD_NS, list(range(N_QUBITS_MESH)), unit="ns")

    # 3. Végmérések mindkét központon (S1 és S2)
    cr = ClassicalRegister(2, "meas")
    qc.add_register(cr)
    qc.measure(Q_S1, cr[0])
    qc.measure(Q_S2, cr[1])

    return qc
