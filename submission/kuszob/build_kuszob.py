#!/usr/bin/env python3
"""Küszöb-job CIRCUIT-építő és szeletelő (QPU NÉLKÜL) — a küszöb-job csomag lelke.

Amit épít: a "Ring-Ramsey" echo-protokoll áramkörei (lásd PLAN_KUSZOB_v1.0.md):

    prep(m) → [PC? RZ(π/3) on R2] → k kör gyűrű-él (Peierls φ_f = π/6) → prep† → mérés

    P_return = P(R1R2R3 = 000) — az echo a VAKUUMBA ad vissza (prep∘prep† = I);
    a kapu NEM a |100⟩-ra vár — ez a leggyakoribb félreértés, a számlálásnál
    a '000' kulcs a jel.

NEM nyúl a fagyasztott Kerék-anyaghoz (frozen_wheel_params.json-t nem olvas).
A gyűrű-élek, a prep-sablon és a routing a src/wheel MEGLÉVŐ primitívjeire
épül (azonos Givens-prep, azonos Peierls-élek, azonos opt=0 routing) — így a
küszöb-job közvetlenül azzal a hardware-viselkedéssel áll kapcsolatban,
amit a Kerék-menet routolt áramkörei is látnak.

Kimenet (a script mappájába):
    circuits/<id>.qasm        — a TÉNYLEGES, routolt, kapuzott áramkör (4 qubit)
    circuits_manifest.json    — minden áramkör: id, kar, k, shots, hashek, kapuszámok,
                                zajtalan referencia (Statevector, exact), becsült 2Q-hiba
    gate_table.json           — a kaputilus-tábla páronként (a W3 számvitellel azonos)

Futtatás: .venv/bin/python submission/kuszob/build_kuszob.py
(A QPU-hoz SEMMILYEN kapcsolódást nem tartalmaz; a beküldést a /tmp-beli
csillag-referencia mutatja, de azt az agent SOSEM futtatja.)
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from qiskit import QuantumCircuit, transpile, ClassicalRegister  # noqa: E402
from qiskit.circuit.library import UnitaryGate  # noqa: E402
from qiskit.quantum_info import Statevector  # noqa: E402
import qiskit  # noqa: E402

from src.wheel.circuits import PHI, PHI_F, EDGE_ORDER, RING_EDGES  # noqa: E402
from src.wheel.circuits_base import Q_S, Q_R1, Q_R2, Q_R3, edge_matrix  # noqa: E402
from src.wheel.prep import prep_angles, CIRCULATION  # noqa: E402
from src.wheel.noise import load_snapshot  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CIRC_DIR = os.path.join(HERE, "circuits")
LAYOUT = [125, 117, 124, 126]  # S=125, R1=117, R2=124, R3=126 (a csillag-menet layoutja — fagyasztott)
BASIS = ["cz", "rz", "sx", "x", "delay", "id"]
OPT_LEVEL = 0          # a Kerék-menettel AZONOS választás (kaputilus-illesztés)
SEED_TRANSPILER = 1234
SHOTS = 4096
# karok és ellenpontok (PLAN_KUSZOB_v1.0, 4. fejezet)
ARMS = {"m+1": [0, 2, 4, 8], "m-1": [0, 2, 4, 8], "m0": [0, 2, 4, 8],
        "pc": [0, 4], "cut": [2, 4, 8]}
PC_PHASE = math.pi / 3  # az ismert beépített hiba fázisa (zajtalan referencia: 7/9)
T2Q_US = 0.068
T1Q_US = 0.035


def prep_block(qc: QuantumCircuit, m: int, dagger: bool = False) -> None:
    """A Kerék-menettel AZONOS Givens-prep-sablon (X(R1) + XY(R1,R2) + XY(R2,R3))."""
    t1, p1, t2, p2 = prep_angles(m)
    if not dagger:
        qc.x(Q_R1)
        qc.append(UnitaryGate(edge_matrix(t1, p1), label="P1"), [Q_R1, Q_R2])
        qc.append(UnitaryGate(edge_matrix(t2, p2), label="P2"), [Q_R2, Q_R3])
    else:
        qc.append(UnitaryGate(edge_matrix(t2, p2).conj().T, label="P2d"), [Q_R2, Q_R3])
        qc.append(UnitaryGate(edge_matrix(t1, p1).conj().T, label="P1d"), [Q_R1, Q_R2])
        qc.x(Q_R1)


def ring_rounds(qc: QuantumCircuit, k: int, cut: bool = False) -> None:
    """k darab gyűrű-kör: ORDERS-rotált élek, Peierls φ_f = π/6 (a cut: a 2-es él helyett CX·CX = I)."""
    for r in range(k):
        for idx in EDGE_ORDER[r % 3]:
            qa, qb = RING_EDGES[idx]
            reverse = (idx == 2)
            if cut and idx == 2:
                qc.cx(qa, qb)
                qc.cx(qa, qb)
            else:
                qc.append(UnitaryGate(edge_matrix(PHI, PHI_F, reverse=reverse),
                                      label=f"E{idx}"), [qa, qb])


def build_logical(arm: str, k: int) -> QuantumCircuit:
    m = {"m+1": 1, "m-1": -1, "m0": 0, "pc": 1, "cut": 1}[arm]
    qc = QuantumCircuit(4, name=f"kuszob_{arm}_k{k}")
    prep_block(qc, m)
    if arm == "pc":
        qc.rz(PC_PHASE, Q_R2)  # ismert, analitikusan számolt beépített hiba: P_return = 7/9 (zajtalan)
    ring_rounds(qc, k, cut=(arm == "cut"))
    prep_block(qc, m, dagger=True)
    return qc


def transpile_pruned(qc_unit: QuantumCircuit):
    """Rout the logical circuit on the REAL coupling map (opt=0), prune to touched
    physical qubits, keep the final logical->physical layout for the measurement wiring."""
    snap = load_snapshot()
    t = transpile(qc_unit, basis_gates=BASIS, coupling_map=snap["coupling_map"],
                  initial_layout=LAYOUT, optimization_level=OPT_LEVEL,
                  seed_transpiler=SEED_TRANSPILER)
    used = sorted({t.find_bit(q).index for ins in t.data for q in ins.qubits})
    remap = {pid: i for i, pid in enumerate(used)}
    sub = QuantumCircuit(len(used), name=qc_unit.name)
    for ins in t.data:
        qargs = [remap[t.find_bit(q).index] for q in ins.qubits]
        sub.append(ins.operation, qargs)
    final_layout = t.layout.final_index_layout()  # LOGIKAI -> FIZIKAI (coupling-map szám)
    return sub, used, final_layout, t


def with_measurements(sub: QuantumCircuit, used, final_layout) -> QuantumCircuit:
    """Mérés: c0 <- R3, c1 <- R2, c2 <- R1 (balról jobbra 'R1R2R3' a rekordlajstromban)."""
    cr = ClassicalRegister(3, "c")
    m = sub.copy()
    m.add_register(cr)
    for logical, clbit in ((3, 0), (2, 1), (1, 2)):
        m.measure(used.index(final_layout[logical]), clbit)
    return m


def routed_stats(t) -> dict:
    ops = t.count_ops()
    pairs: dict[tuple[int, int], int] = {}
    for ins in t.data:
        if ins.operation.name == "cz":
            idxs = tuple(sorted(int(t.find_bit(q).index) for q in ins.qubits))
            pairs[idxs] = pairs.get(idxs, 0) + 1
    snap = load_snapshot()
    paire = {(e["physical"][0], e["physical"][1]): e["error"] for e in snap["two_qubit_edges"]}
    exp_err = 0.0
    for (a, b), n in pairs.items():
        e = paire.get((a, b), paire.get((b, a)))
        exp_err += n * (e if e is not None else max(paire.values()))
    n_cz = sum(pairs.values())
    t_est = n_cz * T2Q_US + ops.get("sx", 0) * T1Q_US + ops.get("x", 0) * T1Q_US
    return {"ops": dict(ops), "depth": int(t.depth()),
            "cz_pairs": {f"{a}-{b}": n for (a, b), n in pairs.items()},
            "n_cz": int(n_cz), "exp_2q_error": float(exp_err),
            "t_est_us": float(t_est)}


def exact_p000(sub: QuantumCircuit, used, final_layout) -> dict:
    sv = Statevector.from_instruction(sub)
    probs = sv.probabilities()
    fl_idx = {q: used.index(final_layout[q]) for q in (1, 2, 3)}
    marg: dict[str, float] = {}
    for state, pr in enumerate(probs):
        bits = [(state >> q) & 1 for q in range(sub.num_qubits)]
        key = f"{bits[fl_idx[1]]}{bits[fl_idx[2]]}{bits[fl_idx[3]]}"
        marg[key] = marg.get(key, 0.0) + pr
    return {"p000_exact": float(marg.get("000", 0.0)),
            "marginal_r1r2r3": {k: float(v) for k, v in sorted(marg.items())}}


def main() -> int:
    os.makedirs(CIRC_DIR, exist_ok=True)
    manifest = {
        "kind": "KUSZOB-JOB CIRCUIT MANIFEST — AER/STATEVECTOR REFERENCIA, NEM HARDWARE",
        "created_utc": "2026-11-11",
        "qiskit_version": qiskit.__version__,
        "layout_logical_to_physical": {"q0(S,coupler)": 125, "q1(R1)": 117, "q2(R2)": 124, "q3(R3)": 126},
        "routing": {"initial_layout": LAYOUT, "optimization_level": OPT_LEVEL,
                    "seed_transpiler": SEED_TRANSPILER, "basis_gates": BASIS},
        "transpile_target": "data/snapshot.json coupling_map (ibm_kingston, 2026-11-11)",
        "shots_per_circuit": SHOTS,
        "circuits": [],
    }
    gate_table = []
    for arm, ks in ARMS.items():
        for k in ks:
            qasm_id = f"kuszob_{arm}_k{k}"
            qc_unit = build_logical(arm, k)
            sub, used, final_layout, t = transpile_pruned(qc_unit)
            measured = with_measurements(sub, used, final_layout)
            from qiskit import qasm2
            qasm = qasm2.dumps(measured)
            qasm_path = os.path.join(CIRC_DIR, f"{qasm_id}.qasm")
            with open(qasm_path, "w") as f:
                f.write(qasm)
            st = routed_stats(t)
            exact = exact_p000(sub, used, final_layout)
            snap = load_snapshot()
            T1 = {"S": snap["qubits"]["S"]["T1_us"], "A1": snap["qubits"]["A1"]["T1_us"],
                  "A2": snap["qubits"]["A2"]["T1_us"], "A3": snap["qubits"]["A3"]["T1_us"]}
            storage_min = min(math.exp(-st["t_est_us"] / v) for v in T1.values())
            entry = {
                "id": qasm_id, "arm": arm, "k": k, "shots": SHOTS,
                "final_layout_logical_to_physical": fl_list(final_layout),
                "used_physical_ids": used,
                "qasm_sha256": hashlib.sha256(qasm.encode()).hexdigest(),
                "qasm_file": f"circuits/{qasm_id}.qasm",
                **st, "storage_ge_095_check": bool(storage_min >= 0.9),
                "storage_min_factor": float(storage_min),
                **exact,
            }
            manifest["circuits"].append(entry)
            gate_table.append({"id": qasm_id, **{k2: entry[k2] for k2 in
                               ("n_cz", "cz_pairs", "exp_2q_error", "depth", "t_est_us")}})
            print(f"built {qasm_id}: n_cz={st['n_cz']} err={st['exp_2q_error']:.4f} "
                  f"P000_exact={exact['p000_exact']:.4f}", flush=True)
    manifest["circuits"].sort(key=lambda c: c["id"])
    man_id = ",".join(c["id"] for c in manifest["circuits"])
    # a payload a STABIL fv-nel: id-sorrend + qasm-hashek konkatenálva hashelve
    payload = hashlib.sha256(
        "".join(c["qasm_sha256"] for c in manifest["circuits"]).encode()
    ).hexdigest()
    manifest["payload_sha256"] = payload
    manifest["circuit_count"] = len(manifest["circuits"])
    with open(os.path.join(HERE, "circuits_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    with open(os.path.join(HERE, "gate_table.json"), "w") as f:
        json.dump(gate_table, f, indent=2, ensure_ascii=False)
    print(f"\n{len(manifest['circuits'])} áramkör | payload_sha256={payload}")
    print("circuits_manifest.json + gate_table.json + circuits/ mentve.")
    return 0


def fl_list(fl):
    return [int(x) for x in list(fl)]


if __name__ == "__main__":
    sys.exit(main())
