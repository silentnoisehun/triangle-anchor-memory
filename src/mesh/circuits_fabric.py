#!/usr/bin/env python3
"""src/mesh/circuits_fabric.py — 13-qubites 2D Kvantum Tér-Szövet (2D Quantum Space-Fabric).

Fizikai elrendezés az IBM Heron heavy-hex rácson (100%-ban natív fizikai élek, zéró SWAP!):
  - Központi Mag (Master Router): S0 = 125
  - Hidak a 3 szatellit felé:
      * Híd Észak-Nyugat: BNW = 117
      * Híd Észak-Kelet:  BNE = 126
      * Híd Dél:          BS  = 124
  - Szatellit 1 (Észak-Nyugat): Mag S1 = 105, küllők A1 = 104, A2 = 106
  - Szatellit 2 (Észak-Kelet):  Mag S2 = 127, küllők B1 = 128, B2 = 137
  - Szatellit 3 (Dél):          Mag S3 = 123, küllők C1 = 122, C2 = 136

Logikai indexek:
  q0  = S0 (125)
  q1  = BNW (117)
  q2  = BNE (126)
  q3  = BS (124)
  q4  = S1 (105)
  q5  = A1 (104)
  q6  = A2 (106)
  q7  = S2 (127)
  q8  = B1 (128)
  q9  = B2 (137)
  q10 = S3 (123)
  q11 = C1 (122)
  q12 = C2 (136)
"""
from __future__ import annotations

import math
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit.library import UnitaryGate

from src.wheel.circuits_base import edge_matrix
from src.wheel.prep import prep_angles

N_QUBITS_FABRIC = 13
Q_S0 = 0
Q_BNW = 1
Q_BNE = 2
Q_BS = 3
Q_S1 = 4
Q_A1 = 5
Q_A2 = 6
Q_S2 = 7
Q_B1 = 8
Q_B2 = 9
Q_S3 = 10
Q_C1 = 11
Q_C2 = 12

PHI = math.pi / 16
PHI_F = math.pi / 6
T_HOLD_NS = 5000

# 100%-ban natív fizikai élek a heavy-hex rácson
SPOKES_CENTER = [(Q_S0, Q_BNW), (Q_S0, Q_BNE), (Q_S0, Q_BS)]
SPOKES_W1 = [(Q_S1, Q_BNW), (Q_S1, Q_A1), (Q_S1, Q_A2)]
SPOKES_W2 = [(Q_S2, Q_BNE), (Q_S2, Q_B1), (Q_S2, Q_B2)]
SPOKES_W3 = [(Q_S3, Q_BS), (Q_S3, Q_C1), (Q_S3, Q_C2)]

RIM_W1 = [(Q_A1, Q_A2)]
RIM_W2 = [(Q_B1, Q_B2)]
RIM_W3 = [(Q_C1, Q_C2)]


def build_fabric_circuit(
    k_rounds: int,
    init_s0: bool = True,
    sync_coupling: bool = True,
    flux_w1: float = PHI_F,
    flux_w2: float = -PHI_F,
    flux_w3: float = PHI_F,
) -> QuantumCircuit:
    qr = QuantumRegister(N_QUBITS_FABRIC, "q")
    qc = QuantumCircuit(qr)

    # 1. Injektálás a központi magba
    if init_s0:
        qc.x(Q_S0)

    # 2. Időfejlődés k ciklusban
    for r in range(k_rounds):
        # Központi mag küllői
        for qa, qb in SPOKES_CENTER:
            qc.append(UnitaryGate(edge_matrix(PHI, 0.0)), [qa, qb])

        if sync_coupling:
            # Szatellit 1 (Észak-Nyugat)
            for qa, qb in SPOKES_W1:
                qc.append(UnitaryGate(edge_matrix(PHI, flux_w1)), [qa, qb])
            for qa, qb in RIM_W1:
                qc.append(UnitaryGate(edge_matrix(PHI, 0.0)), [qa, qb])

            # Szatellit 2 (Észak-Kelet)
            for qa, qb in SPOKES_W2:
                qc.append(UnitaryGate(edge_matrix(PHI, flux_w2)), [qa, qb])
            for qa, qb in RIM_W2:
                qc.append(UnitaryGate(edge_matrix(PHI, 0.0)), [qa, qb])

            # Szatellit 3 (Dél)
            for qa, qb in SPOKES_W3:
                qc.append(UnitaryGate(edge_matrix(PHI, flux_w3)), [qa, qb])
            for qa, qb in RIM_W3:
                qc.append(UnitaryGate(edge_matrix(PHI, 0.0)), [qa, qb])

        qc.delay(T_HOLD_NS, list(range(N_QUBITS_FABRIC)), unit="ns")

    # 3. Végmérés mind a 4 magon (S0, S1, S2, S3)
    cr = ClassicalRegister(4, "meas")
    qc.add_register(cr)
    qc.measure(Q_S0, cr[0])
    qc.measure(Q_S1, cr[1])
    qc.measure(Q_S2, cr[2])
    qc.measure(Q_S3, cr[3])

    return qc
