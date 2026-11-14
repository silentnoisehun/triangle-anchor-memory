#!/usr/bin/env python3
"""src/mesh/circuits_dist_mesh.py — Elosztott Autonóm Kvantum-Memória Hálózat (Distributed Quantum DRAM Mesh).

Protokoll:
  - Fázis A (Write & 2D Broadcast, r < k_pump): A központi mag (S0=125) a 3 hídon át feltölti a 3 szatellit magot.
  - Fázis B (Global Decoupling, r >= k_pump):
      * A központi mag és az összes híd (117, 126, 124) LE VAN KAPCSOLVA (0 kapu).
  - Fázis C (Distributed Autonomous Hold):
      * 'hold_mesh': A 3 izolált szatellit cella a térben magára hagyva, saját belső hurkaiban forog.
      * 'hold_idle': Minden kapu leáll (tétlen transzmon relaxációs kontroll).
      * 'continuous': A csatolás végig aktív marad (pozitív referencia).
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

# 100% natív élek
SPOKES_CENTER = [(Q_S0, Q_BNW), (Q_S0, Q_BNE), (Q_S0, Q_BS)]
SPOKES_W1 = [(Q_S1, Q_BNW), (Q_S1, Q_A1), (Q_S1, Q_A2)]
SPOKES_W2 = [(Q_S2, Q_BNE), (Q_S2, Q_B1), (Q_S2, Q_B2)]
SPOKES_W3 = [(Q_S3, Q_BS), (Q_S3, Q_C1), (Q_S3, Q_C2)]

RIM_W1 = [(Q_A1, Q_A2)]
RIM_W2 = [(Q_B1, Q_B2)]
RIM_W3 = [(Q_C1, Q_C2)]

# Izolált autonóm küllők a szatellitekhez (a hidak nélkül!)
AUTONOMOUS_SPOKES_W1 = [(Q_S1, Q_A1), (Q_S1, Q_A2)]
AUTONOMOUS_SPOKES_W2 = [(Q_S2, Q_B1), (Q_S2, Q_B2)]
AUTONOMOUS_SPOKES_W3 = [(Q_S3, Q_C1), (Q_S3, Q_C2)]


def build_dist_mesh_circuit(
    k_total: int,
    k_pump: int = 8,
    mode: str = "hold_mesh",
    flux_w1: float = PHI_F,
    flux_w2: float = -PHI_F,
    flux_w3: float = PHI_F,
) -> QuantumCircuit:
    qr = QuantumRegister(N_QUBITS_FABRIC, "q")
    qc = QuantumCircuit(qr)

    # 1. Injektálás a központi magba
    qc.x(Q_S0)

    # 2. Váltakozó kiralitású perem-előkészítés
    t1, p1, t2, p2 = prep_angles(+1)
    qc.x(Q_A1)
    qc.append(UnitaryGate(edge_matrix(t1, p1)), [Q_A1, Q_A2])
    qc.append(UnitaryGate(edge_matrix(t2, p2)), [Q_A2, Q_BNW])

    t1b, p1b, t2b, p2b = prep_angles(-1)
    qc.x(Q_B1)
    qc.append(UnitaryGate(edge_matrix(t1b, p1b)), [Q_B1, Q_B2])
    qc.append(UnitaryGate(edge_matrix(t2b, p2b)), [Q_B2, Q_BNE])

    t1c, p1c, t2c, p2c = prep_angles(+1)
    qc.x(Q_C1)
    qc.append(UnitaryGate(edge_matrix(t1c, p1c)), [Q_C1, Q_C2])
    qc.append(UnitaryGate(edge_matrix(t2c, p2c)), [Q_C2, Q_BS])

    # 3. Időfejlődés
    for r in range(k_total):
        if r < k_pump or mode == "continuous":
            # Teljes csatolt 2D hálózat
            for qa, qb in SPOKES_CENTER:
                qc.append(UnitaryGate(edge_matrix(PHI, 0.0)), [qa, qb])
            for qa, qb in SPOKES_W1:
                qc.append(UnitaryGate(edge_matrix(PHI, flux_w1)), [qa, qb])
            for qa, qb in RIM_W1:
                qc.append(UnitaryGate(edge_matrix(PHI, 0.0)), [qa, qb])
            for qa, qb in SPOKES_W2:
                qc.append(UnitaryGate(edge_matrix(PHI, flux_w2)), [qa, qb])
            for qa, qb in RIM_W2:
                qc.append(UnitaryGate(edge_matrix(PHI, 0.0)), [qa, qb])
            for qa, qb in SPOKES_W3:
                qc.append(UnitaryGate(edge_matrix(PHI, flux_w3)), [qa, qb])
            for qa, qb in RIM_W3:
                qc.append(UnitaryGate(edge_matrix(PHI, 0.0)), [qa, qb])
        elif mode == "hold_mesh":
            # Globális lekapcsolás: A központ és a hidak tétlenek (0 kapu).
            # Csak a 3 izolált szatellit kerék belső hurka forog autonóm módon!
            for qa, qb in AUTONOMOUS_SPOKES_W1:
                qc.append(UnitaryGate(edge_matrix(PHI, flux_w1)), [qa, qb])
            for qa, qb in RIM_W1:
                qc.append(UnitaryGate(edge_matrix(PHI, 0.0)), [qa, qb])

            for qa, qb in AUTONOMOUS_SPOKES_W2:
                qc.append(UnitaryGate(edge_matrix(PHI, flux_w2)), [qa, qb])
            for qa, qb in RIM_W2:
                qc.append(UnitaryGate(edge_matrix(PHI, 0.0)), [qa, qb])

            for qa, qb in AUTONOMOUS_SPOKES_W3:
                qc.append(UnitaryGate(edge_matrix(PHI, flux_w3)), [qa, qb])
            for qa, qb in RIM_W3:
                qc.append(UnitaryGate(edge_matrix(PHI, 0.0)), [qa, qb])
        elif mode == "hold_idle":
            # Tétlen relaxáció: nem fut kapu a lekapcsolás után
            pass

        qc.delay(T_HOLD_NS, list(range(N_QUBITS_FABRIC)), unit="ns")

    # 4. Végmérés mind a 4 magon (S0, S1, S2, S3)
    cr = ClassicalRegister(4, "meas")
    qc.add_register(cr)
    qc.measure(Q_S0, cr[0])
    qc.measure(Q_S1, cr[1])
    qc.measure(Q_S2, cr[2])
    qc.measure(Q_S3, cr[3])

    return qc
