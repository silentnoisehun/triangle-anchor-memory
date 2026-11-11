"""Kerék-menet 0. fázis — szimulációs futtató.

MINDEN eredmény Aer-szimuláció (vagy noiseless állapotvektor) — SOHA nem
hardver-eredmény. A zajos futások a snapshot (data/snapshot.json) paramétereit
használják.
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from src.wheel.circuits import (ARM_NAMES, ARM_DEFS, build_circuit,
                                build_virtual_ring_circuit, K)
from src.wheel.noise import build_noise_model, build_noise_model_physical, load_snapshot


def p_s1_from_counts(counts: dict, s_is_q0: bool = True):
    n1 = 0
    n = 0
    for bits, c in counts.items():
        bit = int(bits.replace(" ", "")[-1]) if s_is_q0 else None
        # qiskit little-endian: az utolsó karakter q0 (S)
        n1 += (int(bits.replace(" ", "")[::-1][0])) * c
        n += c
    return (n1 / n if n else float("nan"))


def measure_circuit(qc: QuantumCircuit, s_qubit: int = 0):
    q = qc.cregs[0] if qc.cregs else None
    from qiskit import ClassicalRegister, QuantumRegister
    circ = qc.copy()
    cr = ClassicalRegister(1, "c")
    circ.add_register(cr)
    circ.measure(s_qubit, cr)
    return circ


def run_noisy(arms, k_list, pop_branch=0, shots=1024, seed=42,
              positive_control=False, variant="ideal", ring_off=False):
    nm = build_noise_model()
    sim = AerSimulator(noise_model=nm)
    out = {}
    for arm in arms:
        out[arm] = []
        for k in k_list:
            if variant == "virtual":
                qc = build_virtual_ring_circuit(arm, k, pop_branch=pop_branch,
                                                positive_control=positive_control)
            else:
                qc = build_circuit(arm, k, pop_branch=pop_branch,
                                   positive_control=positive_control)
            m = measure_circuit(qc, 0)
            r = sim.run(m, shots=shots, seed_simulator=seed).result()
            out[arm].append(p_s1_from_counts(r.get_counts()))
    return out


def run_ideal_state(arms, k_list, pop_branch=0, positive_control=False):
    from qiskit.quantum_info import Statevector
    out = {}
    for arm in arms:
        out[arm] = []
        for k in k_list:
            qc = build_circuit(arm, k, pop_branch=pop_branch,
                               positive_control=positive_control)
            sv = Statevector(qc).data
            probs = np.abs(sv) ** 2
            # S = q0 (kis-endian bit 0)
            p1 = sum(probs[i] for i in range(len(probs)) if (i & 1) == 1)
            out[arm].append(float(p1))
    return out


def routing_report(arm: str, k_rounds: int, pop_branch: int = 0, opt_level: int = 3):
    """A TÉNYLEGES coupling-map-en transzpilálva: kapuszámok (javítás #1)."""
    snap = load_snapshot()
    cm = snap["coupling_map"]
    basis = ["cz", "rz", "sx", "x", "delay", "id", "measure"]
    qc = build_circuit(arm, k_rounds, pop_branch=pop_branch)
    t0 = transpile(qc, basis_gates=basis, coupling_map=cm,
                   initial_layout=[125, 117, 124, 126], optimization_level=opt_level,
                   seed_transpiler=1234)
    ops = t0.count_ops()
    two_q = sum(v for k, v in ops.items() if k in ("cz", "cx", "ecr", "iswap", "swap"))
    return {"arm": arm, "k_rounds": k_rounds, "ops": dict(ops),
            "two_q": int(two_q), "depth": int(t0.depth()),
            "ops_total": int(sum(ops.values()))}


if __name__ == "__main__":
    print("module import OK")


def transpile_routed(arm: str, k_rounds: int, pop_branch: int = 0, opt_level: int = 0):
    """A TÉNYLEGES coupling-map-en transzpilált áramkör, képernyős prune-nal.

    initial_layout: S=125, R1=117, R2=124, R3=126 (a csillag-menet layoutja,
    PLAN_WHEEL_v1.1 javítás #1). Visszaadja: (prune-elt 4-qubites áramkör,
    used_physical_ids, transpile-statisztika).
    FIGYELEM: az opt_level=0 FAGYASZTOTT választás — az identitás-kitöltők
    (gate-count matching!) csak így maradnak tényleges kapuk; a szigorúbb
    opt=3-as számokat a terv mellékjelenti.
    """
    snap = load_snapshot()
    cm = snap["coupling_map"]
    basis = ["cz", "rz", "sx", "x", "delay", "id"]
    qc = build_circuit(arm, k_rounds, pop_branch=pop_branch)
    t = transpile(qc, basis_gates=basis, coupling_map=cm,
                  initial_layout=[125, 117, 124, 126],
                  optimization_level=opt_level, seed_transpiler=1234)
    used = sorted({t.find_bit(q).index for ins in t.data for q in ins.qubits})
    remap = {pid: i for i, pid in enumerate(used)}
    sub = QuantumCircuit(len(used), name=f"{arm}_routed_{k_rounds}")
    for ins in t.data:
        qargs = [remap[t.find_bit(q).index] for q in ins.qubits]
        sub.append(ins.operation, qargs, ins.clbits)
    s_final_phys = t.layout.final_index_layout()[0]  # virtual 0 = S végső helye
    ops = t.count_ops()
    two_q = sum(v for k, v in ops.items() if k in ("cz", "cx", "ecr", "swap", "iswap"))
    stats = {"arm": arm, "k_rounds": k_rounds, "ops": dict(ops),
             "two_q": int(two_q), "depth": int(t.depth()),
             "used_physical_ids": used, "s_final_phys": int(s_final_phys)}
    return sub, used, stats


def run_routed_noisy(arm: str, k_list, pop_branch: int = 0, shots: int = 1024, seed: int = 42):
    """A transzpilált áramkör zajos Aer-szimulációja a valós qubit-ID-ken."""
    from src.wheel.noise import build_noise_model_physical
    out = []
    stats_list = []
    for k in k_list:
        sub, used, stats = transpile_routed(arm, k, pop_branch=pop_branch)
        nm = build_noise_model_physical(used)
        sim = AerSimulator(noise_model=nm)
        m = sub.copy()
        from qiskit import ClassicalRegister
        s_idx = used.index(stats["s_final_phys"])
        cr = ClassicalRegister(1, "c")
        m.add_register(cr)
        m.measure(s_idx, cr)
        r = sim.run(m, shots=shots, seed_simulator=seed).result()
        out.append(p_s1_from_counts(r.get_counts()))
        stats_list.append(stats)
    return out, stats_list


def run_noisy_counts(arms, k_list, pop_branch=0, shots=2048, seed=42,
                     positive_control=False, variant="ideal"):
    """Nyers számlálók (arm, k) kulcson: {'0': n0, '1': n1} — a bootstraphoz."""
    nm = build_noise_model()
    sim = AerSimulator(noise_model=nm)
    out = {}
    for arm in arms:
        out[(arm, pop_branch)] = {}
        for k in k_list:
            if variant == "virtual":
                qc = build_virtual_ring_circuit(arm, k, pop_branch=pop_branch,
                                                positive_control=positive_control)
            else:
                qc = build_circuit(arm, k, pop_branch=pop_branch,
                                   positive_control=positive_control)
            m = measure_circuit(qc, 0)
            r = sim.run(m, shots=shots, seed_simulator=seed).result()
            c = r.get_counts()
            out[(arm, pop_branch)][k] = {"0": int(c.get("0", 0)), "1": int(c.get("1", 0)),
                                         "shots": int(shots)}
    return out


def collect_routed_counts(arm: str, k_list, shots: int = 2048, seed: int = 42,
                          positive_control: bool = False):
    """A FAGYASZTOTT protokoll szerint mért számlálók (routolt áramkör,
    physical-id zaj, S végső pozícióján mérve) — a dryrun/selftest és a
    valódi kiértékelés közös útvonala. NEM hardware."""
    from qiskit_aer import AerSimulator
    from qiskit import ClassicalRegister
    from src.wheel.noise import build_noise_model_physical
    out = {}
    for k in k_list:
        sub, used, stats = transpile_routed(arm, k, pop_branch=1)
        # pozitív kontroll: a routed-hoz épített logikai áramkörbe építjük a hatást
        if positive_control:
            from src.wheel.circuits import build_circuit
            from qiskit import transpile as _transpile
            from src.wheel.noise import load_snapshot
            snap = load_snapshot()
            qc = build_circuit(arm, k, pop_branch=1, positive_control=True)
            t = _transpile(qc, basis_gates=["cz", "rz", "sx", "x", "delay", "id"],
                           coupling_map=snap["coupling_map"],
                           initial_layout=[125, 117, 124, 126],
                           optimization_level=0, seed_transpiler=1234)
            s_final = t.layout.final_index_layout()[0]
            remap = {pid: i for i, pid in enumerate(used)}
            sub = QuantumCircuit(len(used))
            for ins in t.data:
                qargs = [remap[t.find_bit(q).index] for q in ins.qubits]
                sub.append(ins.operation, qargs, ins.clbits)
            stats = dict(stats)
            stats["s_final_phys"] = s_final
        nm = build_noise_model_physical(used)
        sim = AerSimulator(noise_model=nm)
        m = sub.copy()
        cr = ClassicalRegister(1, "c")
        m.add_register(cr)
        m.measure(used.index(stats["s_final_phys"]), cr)
        r = sim.run(m, shots=shots, seed_simulator=seed).result()
        c = r.get_counts()
        out[str(k)] = {"0": int(c.get("0", 0)), "1": int(c.get("1", 0)), "shots": int(shots)}
    return out
