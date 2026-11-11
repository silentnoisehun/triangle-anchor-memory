"""Pillanatkép-alapú zajos modell a Kerék-menet 0. fázisához.

A snapshot (data/snapshot.json, 2026-11-11T20:51:59Z, ibm_kingston, VALÓS
backend-pillanatkép — NEM hardver-eredmény) paraméterei töltődnek be:
  - T1/T2, eps_1q, eps_2q, eps_readout qubitenként;
  - S–A1/A2/A3 él-mérési hibák (a gyűrű-élek NEM léteznek — ezekre
    az érintett qubitek eps_2q értékeinek ÖSSZEGVEL számolunk, dokumentált
    közelítés);
  - kapuidők: t1q=0.032 µs, t2q=0.068 µs, t_readout=2.18 µs.

A modell: qubitenként thermal (T1,T2,kapuidő) ∘ depolarizáló (eps_1q) —
unitary/CX kapu után; delay-en thermal a tárolási időre; kiolvasás szimmetrikus
ReadoutError(eps_readout). A csillag-menet receptjével azonos szerkezet.
"""
from __future__ import annotations

import json
import math
import os

from qiskit_aer.noise import (NoiseModel, thermal_relaxation_error,
                              depolarizing_error, ReadoutError)

SNAPSHOT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "snapshot.json")
TS_US = {"t1q": 0.032, "t2q": 0.068, "treadout": 2.18}

# logikai qubit -> snapshot-kulcs
LOGICAL_TO_SNAP = {0: "S", 1: "A1", 2: "A2", 3: "A3"}


def load_snapshot(path: str = SNAPSHOT_PATH):
    with open(path) as f:
        snap = json.load(f)
    return snap


def _thermal(T1_us, T2_us, gate_us):
    return thermal_relaxation_error(T1_us, min(T2_us, 2 * T1_us), gate_us)


def build_noise_model(path: str = SNAPSHOT_PATH) -> NoiseModel:
    snap = load_snapshot(path)
    qb = snap["qubits"]
    nm = NoiseModel()
    # 1-qubites kapuk: thermal ∘ depol minden qubiten
    one_q_errs = {}
    for lq, key in LOGICAL_TO_SNAP.items():
        p = qb[key]
        th = _thermal(p["T1_us"], p["T2_us"], TS_US["t1q"])
        dp = depolarizing_error(p["eps_1q"], 1)
        one_q_errs[lq] = th.compose(dp)
        nm.add_quantum_error(one_q_errs[lq], ["x", "rx", "rz", "sx", "h", "id"], [lq])
    # 2-qubites kapuk: páronként thermal(t2q) ⊗ ⊗ depolarizáló(él-hiba)
    edge_err = {}
    for e in snap["two_qubit_edges"]:
        a, b = e["physical"]
        edge_err[frozenset((a, b))] = e["error"]
    phys = {key: qb[key]["physical_qubit"] for key in ("S", "A1", "A2", "A3")}
    phys_to_log = {v: k for k, v in phys.items()}
    for i in range(4):
        for j in range(i + 1, 4):
            key_i, key_j = LOGICAL_TO_SNAP[i], LOGICAL_TO_SNAP[j]
            pi, pj = phys[key_i], phys[key_j]
            e2 = edge_err.get(frozenset((pi, pj)))
            if e2 is None:
                # gyűrű-él: nincs mért adat — a két qubit eps_2q összege (dokumentált)
                e2 = min(qb[key_i]["eps_2q"] + qb[key_j]["eps_2q"], 1.0)
            th_i = _thermal(qb[key_i]["T1_us"], qb[key_i]["T2_us"], TS_US["t2q"])
            th_j = _thermal(qb[key_j]["T1_us"], qb[key_j]["T2_us"], TS_US["t2q"])
            th = th_i.expand(th_j)
            dp = depolarizing_error(e2, 2)
            err = th.compose(dp)
            nm.add_quantum_error(err, ["unitary", "cx"], [i, j])
    # delay: thermal a qubitenkénti tárolási időre — t_hold FIX 5 µs (fagyasztott),
    # tehát a thermal t-je pontosan a delay hossza
    T_HOLD_US = 5.0
    for lq, key in LOGICAL_TO_SNAP.items():
        p = qb[key]
        nm.add_quantum_error(_thermal(p["T1_us"], p["T2_us"], T_HOLD_US), ["delay"], [lq])
    # kiolvasás: szimmetrikus ReadoutError
    for lq, key in LOGICAL_TO_SNAP.items():
        p = qb[key]
        nm.add_readout_error(ReadoutError([[1 - p["eps_readout"], p["eps_readout"]],
                                           [p["eps_readout"], 1 - p["eps_readout"]]]), [lq])
    return nm


def t1_t2_us():
    snap = load_snapshot()
    return {key: (snap["qubits"][key]["T1_us"], snap["qubits"][key]["T2_us"])
            for key in ("S", "A1", "A2", "A3")}


def build_noise_model_physical(physical_ids):
    """Zajos modell a VALÓS fizikai qubit-ID-kre (a transzpilált áramkörökhöz).

    physical_ids: pl. [117, 124, 125, 126] — a T1/T2/eps a snapshot-ból a
    qubit fizikai sorszáma szerint; a kétutas kapu-hiba a párhoz tartozó
    mért S–Ai él-hiba, ha van, különben az érintett qubitek eps_2q összege.
    A modell kapui: cz/cx (Heron natív), 1Q: x/rx/rz/sx/h/id, delay: thermal(5 µs).
    """
    snap = load_snapshot()
    qb = snap["qubits"]
    id_to_key = {}
    for key, p in qb.items():
        id_to_key[p["physical_qubit"]] = key
    # a modell a PRUNE-ELT áramkör qubit-indexeire (0..len-1) köti a hibákat,
    # de a paramétereket a FIZIKAI qubit-ID-khez tartozó snapshot-értékekből
    # veszi; a csatolt CNOT/CZ pár-hibákat a FIZIKAI párokhoz tartozó (mért
    # vagy becsült) él-hibából rakja össze.
    nm = NoiseModel()
    for i, pid in enumerate(physical_ids):
        key = id_to_key[pid]
        p = qb[key]
        th = _thermal(p["T1_us"], p["T2_us"], TS_US["t1q"])
        dp = depolarizing_error(p["eps_1q"], 1)
        nm.add_quantum_error(th.compose(dp), ["x", "rx", "rz", "sx", "h", "id"], [i])
    edge_err = {}
    for e in snap["two_qubit_edges"]:
        a, b = e["physical"]
        edge_err[frozenset((a, b))] = e["error"]
    n = len(physical_ids)
    for i in range(n):
        for j in range(i + 1, n):
            pi, pj = physical_ids[i], physical_ids[j]
            ki, kj = id_to_key[pi], id_to_key[pj]
            e2 = edge_err.get(frozenset((pi, pj)))
            if e2 is None:
                e2 = min(qb[ki]["eps_2q"] + qb[kj]["eps_2q"], 1.0)
            th_i = _thermal(qb[ki]["T1_us"], qb[ki]["T2_us"], TS_US["t2q"])
            th_j = _thermal(qb[kj]["T1_us"], qb[kj]["T2_us"], TS_US["t2q"])
            err = th_i.expand(th_j).compose(depolarizing_error(e2, 2))
            nm.add_quantum_error(err, ["cz", "cx"], [i, j])
    T_HOLD_US = 5.0
    for i, pid in enumerate(physical_ids):
        key = id_to_key[pid]
        p = qb[key]
        nm.add_quantum_error(_thermal(p["T1_us"], p["T2_us"], T_HOLD_US), ["delay"], [i])
    for i, pid in enumerate(physical_ids):
        key = id_to_key[pid]
        p = qb[key]
        nm.add_readout_error(ReadoutError([[1 - p["eps_readout"], p["eps_readout"]],
                                           [p["eps_readout"], 1 - p["eps_readout"]]]), [i])
    return nm
