import json
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.audit_excitation_v2 import audit_phase, run_ideal_simulation, PHASE_FILES


def test_synthetic_marginal_identity():
    """Verify that the sum of marginals identically equals the expected number of excited qubits."""
    # Synthetic 3-qubit counts with multi-excitations
    # Bitstrings: c2 c1 c0
    counts = {
        "000": 100,
        "001": 200,
        "011": 150,
        "111": 50
    }
    shots = sum(counts.values())  # 500
    p0 = (200 + 150 + 50) / shots  # 400/500 = 0.8
    p1 = (150 + 50) / shots        # 200/500 = 0.4
    p2 = 50 / shots                # 50/500 = 0.1
    sum_marginals = p0 + p1 + p2   # 1.3

    hw = {0: 100, 1: 200, 2: 150, 3: 50}
    expected_n = (0 * 100 + 1 * 200 + 2 * 150 + 3 * 50) / shots  # (200 + 300 + 150)/500 = 650/500 = 1.3

    assert pytest.approx(sum_marginals, abs=1e-9) == expected_n
    assert sum_marginals > 1.0, "Multi-excitation shots cause the marginal sum to exceed 100%"


def test_bit_order_reversal_detection():
    """Verify that an inverted bit order produces a mismatch against stored P_* marginals."""
    cfg = PHASE_FILES["phase_7_tri_wheel"]
    res = audit_phase("phase_7_tri_wheel", cfg)
    # The real data has valid bit order
    for bname, bdata in res["branches"].items():
        for k_str, k_entry in bdata.items():
            assert k_entry["bit_order_valid"] is True

    # Artificially corrupt bit order: simulate by altering qubit names
    corrupted_cfg = {
        "file": cfg["file"],
        "qubit_names": ["S3", "S2", "S1"],  # Reversed order
        "phase_num": 7,
    }
    corrupted_res = audit_phase("phase_7_tri_wheel", corrupted_cfg)
    # Because S1 != S3 in the data (e.g. k=32: S1=0.275, S3=0.285), reversed names must fail validation
    has_mismatch = any(
        not k_entry["bit_order_valid"]
        for bdata in corrupted_res["branches"].values()
        for k_entry in bdata.values()
    )
    assert has_mismatch, "Reversed bit order must trigger validation failure"


def test_phase8_104_5_percent_exact_numbers():
    """
    Verify Phase 8 (fabric_13q) sync k=12 exact values:
    - Satellite HW distribution (0, 1, 2, 3): [136, 234, 125, 17]
    - (234 + 2*125 + 3*17) / 512 = 535 / 512 = 104.49%
    - Multi-satellite shots (>=2): 142/512 (27.73%)
    - Total 4-qubit multi-excitation (>=2): 241/512 (47.07%)
    """
    cfg = PHASE_FILES["phase_8_fabric_13q"]
    res = audit_phase("phase_8_fabric_13q", cfg)
    entry = res["branches"]["sync"]["12"]
    sat = entry["satellites"]

    assert sat["hw_sat"]["0"] == 136
    assert sat["hw_sat"]["1"] == 234
    assert sat["hw_sat"]["2"] == 125
    assert sat["hw_sat"]["3"] == 17

    assert pytest.approx(sat["sum_sat_marginals"], abs=1e-5) == 535.0 / 512.0
    assert pytest.approx(sat["sum_sat_marginals"] * 100.0, abs=0.01) == 104.49
    assert sat["marginal_identity_holds"] is True

    assert sat["multi_satellite_shots_ge_2"] == 142
    assert pytest.approx(sat["multi_satellite_pct_ge_2"], abs=0.1) == 27.7

    assert entry["multi_excitation_shots_ge_2"] == 241
    assert pytest.approx(entry["multi_excitation_pct_ge_2"], abs=0.1) == 47.1


def test_25_4_percent_belongs_to_phase7():
    """Verify that the 25.4% multi-excitation figure belongs to Phase 7 (Tri-Wheel, k=32 sync)."""
    cfg = PHASE_FILES["phase_7_tri_wheel"]
    res = audit_phase("phase_7_tri_wheel", cfg)
    entry_sync = res["branches"]["sync"]["32"]
    entry_nosync = res["branches"]["nosync"]["32"]

    assert entry_sync["multi_excitation_shots_ge_2"] == 130
    assert pytest.approx(entry_sync["multi_excitation_pct_ge_2"], abs=0.1) == 25.4

    assert entry_nosync["multi_excitation_shots_ge_2"] == 10
    assert pytest.approx(entry_nosync["multi_excitation_pct_ge_2"], abs=0.1) == 2.0


def test_phase9_numbers_reproduced():
    """
    Verify Phase 9 (dist_mesh) multi-excitation numbers at k=32:
    - hold_idle: 77/512 (15.0%)
    - hold_mesh: 168/512 (32.8%)
    - continuous: 285/512 (55.7%)
    """
    cfg = PHASE_FILES["phase_9_dist_mesh"]
    res = audit_phase("phase_9_dist_mesh", cfg)

    idle = res["branches"]["hold_idle"]["32"]
    mesh = res["branches"]["hold_mesh"]["32"]
    cont = res["branches"]["continuous"]["32"]

    assert idle["multi_excitation_shots_ge_2"] == 77
    assert pytest.approx(idle["multi_excitation_pct_ge_2"], abs=0.1) == 15.0

    assert mesh["multi_excitation_shots_ge_2"] == 168
    assert pytest.approx(mesh["multi_excitation_pct_ge_2"], abs=0.1) == 32.8

    assert cont["multi_excitation_shots_ge_2"] == 285
    assert pytest.approx(cont["multi_excitation_pct_ge_2"], abs=0.1) == 55.7


def test_phase7_p_s3_exact_value():
    """Verify Phase 7 tri_wheel sync k=32 yields P(S3) = 146/512 = 28.5%, NOT 30.1%."""
    cfg = PHASE_FILES["phase_7_tri_wheel"]
    res = audit_phase("phase_7_tri_wheel", cfg)
    p_s3 = res["branches"]["sync"]["32"]["marginals"]["S3"]["computed"]

    assert pytest.approx(p_s3, abs=1e-5) == 146.0 / 512.0
    assert pytest.approx(p_s3 * 100.0, abs=0.01) == 28.52
    assert abs(p_s3 * 100.0 - 30.1) > 1.0


def test_ideal_circuit_conserves_single_excitation():
    """Verify that noiseless statevector evolution strictly conserves the single excitation."""
    pytest.importorskip("qiskit")
    rep = run_ideal_simulation()
    assert rep["available"] is True
    res12 = rep["results"]["12"]
    res32 = rep["results"]["32"]

    assert pytest.approx(res12["p_weight_1"], abs=1e-5) == 1.000000
    assert pytest.approx(res12["sum_satellite_marginals"] * 100.0, abs=0.05) == 57.00

    assert pytest.approx(res32["p_weight_1"], abs=1e-5) == 1.000000
    assert pytest.approx(res32["sum_satellite_marginals"] * 100.0, abs=0.05) == 10.40
