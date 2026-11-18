#!/usr/bin/env python3
"""
scripts/audit_excitation_v2.py — Multi-qubit Excitation, Bit-order, and Hardware-Audit Suite.

Verifies:
1. Bit-order consistency across all multi-qubit phases (Phases 6, 7, 8, 9), branches, and k.
2. Exact mathematical identity: sum of marginals == expected number of excited qubits / satellites.
3. Hamming weight distribution and multi-excitation noise pumping rates.
4. Optional --ideal flag for noiseless statevector excitation conservation test.
Output: data/audit_excitation_v2.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
DATA_DIR = REPO_ROOT / "data"

PHASE_FILES = {
    "phase_6_dual_wheel_decouple": {
        "file": "dual_wheel_decouple_raw_counts.json",
        "qubit_names": ["S1", "S2"],
        "phase_num": 6,
    },
    "phase_7_tri_wheel": {
        "file": "tri_wheel_raw_counts.json",
        "qubit_names": ["S1", "S2", "S3"],
        "phase_num": 7,
    },
    "phase_8_fabric_13q": {
        "file": "fabric_13q_raw_counts.json",
        "qubit_names": ["S0", "S1", "S2", "S3"],
        "satellite_indices": [1, 2, 3],  # S1, S2, S3
        "phase_num": 8,
    },
    "phase_9_dist_mesh": {
        "file": "dist_mesh_raw_counts.json",
        "qubit_names": ["S0", "S1", "S2", "S3"],
        "phase_num": 9,
    },
}


def parse_args():
    p = argparse.ArgumentParser(description="Multi-qubit Excitation & Bit-order Audit v2")
    p.add_argument("--ideal", action="store_true", help="Run noiseless statevector simulation check")
    p.add_argument("--output", type=str, default=str(DATA_DIR / "audit_excitation_v2.json"), help="Output JSON path")
    return p.parse_args()


def audit_phase(phase_key: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    file_path = DATA_DIR / cfg["file"]
    if not file_path.exists():
        return {"error": f"File {file_path} not found"}

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    qubit_names = cfg["qubit_names"]
    sat_indices = cfg.get("satellite_indices")
    results_by_branch = {}

    for branch_name, branch_data in data.items():
        if not isinstance(branch_data, dict):
            continue
        results_by_branch[branch_name] = {}

        for k_str, k_info in branch_data.items():
            if not isinstance(k_info, dict) or "counts" not in k_info:
                continue

            counts = k_info["counts"]
            total_shots = sum(counts.values())
            if total_shots == 0:
                continue

            # 1. Bit-order & marginal check
            marginals = {}
            bit_order_valid = True
            for i, qn in enumerate(qubit_names):
                # Qiskit little-endian: qubit index i is at position -1 - i
                comp_p = sum(c for bs, c in counts.items() if bs.replace(" ", "")[-1 - i] == "1") / total_shots
                stored_p = k_info.get(f"P_{qn}")
                marginals[qn] = {
                    "computed": comp_p,
                    "stored": stored_p,
                    "matches_stored": bool(stored_p is None or abs(comp_p - stored_p) < 1e-6),
                }
                if stored_p is not None and abs(comp_p - stored_p) >= 1e-6:
                    bit_order_valid = False

            # 2. Hamming weight breakdown on all measured qubits
            hw_all = {}
            for bs, c in counts.items():
                w = bs.replace(" ", "").count("1")
                hw_all[w] = hw_all.get(w, 0) + c

            n_ge_2 = sum(c for w, c in hw_all.items() if w >= 2)
            pct_ge_2 = n_ge_2 / total_shots * 100.0

            # Mean number of excited qubits (all measured)
            expected_n_all = sum(w * c for w, c in hw_all.items()) / total_shots
            sum_marginals_all = sum(m["computed"] for m in marginals.values())
            all_identity_match = bool(abs(expected_n_all - sum_marginals_all) < 1e-6)

            entry = {
                "shots": total_shots,
                "bit_order_valid": bit_order_valid,
                "marginals": marginals,
                "sum_marginals_all": sum_marginals_all,
                "expected_excitations_all": expected_n_all,
                "marginal_identity_holds": all_identity_match,
                "hw_all": {str(w): hw_all[w] for w in sorted(hw_all.keys())},
                "multi_excitation_shots_ge_2": n_ge_2,
                "multi_excitation_pct_ge_2": pct_ge_2,
            }

            # 3. Satellite-specific breakdown if applicable (e.g. Phase 8)
            if sat_indices is not None:
                hw_sat = {}
                for bs, c in counts.items():
                    clean_bs = bs.replace(" ", "")
                    # Extract satellite bits
                    w_sat = sum(1 for idx in sat_indices if clean_bs[-1 - idx] == "1")
                    hw_sat[w_sat] = hw_sat.get(w_sat, 0) + c

                expected_n_sat = sum(w * c for w, c in hw_sat.items()) / total_shots
                sum_sat_marginals = sum(marginals[qubit_names[idx]]["computed"] for idx in sat_indices)
                sat_identity_match = bool(abs(expected_n_sat - sum_sat_marginals) < 1e-6)
                n_sat_ge_2 = sum(c for w, c in hw_sat.items() if w >= 2)
                pct_sat_ge_2 = n_sat_ge_2 / total_shots * 100.0

                entry["satellites"] = {
                    "indices": sat_indices,
                    "names": [qubit_names[idx] for idx in sat_indices],
                    "hw_sat": {str(w): hw_sat.get(w, 0) for w in range(len(sat_indices) + 1)},
                    "expected_n_sat": expected_n_sat,
                    "sum_sat_marginals": sum_sat_marginals,
                    "marginal_identity_holds": sat_identity_match,
                    "multi_satellite_shots_ge_2": n_sat_ge_2,
                    "multi_satellite_pct_ge_2": pct_sat_ge_2,
                }

            results_by_branch[branch_name][k_str] = entry

    return {
        "phase_num": cfg["phase_num"],
        "file": cfg["file"],
        "branches": results_by_branch,
    }


def run_ideal_simulation() -> Dict[str, Any]:
    try:
        from qiskit.quantum_info import Statevector
        from src.mesh.circuits_fabric import build_fabric_circuit, Q_S1, Q_S2, Q_S3
    except ImportError as e:
        return {"available": False, "error": str(e)}

    ideal_results = {}
    for k in [12, 32]:
        qc = build_fabric_circuit(k, sync_coupling=True)
        qc_pure = qc.copy()
        qc_pure.remove_final_measurements()
        # Remove delays for unitary evolution
        qc_unitary = qc_pure.copy_empty_like()
        for inst in qc_pure.data:
            if inst.operation.name != "delay":
                qc_unitary.append(inst)

        sv = Statevector.from_instruction(qc_unitary)
        probs = sv.probabilities_dict()

        p_wt1 = sum(p for bs, p in probs.items() if bs.count("1") == 1)
        p_s1 = sum(p for bs, p in probs.items() if bs[-1 - Q_S1] == "1")
        p_s2 = sum(p for bs, p in probs.items() if bs[-1 - Q_S2] == "1")
        p_s3 = sum(p for bs, p in probs.items() if bs[-1 - Q_S3] == "1")
        p_sats = p_s1 + p_s2 + p_s3

        ideal_results[str(k)] = {
            "p_weight_1": float(p_wt1),
            "p_s1": float(p_s1),
            "p_s2": float(p_s2),
            "p_s3": float(p_s3),
            "sum_satellite_marginals": float(p_sats),
            "excitation_strictly_conserved": bool(abs(p_wt1 - 1.0) < 1e-5),
        }

    return {"available": True, "results": ideal_results}


def main():
    args = parse_args()
    print("=================================================================")
    print("triangle-anchor-memory — Multi-Qubit Excitation & Bit-Order Audit")
    print("=================================================================")

    full_report = {}
    for phase_key, cfg in PHASE_FILES.items():
        res = audit_phase(phase_key, cfg)
        full_report[phase_key] = res
        print(f"Phase {cfg['phase_num']} ({cfg['file']}): processed.")

    if args.ideal:
        print("\nRunning noiseless statevector conservation checks...")
        ideal_rep = run_ideal_simulation()
        full_report["ideal_noiseless_conservation"] = ideal_rep
        if ideal_rep.get("available"):
            for k_str, k_res in ideal_rep["results"].items():
                print(f"  Ideal k={k_str}: P(wt=1) = {k_res['p_weight_1']:.6f}, sum of satellite marginals = {k_res['sum_satellite_marginals']*100:.2f}%")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2)

    print(f"\nAudit complete. Output written to: {out_path}")


if __name__ == "__main__":
    main()
