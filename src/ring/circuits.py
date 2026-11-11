"""Gyűrű-menet áramkörök (0. fázis, szimulációhoz).

Logikai elrendezés: q1..q3 = gyűrű R1..R3 (q0 = S — CSAK a csillag-kontrollban
és a routolt-variansban szerepel, mint fizikai kötőelem; a gyűrű önmagában
NEM méri és NEM készíti elő az S-t).

A gyűrű-prep és a Peierls-élek a kerék-menet primitívjeivel AZONOSAK
(src.wheel.prep / circuits_base.edge_matrix) — a keringési sajátállapotok
ugyanazok.
"""
from __future__ import annotations
import math
from qiskit import QuantumCircuit
from qiskit.circuit.library import UnitaryGate

from src.wheel.circuits import PHI, PHI_F, EDGE_ORDER, RING_EDGES
from src.wheel.circuits_base import Q_S, Q_R1, Q_R2, Q_R3, edge_matrix
from src.wheel.prep import prep_angles


def prep_block(qc, m, dagger=False):
    t1, p1, t2, p2 = prep_angles(m)
    if not dagger:
        qc.x(Q_R1)
        qc.append(UnitaryGate(edge_matrix(t1, p1), label="P1"), [Q_R1, Q_R2])
        qc.append(UnitaryGate(edge_matrix(t2, p2), label="P2"), [Q_R2, Q_R3])
    else:
        qc.append(UnitaryGate(edge_matrix(t2, p2).conj().T, label="P2d"), [Q_R2, Q_R3])
        qc.append(UnitaryGate(edge_matrix(t1, p1).conj().T, label="P1d"), [Q_R1, Q_R2])
        qc.x(Q_R1)


def _filler_2q(qc, qa, qb):
    qc.cx(qa, qb); qc.cx(qa, qb)


def ring_edges(qc, k, cut=False, flux=None, pump_m=None, pump_fi=0.0, omega=0.0):
    flux = PHI_F if flux is None else flux
    for r in range(k):
        scale = 1.0
        if pump_m:
            scale = 1.0 + pump_m * math.cos(2 * omega * r + pump_fi)
        theta = PHI * scale
        for idx in EDGE_ORDER[r % 3]:
            qa, qb = RING_EDGES[idx]
            reverse = (idx == 2)
            if cut and idx == 2:
                _filler_2q(qc, qa, qb)   # CUT: csak a (R3,R1) él nyitott — a többi AKTÍV
            else:
                qc.append(UnitaryGate(edge_matrix(theta, flux, reverse=reverse),
                                      label=f"E{idx}"), [qa, qb])


def build_ring_arm(arm: str, k: int, pump_m=None, pump_fi=0.0, omega=0.0) -> QuantumCircuit:
    """Gyűrű-karok + staticus/broken. A mérés ELŐTT a fix + irány-unprep (prep_+†),
    majd R1-mérés. (A broken kar a kaputilus-illesztést tartja: I = CX·CX.)"""
    flux = PHI_F
    prep_m = {"ring_p": 1, "ring_m": -1, "ring_0": 0, "static": 1, "broken": 1, "pump": 1}[arm]
    if arm == "static":
        flux = 0.0
    qc = QuantumCircuit(4, 3, name=f"ring_{arm}_k{k}" + (f"_pm{pump_m}_pf{pump_fi}" if arm == "pump" else ""))
    prep_block(qc, prep_m)
    if arm == "pump":
        ring_edges(qc, k, cut=False, flux=flux, pump_m=pump_m or 0.0, pump_fi=pump_fi, omega=omega)
    else:
        ring_edges(qc, k, cut=(arm == "broken"), flux=flux)
    prep_block(qc, +1, dagger=True)     # FIX + irány-unprep — irány-switching TILOS
    qc.measure([Q_R1, Q_R2, Q_R3], [0, 1, 2])   # P_return = P(000) (az echo a vákuumba ad vissza)
    return qc


def build_star_control(k: int) -> QuantumCircuit:
    """(a) — csillag-visszaáramlás, azonos össz-kapukosztés: S=|1⟩, 3 küllő aktív
    (θ = PHI mindegyik), gyűrű-élek identitás; mérés: P(S=1)."""
    qc = QuantumCircuit(4, 1, name=f"ring_star_k{k}")
    qc.x(Q_S)
    for r in range(k):
        order = EDGE_ORDER[r % 3]
        for i, idx in enumerate(order):  # küllők ORDERS-rotált sorrendben, θ=PHI
            qa, qb = RING_EDGES[idx]
            _filler_2q(qc, qa, qb)
        for j, (qa, qb) in enumerate([(Q_S, Q_R1), (Q_S, Q_R2), (Q_S, Q_R3)]):
            qc.append(UnitaryGate(edge_matrix(PHI, 0.0), label="SP"), [qa, qb])
    qc.measure(Q_S, 0)
    return qc


def build_lone_idle(k: int) -> QuantumCircuit:
    """(b) — magányos qubit |1⟩, kapu nélkül, csak tárolás (mérés minden lépésben a
    gridnél). A 'round' itt csak időbélyeg — nincs kapu, nincs kitöltő."""
    qc = QuantumCircuit(3, 1, name=f"ring_lone_k{k}")
    qc.x(Q_R1)
    for _ in range(k):
        qc.id(Q_R1)
    qc.measure(Q_R1, 0)
    return qc


def build_delay_matched(k: int) -> QuantumCircuit:
    """(c) — horgony nélküli, csak identitás-kitöltők: ugyanaz a kaputilus-szám,
    mint a gyűrű-karban (3× 2 CX/kör), de NEM hat kölcsönhatás."""
    qc = QuantumCircuit(4, 1, name=f"ring_delayed_k{k}")
    qc.x(Q_R1)
    for r in range(k):
        for idx in EDGE_ORDER[r % 3]:
            qa, qb = RING_EDGES[idx]
            _filler_2q(qc, qa, qb)
    qc.measure(Q_R1, 0)
    return qc


def build_arm(arm: str, k: int, **kw) -> QuantumCircuit:
    if arm in ("ring_p", "ring_m", "ring_0", "static", "broken", "pump"):
        return build_ring_arm(arm, k, **kw)
    if arm == "star":
        return build_star_control(k)
    if arm == "lone":
        return build_lone_idle(k)
    if arm == "delayed":
        return build_delay_matched(k)
    raise ValueError(arm)
