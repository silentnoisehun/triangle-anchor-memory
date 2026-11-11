"""Gyűrű-menet szimuláció (0. fázis): zajtalan (Statevector exact) és zajos (Aer).

KÉT zajos varians (mindkettő a csillag snapshot.json-jából):
  - variant="native": a gyűrű-élek mint ha LÉTEZNÉNEK (A1,A2,A3) — a párhibák az
    érintett qubitek eps_2q-jával ÖSSZEGZÉSEL (dokumentált közelítés) — ez a
    felső korlát;
  - variant="routed": a TÉNYLEGES heavy-hex rácson transzpilálva (S=125 hub,
    opt=0, a kerék-menettel azonos beállítás), a CZ-párok mért él-hibáival —
    ez az "ahogy a chipen futna" szám.

Egyik sem hardware-eredmény. A '000'/'100' kulcsok a logikai mérés bitjei.
"""
from __future__ import annotations
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
from qiskit import QuantumCircuit, transpile, ClassicalRegister
from src.wheel.circuits_base import edge_matrix
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, thermal_relaxation_error, depolarizing_error, ReadoutError

from src.ring.circuits import build_arm
from src.wheel.noise import load_snapshot

SNAPSHOT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "snapshot.json")
TS_US = {"t1q": 0.032, "t2q": 0.068}
LOGICAL_KEYS = {0: "A1", 1: "A2", 2: "A3"}   # a natív 3-qubites variansban


def build_noise_model_native() -> NoiseModel:
    """3-qubites, natív-élek Aer-zajos modell (felső korlát)."""
    snap = load_snapshot()
    qb = snap["qubits"]
    nm = NoiseModel()
    for qi, key in LOGICAL_KEYS.items():
        p = qb[key]
        th = thermal_relaxation_error(p["T1_us"], min(p["T2_us"], 2 * p["T1_us"]), TS_US["t1q"])
        dp = depolarizing_error(p["eps_1q"], 1)
        nm.add_quantum_error(th.compose(dp), ["x", "rx", "rz", "sx", "h", "id"], [qi])
    for i in range(3):
        for j in range(i + 1, 3):
            ki, kj = LOGICAL_KEYS[i], LOGICAL_KEYS[j]
            pi_, pj_ = qb[ki], qb[kj]
            e2 = min(pi_["eps_2q"] + pj_["eps_2q"], 1.0)  # natív él nem létezik — összeg (dokumentált)
            th_i = thermal_relaxation_error(pi_["T1_us"], min(pi_["T2_us"], 2 * pi_["T1_us"]), TS_US["t2q"])
            th_j = thermal_relaxation_error(pj_["T1_us"], min(pj_["T2_us"], 2 * pj_["T1_us"]), TS_US["t2q"])
            err = th_i.expand(th_j).compose(depolarizing_error(e2, 2))
            nm.add_quantum_error(err, ["unitary", "cx"], [i, j])
    for qi, key in LOGICAL_KEYS.items():
        p = qb[key]
        nm.add_readout_error(ReadoutError([[1 - p["eps_readout"], p["eps_readout"]],
                                           [p["eps_readout"], 1 - p["eps_readout"]]]), [qi])
    return nm


def physical_pruned(qc_unit: QuantumCircuit):
    """Rout the (4-qubit) circuit on the real coupling map (opt=0), prune to the
    touched physical qubits; returns (sub, used, final_layout)."""
    snap = load_snapshot()
    t = transpile(qc_unit, basis_gates=["cz", "rz", "sx", "x", "delay", "id"],
                  coupling_map=snap["coupling_map"],
                  initial_layout=[125, 117, 124, 126],
                  optimization_level=0, seed_transpiler=1234)
    used = sorted({t.find_bit(q).index for ins in t.data for q in ins.qubits})
    remap = {pid: i for i, pid in enumerate(used)}
    sub = QuantumCircuit(len(used), name=qc_unit.name)
    for ins in t.data:
        qargs = [remap[int(t.find_bit(q).index)] for q in ins.qubits]
        sub.append(ins.operation, qargs)
    return sub, used, t.layout.final_index_layout()


def attached_measurement(sub: QuantumCircuit, used, final_layout, logical_q: int, clbit: int = 0):
    """Mérés a LOGIKAI qubit végső fizikai helyén, friss 1-bite s regiszterbe."""
    cr = ClassicalRegister(1, "c")
    m = sub.copy()
    m.add_register(cr)
    m.measure(used.index(final_layout[logical_q]), clbit)
    return m


def exact_p1(qc_unit: QuantumCircuit, logical_q_to_unitary_index: int) -> float:
    """Zajtalan exact P(mért bit = 1) a LOGIKAI áramkörön."""
    sv = Statevector.from_instruction(qc_unit.remove_final_measurements(inplace=False))
    probs = sv.probabilities()
    p = 0.0
    for state, pr in enumerate(probs):
        if (state >> logical_q_to_unitary_index) & 1:
            p += pr
    return float(p)


def exact_p000(qc_unit: QuantumCircuit, ring_qubits=(1, 2, 3)) -> float:
    """Zajtalan exact P(R1R2R3 = 000) — az ECHO-VISSZATÉRÉS valószínűsége."""
    sv = Statevector.from_instruction(qc_unit.remove_final_measurements(inplace=False))
    probs = sv.probabilities()
    p = 0.0
    mask = 0
    for q in ring_qubits:
        mask |= 1 << q
    for state, pr in enumerate(probs):
        if (state & mask) == 0:
            p += pr
    return float(p)


def run_noisy(arm: str, k: int, variant: str, shots: int, seed: int, **kw) -> dict:
    """Egy (kar, k) cella zajos Aer-futása; a közös kimenet: counts."""
    if arm in ("lone", "delayed"):
        qc = build_arm(arm, k)  # 3 qubitos, nincs S — szimulold natívan (fizikai leképezés: A1)
        nm = None
        snap = load_snapshot()
        # egyszerű zajos modell: A1 thermal+depol+readout
        p = snap["qubits"]["A1"]
        nm = NoiseModel()
        th = thermal_relaxation_error(p["T1_us"], min(p["T2_us"], 2 * p["T1_us"]), TS_US["t1q"])
        dp = depolarizing_error(p["eps_1q"], 1)
        nm.add_quantum_error(th.compose(dp), ["id", "x"], [0])
        nm.add_readout_error(ReadoutError([[1 - p["eps_readout"], p["eps_readout"]],
                                           [p["eps_readout"], 1 - p["eps_readout"]]]), [0])
        # NINCS 5 µs kitartás a gyűrű-protokollban — a tárolási hiba a kapukon átütéseken keresztül jön be
        r = AerSimulator(noise_model=nm).run(qc, shots=shots, seed_simulator=seed).result()
        return dict(counts=r.get_counts(), used=None, variant="lone-like")
    if variant == "native":
        qc = build_arm(arm, k, **kw)
        unit = qc.remove_final_measurements(inplace=False)
        # csak az első 3 qubitre építünk modellt (S-t elhagyjuk VAGY küllő-kontroll)
        if arm == "star":
            # a csillag-kontroll 4 qubites — a natív modell 4-qubites változatát használjuk
            nm = _native_4q_model()
            meas = _star_measurement(qc)
            r = AerSimulator(noise_model=nm).run(meas, shots=shots, seed_simulator=seed).result()
            return dict(counts=r.get_counts(), used=None, variant="native")
        nm = build_noise_model_native()
        c3 = ClassicalRegister(3, "c")
        m = unit.copy(); m.add_register(c3)
        m.measure([1, 2, 3], [0, 1, 2])   # R1,R2,R3 — a jel a '000' kulcs
        r = AerSimulator(noise_model=nm).run(m, shots=shots, seed_simulator=seed).result()
        return dict(counts=r.get_counts(), used=None, variant="native")
    # variant == "routed"
    qc = build_arm(arm, k, **kw)
    unit = qc.remove_final_measurements(inplace=False)
    sub, used, final_layout = physical_pruned(unit)
    from src.wheel.noise import build_noise_model_physical
    nm = build_noise_model_physical(used)
    if arm == "star":
        m = attached_measurement(sub, used, final_layout, 0, 0)   # S (logikai 0)
    else:
        cr = ClassicalRegister(3, "c")
        m = sub.copy(); m.add_register(cr)
        # c0<-R3', c1<-R2', c2<-R1' ; a jel a '000' (bitsorrend mindegy neki)
        for logical, clbit in ((3, 0), (2, 1), (1, 2)):
            m.measure(used.index(final_layout[logical]), clbit)
    r = AerSimulator(noise_model=nm).run(m, shots=shots, seed_simulator=seed).result()
    return dict(counts=r.get_counts(), used=used, variant="routed")


def _native_4q_model() -> NoiseModel:
    """4-qubites natív modell a csillag-kontrollhoz (S + A1..A3) — a kerék
    build_noise_model-jével azonos recept (S–Ai mért élek + ring-élek összeg-közelítés)."""
    from src.wheel.noise import build_noise_model
    return build_noise_model()


def _star_measurement(qc: QuantumCircuit):
    c1 = ClassicalRegister(1, "c")
    m = qc.copy()
    # a mérés már szerepel a qc-ben (S-re) — csak adjuk vissza
    return m


def exact_reference(arm: str, k: int, **kw) -> dict:
    """Zajtalan exact referencia — KARI JELLEMTŐL függő mennyiség:
    ring-family: P000 (echo-visszatérés); star: P(S=1); lone/delayed: P(R1=1)."""
    qc = build_arm(arm, k, **kw)
    if arm in ("lone", "delayed"):
        from src.wheel.circuits_base import Q_R1
        p = exact_p1(qc, Q_R1)   # a magányos qubit = Q_R1 (logikai 1)
    elif arm == "star":
        p = exact_p1(qc, 0)   # S (q0)
    else:
        p = exact_p000(qc, (1, 2, 3))
    return {"p_measure_exact": p}
def round_matrix(flux: float) -> np.ndarray:
    """EGY kör operátora a teljes 4-qubites térben (q0 = S, üres)."""
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import UnitaryGate
    from qiskit.quantum_info import Operator
    from src.wheel.circuits import EDGE_ORDER, RING_EDGES, PHI as _PHI
    qc = QuantumCircuit(4)
    for idx in EDGE_ORDER[0]:
        qa, qb = RING_EDGES[idx]
        qc.append(UnitaryGate(edge_matrix(_PHI, flux, reverse=(idx == 2))), [qa, qb])
    return Operator(qc).data


def omega_from_round_spectrum(flux: float = None) -> dict:
    """Ω — a keringési frekvencia (rad/kör) a kör-spektrumából.

    A egy-gerjesztéses blokk sajátértékeiből: Ω = |φ(j+) − φ(j−)|, ahol j+/j−
    a |k+> / |k−> sajátvektorok által dominált sajátértékek.
    """
    from src.wheel.prep import CIRCULATION
    from src.wheel.circuits import PHI_F as _DF
    flux = _DF if flux is None else flux
    U = round_matrix(flux)
    idxs = [1 << 1, 1 << 2, 1 << 3]  # q1,q2,q3 little-endian bitek (q0 üres)
    block = U[np.ix_(idxs, idxs)]
    w, v = np.linalg.eig(block)
    phases = np.angle(w)
    kp, km, k0 = CIRCULATION[+1], CIRCULATION[-1], CIRCULATION[0]
    labels = []
    for j in range(3):
        vj = v[:, j] / np.linalg.norm(v[:, j])
        labels.append({"phase": float(phases[j]),
                       "share_k+": float(abs(np.vdot(kp, vj)) ** 2),
                       "share_k-": float(abs(np.vdot(km, vj)) ** 2),
                       "share_k0": float(abs(np.vdot(k0, vj)) ** 2)})
    j_plus = max(range(3), key=lambda j: labels[j]["share_k+"])
    j_minus = max(range(3), key=lambda j: labels[j]["share_k-"])
    omega = abs(phases[j_plus] - phases[j_minus])
    return {"omega_rad_per_round": float(omega),
            "eigenphases": [float(p) for p in phases],
            "branches": labels,
            "j_plus": int(j_plus), "j_minus": int(j_minus)}


if __name__ == "__main__":
    print("omega:", omega_from_round_spectrum())
    print("smoke exact refs:")
    for arm in ("ring_p", "ring_m", "ring_0", "static", "broken", "star", "lone", "delayed"):
        print(arm, {k: round(exact_reference(arm, k)["p_measure_exact"], 4) for k in (0, 4, 32)})
