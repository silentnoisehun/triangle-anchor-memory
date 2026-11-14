#!/usr/bin/env python3
"""src/mesh/circuits_decouple.py — Dual-Wheel Pump-and-Decouple (Lekapcsolási & Önfenntartási) áramkörök.

Protokoll:
  - Fázis A (Pump & Sync, r < k_pump): Mindkét kerék forog, híd-csatolás aktív.
  - Fázis B (Decouple & Hold, r >= k_pump):
      * 'hold_wheel2': A híd és a Kerék 1 lekapcsolva. A Kerék 2 önállóan tovább forog.
      * 'hold_idle': Minden kapu lekapcsolva a k_pump után (tétlen relaxációs kontroll).
      * 'continuous': A csatolás végig aktív marad (referencia bázis).
"""
from __future__ import annotations

import math
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

SPOKES_W1 = [(Q_S1, Q_A1), (Q_S1, Q_A2), (Q_S1, Q_SHARED)]
SPOKES_W2 = [(Q_S2, Q_B1), (Q_S2, Q_B2), (Q_S2, Q_SHARED)]

RING_W1 = [(Q_A1, Q_A2), (Q_A2, Q_SHARED), (Q_SHARED, Q_A1)]
RING_W2 = [(Q_B1, Q_B2), (Q_B2, Q_SHARED), (Q_SHARED, Q_B1)]


def build_pump_decouple_circuit(
    k_total: int,
    k_pump: int = 8,
    mode: str = "hold_wheel2",
    flux_w1: float = PHI_F,
    flux_w2: float = -PHI_F,
) -> QuantumCircuit:
    qr = QuantumRegister(N_QUBITS_MESH, "q")
    qc = QuantumCircuit(qr)

    # 1. Állapot-előkészítés: S1 gerjesztve
    qc.x(Q_S1)

    # Mindkét gyűrű előkészítése m=+1 és m=-1 sajátállapotba
    t1, p1, t2, p2 = prep_angles(+1)
    qc.x(Q_A1)
    qc.append(UnitaryGate(edge_matrix(t1, p1)), [Q_A1, Q_A2])
    qc.append(UnitaryGate(edge_matrix(t2, p2)), [Q_A2, Q_SHARED])

    t1b, p1b, t2b, p2b = prep_angles(-1)
    qc.x(Q_B1)
    qc.append(UnitaryGate(edge_matrix(t1b, p1b)), [Q_B1, Q_B2])
    qc.append(UnitaryGate(edge_matrix(t2b, p2b)), [Q_B2, Q_SHARED])

    # 2. Ciklusok futtatása
    for r in range(k_total):
        if r < k_pump or mode == "continuous":
            # Teljes csatolt szinkron háló
            for qa, qb in SPOKES_W1:
                qc.append(UnitaryGate(edge_matrix(PHI, 0.0)), [qa, qb])
            for qa, qb in RING_W1:
                qc.append(UnitaryGate(edge_matrix(PHI, flux_w1)), [qa, qb])
            for qa, qb in SPOKES_W2:
                qc.append(UnitaryGate(edge_matrix(PHI, 0.0)), [qa, qb])
            for qa, qb in RING_W2:
                qc.append(UnitaryGate(edge_matrix(PHI, flux_w2)), [qa, qb])
            # Közös csatoló híd fáziszáró kölcsönhatása
            qc.append(UnitaryGate(edge_matrix(PHI / 2.0, 0.0)), [Q_S1, Q_S2])
        elif mode == "hold_wheel2":
            # Lekapcsolt autonóm mód: Csak a Kerék 2 saját belső hurka forog!
            # Nincs inter-hub kapu, nincs kapu a Kerék 1-en.
            for qa, qb in SPOKES_W2:
                qc.append(UnitaryGate(edge_matrix(PHI, 0.0)), [qa, qb])
            for qa, qb in RING_W2:
                qc.append(UnitaryGate(edge_matrix(PHI, flux_w2)), [qa, qb])
        elif mode == "hold_idle":
            # Tétlen relaxáció: Nem fut kapu a k_pump után
            pass

        qc.delay(T_HOLD_NS, list(range(N_QUBITS_MESH)), unit="ns")

    # 3. Végmérés a két középponton (S1 és S2)
    cr = ClassicalRegister(2, "meas")
    qc.add_register(cr)
    qc.measure(Q_S1, cr[0])
    qc.measure(Q_S2, cr[1])

    return qc
