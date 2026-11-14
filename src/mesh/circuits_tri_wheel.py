#!/usr/bin/env python3
"""src/mesh/circuits_tri_wheel.py — 10-qubites Háromcellás Kvantum-Busz (Tri-Wheel Mesh).

Geometria az IBM Heron heavy-hex rácson (100%-ban natív fizikai élek!):
  - Kerék 1 (Adó, Észak-Nyugat): Mag S1=105, küllők A1=104, A2=106, Híd1=117
  - Kerék 2 (Relé, Közép): Mag S2=125, küllők Híd1=117, B1=126, Híd2=124
  - Kerék 3 (Vevő, Dél): Mag S3=123, küllők Híd2=124, C1=122, C2=136

Logikai indexek (0-9):
  q0 = S1 (105)
  q1 = A1 (104)
  q2 = A2 (106)
  q3 = Híd1 (117)
  q4 = S2 (125)
  q5 = B1 (126)
  q6 = Híd2 (124)
  q7 = S3 (123)
  q8 = C1 (122)
  q9 = C2 (136)
"""
from __future__ import annotations

import math
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit.library import UnitaryGate

from src.wheel.circuits_base import edge_matrix
from src.wheel.prep import prep_angles

N_QUBITS_TRI = 10
Q_S1 = 0
Q_A1 = 1
Q_A2 = 2
Q_B117 = 3
Q_S2 = 4
Q_B126 = 5
Q_B124 = 6
Q_S3 = 7
Q_C122 = 8
Q_C136 = 9

PHI = math.pi / 16
PHI_F = math.pi / 6
T_HOLD_NS = 5000

# Küllők mindhárom kerékben (mindegyik direkt fizikai él a Heron rácson)
SPOKES_W1 = [(Q_S1, Q_A1), (Q_S1, Q_A2), (Q_S1, Q_B117)]
SPOKES_W2 = [(Q_S2, Q_B117), (Q_S2, Q_B126), (Q_S2, Q_B124)]
SPOKES_W3 = [(Q_S3, Q_B124), (Q_S3, Q_C122), (Q_S3, Q_C136)]

# Gyűrűk perem-csatolásai
RING_W1 = [(Q_A1, Q_A2), (Q_A2, Q_B117), (Q_B117, Q_A1)]
RING_W2 = [(Q_B117, Q_B126), (Q_B126, Q_B124), (Q_B124, Q_B117)]
RING_W3 = [(Q_B124, Q_C122), (Q_C122, Q_C136), (Q_C136, Q_B124)]


def build_tri_wheel_circuit(
    k_rounds: int,
    init_s1: bool = True,
    sync_coupling: bool = True,
    flux_w1: float = PHI_F,
    flux_w2: float = -PHI_F,
    flux_w3: float = PHI_F,
) -> QuantumCircuit:
    qr = QuantumRegister(N_QUBITS_TRI, "q")
    qc = QuantumCircuit(qr)

    # 1. Állapot-előkészítés: S1 gerjesztve
    if init_s1:
        qc.x(Q_S1)

    # Perem-qubitek előkészítése váltakozó kiralitású sajátállapotokba (+1, -1, +1)
    t1, p1, t2, p2 = prep_angles(+1)
    qc.x(Q_A1)
    qc.append(UnitaryGate(edge_matrix(t1, p1)), [Q_A1, Q_A2])
    qc.append(UnitaryGate(edge_matrix(t2, p2)), [Q_A2, Q_B117])

    if sync_coupling:
        t1b, p1b, t2b, p2b = prep_angles(-1)
        qc.x(Q_B126)
        qc.append(UnitaryGate(edge_matrix(t1b, p1b)), [Q_B126, Q_B124])
        qc.append(UnitaryGate(edge_matrix(t2b, p2b)), [Q_B124, Q_B117])

        t1c, p1c, t2c, p2c = prep_angles(+1)
        qc.x(Q_C122)
        qc.append(UnitaryGate(edge_matrix(t1c, p1c)), [Q_C122, Q_C136])
        qc.append(UnitaryGate(edge_matrix(t2c, p2c)), [Q_C136, Q_B124])

    # 2. Időfejlődés k ciklusban
    for r in range(k_rounds):
        # Kerék 1
        for qa, qb in SPOKES_W1:
            qc.append(UnitaryGate(edge_matrix(PHI, 0.0)), [qa, qb])
        for qa, qb in RING_W1:
            qc.append(UnitaryGate(edge_matrix(PHI, flux_w1)), [qa, qb])

        if sync_coupling:
            # Kerék 2 (Relé)
            for qa, qb in SPOKES_W2:
                qc.append(UnitaryGate(edge_matrix(PHI, 0.0)), [qa, qb])
            for qa, qb in RING_W2:
                qc.append(UnitaryGate(edge_matrix(PHI, flux_w2)), [qa, qb])
            # Inter-hub csatoló kapu S1 és S2 között
            qc.append(UnitaryGate(edge_matrix(PHI / 2.0, 0.0)), [Q_S1, Q_S2])

            # Kerék 3 (Vevő)
            for qa, qb in SPOKES_W3:
                qc.append(UnitaryGate(edge_matrix(PHI, 0.0)), [qa, qb])
            for qa, qb in RING_W3:
                qc.append(UnitaryGate(edge_matrix(PHI, flux_w3)), [qa, qb])
            # Inter-hub csatoló kapu S2 és S3 között
            qc.append(UnitaryGate(edge_matrix(PHI / 2.0, 0.0)), [Q_S2, Q_S3])

        qc.delay(T_HOLD_NS, list(range(N_QUBITS_TRI)), unit="ns")

    # 3. Végmérés mindhárom központon (S1, S2, S3)
    cr = ClassicalRegister(3, "meas")
    qc.add_register(cr)
    qc.measure(Q_S1, cr[0])
    qc.measure(Q_S2, cr[1])
    qc.measure(Q_S3, cr[2])

    return qc
