"""Kerék-menet áramkörök (v1.1 terv szerint).

Logikai elrendezés: q0 = S (középpont, a CC bit), q1..q3 = gyűrű R1..R3.

Élek (XY-család, bármelyik pontosan 2 CX):
    edge_matrix(theta, phi) — lásd circuits_base.

Karok (minden kar azonos össz-időtartam, azonos 2Q-kapu-darabszám:
    minden aktív XY-kapu = 2 CX; minden identitás-kitöltő slot = CX·CX = 2 CX;
    a prep sablon azonos minden karban: X + 2 XY-kapu):

    wheel      — gyűrű m=+1 forgó (fluxus ON) + 3 küllő (0/120/240°)
    wheel_rev  — gyűrű m=−1 (ellenforgó, fluxus ON) + 3 küllő
    static     — gyűrű m=+1, de fluxus OFF (álló fázisoscilláció, nem forog) + 3 küllő
    ring_only  — gyűrű m=+1 forgó + küllők NINCSENEK (identitás-kitöltők)
    alone      — középpont magában (gyűrű- és küllő-élek identitás-kitöltők)
    alone_DD   — alone + pi-echo impulzus minden lépés végén (a DD-kontroll)
    pump_blind — wheel + vak parametrikus pumpa (másodlagos, W4)
    pump_dir   — wheel + iránykövető lökés (másodlagos, W4, csak középpont-megtartás)
    pump_wrong — wheel + fordított sorrendű lökések (W4 kontrollja)
    cut        — wheel, de a (R3,R1) gyűrű-él kihagyva (identitás-kitöltő) — negatív kontroll
    dark_m1    — sötétállapot-teszt, m=+1 (≈ wheel, S=|1>)
    dark_m0    — sötétállapot-teszt, m=0 (nem forgó, S=|1>)
    dark_mm1   — sötétállapot-teszt, m=−1 (ellenforgó, S=|1>)

A „variánsai":
    variant="ideal"   — logikai circuit (2 CX / XY-kapu a szimulációban is);
    variant="transpiled" — qiskit transpile a VALÓS ibm_kingston coupling-mapre
                           (initial_layout S=125,R1=117,R2=124,R3=126), a kapuszám
                           és a kapuhiba-költség a transpiler számaiból (javítás #1);
    variant="virtual" — routolt-helyett-virtuális gyűrű: minden gyűrű-élt
                           S-mediált, SOROS RÉSZLEGES SWAP-lánccal oldunk meg
                           (3 XY-kapu élenként), routolt összevetés a diff.
"""
from __future__ import annotations

import math
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit.library import UnitaryGate

from .circuits_base import Q_S, Q_R1, Q_R2, Q_R3, N_QUBITS, edge_matrix
from .prep import CIRCULATION, prep_angles

K = 32
T_HOLD_NS = 5000  # 5 µs / lépés (fagyasztott)
PHI = math.pi / 16        # élenként lépés/kör szög (STAR ugyanaz)
PHI_F = math.pi / 6       # fázistolás / él (a teljes fluxus Φ = 3·φ_f = π/2)
THETA_SP = PHI            # küllő-szög — A PRIORI azonos PHI-val
SPOKE_PHASES = [0.0, 2 * math.pi / 3, 4 * math.pi / 3]  # 0/120/240° (Maya-idézet)
OMEGA_DIR = (2 * 1.0477) / 3   # irány-szétválás szögfrekvenciája / kör (~0.6984 rad)
M_BLIND = 0.20                 # vak pumpa mélysége — A PRIORI
M_DIR = 0.20                   # W4 lökés mélysége — A PRIORI
PUMP_FREQ = 2.0 * OMEGA_DIR
PUMP_FI_P = 0.0
EPS_RESTORE = 0.15               # pozitív kontroll: Ry(2·eps) / lépés a |1> felé (javítás #4)

RING_EDGES = [(Q_R1, Q_R2), (Q_R2, Q_R3), (Q_R3, Q_R1)]
EDGE_ORDER = [[0, 1, 2], [1, 2, 0], [2, 0, 1]]  # ORDERS-szimmetria (kör-rotálás)
SPOKES = [(Q_S, Q_R1), (Q_S, Q_R2), (Q_S, Q_R3)]
T_STEP_NS = T_HOLD_NS + 6 * 68  # 6 kétqubites "slot" @ 68 ns + tárolás

ARM_DEFS = {
    "wheel":      {"prep_m": +1, "flux": True,  "spokes": True,  "echo": False, "pump": None,    "cut_edge": None, "dark": False, "init_S": None, "desc": "fogó gyűrű + küllők (a fő kar)"},
    "wheel_rev":  {"prep_m": -1, "flux": True,  "spokes": True,  "echo": False, "pump": None,    "cut_edge": None, "dark": False, "init_S": None, "desc": "ellenforgó gyűrű (W2)"},
    "static":     {"prep_m": +1, "flux": False, "spokes": True,  "echo": False, "pump": None,    "cut_edge": None, "dark": False, "init_S": None, "desc": "álló fázisoscilláció (fluxus OFF), ugyanazok a küllők"},
    "ring_only":  {"prep_m": +1, "flux": True,  "spokes": False, "echo": False, "pump": None,    "cut_edge": None, "dark": False, "init_S": None, "desc": "keringő gyűrű, középpont küllők nélkül"},
    "alone":      {"prep_m": +1, "flux": True,  "spokes": False, "echo": False, "pump": None,    "cut_edge": None, "dark": False, "init_S": None, "ring_off": True, "desc": "középpont magában — gyűrű-élek identitás-kitöltők"},
    "alone_DD":   {"prep_m": +1, "flux": True,  "spokes": False, "echo": True,  "pump": None,    "cut_edge": None, "dark": False, "init_S": None, "ring_off": True, "desc": "alone + minden lépésben X-echo (a DD-kontroll)"},
    "pump_blind": {"prep_m": +1, "flux": True,  "spokes": True,  "echo": False, "pump": "blind", "cut_edge": None, "dark": False, "init_S": None, "desc": "wheel + vak parametrikus pumpa (másodlagos, W4)"},
    "pump_dir":   {"prep_m": +1, "flux": True,  "spokes": True,  "echo": False, "pump": "dir",   "cut_edge": None, "dark": False, "init_S": None, "desc": "wheel + iránykövető lökés (másodlagos, W4 — csak középpont-megtartás)"},
    "pump_wrong": {"prep_m": +1, "flux": True,  "spokes": True,  "echo": False, "pump": "wrong", "cut_edge": None, "dark": False, "init_S": None, "desc": "wheel + fordított sorrendű lökések (W4 kontrollja)"},
    "cut":        {"prep_m": +1, "flux": True,  "spokes": True,  "echo": False, "pump": None,    "cut_edge": "ring_2", "dark": False, "init_S": None, "desc": "megszakított gyűrű (él 3–1 kivéve) — negatív kontroll"},
    "dark_m1":    {"prep_m": +1, "flux": True,  "spokes": True,  "echo": False, "pump": None,    "cut_edge": None, "dark": True,  "init_S": "1", "desc": "sötétállapot-teszt, m=+1 forgó"},
    "dark_m0":    {"prep_m": 0,  "flux": True,  "spokes": True,  "echo": False, "pump": None,    "cut_edge": None, "dark": True,  "init_S": "1", "desc": "sötétállapot-teszt, m=0 nem forgó"},
    "dark_mm1":   {"prep_m": -1, "flux": True,  "spokes": True,  "echo": False, "pump": None,    "cut_edge": None, "dark": True,  "init_S": "1", "desc": "sötétállapot-teszt, m=−1 ellenforgó"},
}
ARM_NAMES = list(ARM_DEFS)


def prep_block(qc: QuantumCircuit, m: int):
    t1, p1, t2, p2 = prep_angles(m)
    qc.x(Q_R1)
    qc.append(UnitaryGate(edge_matrix(t1, p1)), [Q_R1, Q_R2])
    qc.append(UnitaryGate(edge_matrix(t2, p2)), [Q_R2, Q_R3])


def _filler_2q(qc, qa, qb):
    qc.cx(qa, qb)
    qc.cx(qa, qb)


def add_round(qc, r: int, arm: str, k_rounds: int | None = None):
    spec = ARM_DEFS[arm]
    order = EDGE_ORDER[r % 3]
    phi_f = PHI_F if spec["flux"] else 0.0
    # --- gyűrű-élek (ORDERS-rotált sorrend)
    for idx in order:
        qa, qb = RING_EDGES[idx]
        reverse = (idx == 2)
        if spec.get("ring_off") or spec.get("cut_edge") == f"ring_{idx}":
            _filler_2q(qc, qa, qb)
        else:
            qc.append(UnitaryGate(edge_matrix(PHI, phi_f, reverse=reverse)), [qa, qb])
    # --- küllők (0/120/240°, azonos szög)
    if not spec["spokes"]:
        for qa, qb in SPOKES:
            _filler_2q(qc, qa, qb)
    else:
        for i, (qa, qb) in enumerate(SPOKES):
            qc.append(UnitaryGate(edge_matrix(THETA_SP, SPOKE_PHASES[i])), [qa, qb])
    # --- DD echo (alone_DD)
    if spec["echo"]:
        qc.x(Q_S)
    # --- pumpák (másodlagos, W4)
    if spec["pump"] == "blind":
        qc.rx(2 * M_BLIND * math.sin(PUMP_FREQ * r + PUMP_FI_P), Q_S)
    elif spec["pump"] == "dir":
        qc.rx(2 * M_DIR * math.cos(OMEGA_DIR * r), Q_S)
    elif spec["pump"] == "wrong":
        # a helyes irány követő sorrendjének FORDÍTOTTJA (ellentétes fázisú lökéssorrend)
        rr = (k_rounds - 1 - r) if k_rounds else r
        qc.rx(2 * M_DIR * math.cos(OMEGA_DIR * rr), Q_S)


def build_circuit(arm: str, k_rounds: int, pop_branch: int | None = 0,
                  variant: str = "ideal", positive_control: bool = False):
    """Teljes áramkör egy karon, k_rounds lépésben.

    pop_branch: populációs ág (0/1) S kezdőállapota Z-méréshez; None -> nincs X a S-en
                (a sötétállapot-teszt init_S=|1> definíciójával azonos).
    """
    if arm not in ARM_DEFS:
        raise KeyError(arm)
    spec = ARM_DEFS[arm]
    qr = QuantumRegister(N_QUBITS, "q")
    qc = QuantumCircuit(qr)
    if spec["init_S"] == "1":
        qc.x(Q_S)
    elif pop_branch is not None:
        if pop_branch == 1:
            qc.x(Q_S)
    prep_block(qc, spec["prep_m"])
    for r in range(k_rounds):
        add_round(qc, r, arm, k_rounds)
        qc.delay(T_HOLD_NS, [Q_S, Q_R1, Q_R2, Q_R3], unit="ns")
        if positive_control:
            qc.ry(2 * EPS_RESTORE, Q_S)
    return qc


def build_virtual_ring_circuit(arm: str, k_rounds: int, pop_branch: int | None = 0,
                               positive_control: bool = False):
    """Virtuális gyűrű: minden gyűrű-élt S-mediált, soros részleges SWAP-lánc helyettesít.

    U_XY(a,S,pi/2) · U_XY(S,b,phi_eff) · U_XY(a,S,pi/2) — az a informális
    "virtuális él" a,b között; a költség 3 XY-kapu élenként (6 CX/él + 1Q).
    Csak a gyűrű-élekre érvényes; a küllők változatlanok. Az összevetés a
    routolt változattal a szimuláció számaiból (PLAN_WHEEL_v1.1, javítás #1).
    """
    spec = ARM_DEFS[arm]
    if spec.get("ring_off"):
        return build_circuit(arm, k_rounds, pop_branch, positive_control=positive_control)
    qr = QuantumRegister(N_QUBITS, "q")
    qc = QuantumCircuit(qr)
    if spec["init_S"] == "1":
        qc.x(Q_S)
    elif pop_branch is not None:
        if pop_branch == 1:
            qc.x(Q_S)
    prep_block(qc, spec["prep_m"])
    phi_f = PHI_F if spec["flux"] else 0.0
    for r in range(k_rounds):
        order = EDGE_ORDER[r % 3]
        for idx in order:
            qa, qb = RING_EDGES[idx]
            reverse = (idx == 2)
            if spec.get("cut_edge") == f"ring_{idx}":
                _filler_2q(qc, qa, qb)
                continue
            ph = phi_f if not reverse else -phi_f
            # U_XY(qa,S,pi/2) · U_XY(S,qb,gamma) · U_XY(qa,S,pi/2)
            qc.append(UnitaryGate(edge_matrix(math.pi / 2, 0.0)), [qa, Q_S])
            qc.append(UnitaryGate(edge_matrix(PHI, ph)), [Q_S, qb])
            qc.append(UnitaryGate(edge_matrix(math.pi / 2, 0.0)), [qa, Q_S])
        if not spec["spokes"]:
            for qa, qb in SPOKES:
                _filler_2q(qc, qa, qb)
        else:
            for i, (qa, qb) in enumerate(SPOKES):
                qc.append(UnitaryGate(edge_matrix(THETA_SP, SPOKE_PHASES[i])), [qa, qb])
        if spec["echo"]:
            qc.x(Q_S)
        qc.delay(T_HOLD_NS, [Q_S, Q_R1, Q_R2, Q_R3], unit="ns")
        if positive_control:
            qc.ry(2 * EPS_RESTORE, Q_S)
    return qc


def logical_two_qubit_count(arm: str, k_rounds: int) -> int:
    """Logikai 2Q-kapuszám (aktív + identitás-kitöltő, 1 slot = 1 unitary/CX esetén azonos)."""
    spec = ARM_DEFS[arm]
    cnt = 2  # prep: 2 XY-kapu
    for r in range(k_rounds):
        cnt += 6
    return cnt


def k_checkpoints(mode: str = "standard"):
    if mode == "standard":
        return list(range(0, K + 1, 4))
    if mode == "full":
        return list(range(0, K + 1))
    raise ValueError(mode)
