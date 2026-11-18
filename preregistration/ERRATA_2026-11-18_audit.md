# Erratum: Audit Phase Labels, Multi-Excitation Clarification, P(S3) Correction, and Backend Provenance

**Date:** 2026-11-18, 16:50 UTC (17:50 Budapest)  
**Author:** Maya & Máté Róbert (Lead Engineer)  
**Repository:** `triangle-anchor-memory`  
**Base Commit:** `1c8c402`  
**Scope:** Experimental documentation, audit scripts, bit-order census, and backend execution provenance.

---

## 1. Summary of Corrections

This erratum documents four specific corrections in experimental reporting and documentation. None of these corrections introduce any new physical memory effects; all experimental results remain completely consistent with standard textbook open-system quantum mechanics and gate depolarizing noise.

### Correction 1: Phase Label Consistency
In historical audit scripts and drafts (`scripts/audit_excitation_and_aer.py` and `docs/RED_TEAM_AUDIT_REPORT.md`), legacy phase numbers appeared in section headings despite the numbers themselves being accurate:
- `tri_wheel` (`dbsam57v5hds73dio4i0`) is formally **Phase 7** (previously mislabeled Phase 8).
- `dual_wheel_decouple` (`dbsa7vpabdes73fqts9g`) is formally **Phase 6** (previously mislabeled Phase 7).
- `wheel` Aer comparison (`dbs9bbvv5hds73dimmfg`) is formally **Phase 4** (previously mislabeled Phase 3).
The labels have been unified across all audit scripts and reports.

### Correction 2: Physical Explanation of the 104.5% Marginal Satellite Sum
In Phase 8 (`fabric_13q`, job `dbsap8ok09pc73avuql0`, `sync` arm, $k=12$), the sum of satellite core marginals is:
$$P(S_1) + P(S_2) + P(S_3) = 36.13\% + 37.30\% + 31.05\% = 104.49\% \approx 104.5\%$$
- **Mathematical Identity:** The sum of marginals identically equals the average number of excited satellites: $\sum_{i} P(S_i) \equiv \mathbb{E}[N_\text{sat}] = (234 + 2\cdot 125 + 3\cdot 17)/512 = 535/512 = 1.0449$.
- **Source of the >100% Value:** In an ideal, noiseless circuit with $XY$-type unitary coupling, the single excitation is strictly conserved ($P(\text{total excitation}=1) = 1.000000$, with satellite marginal sums of $57.00\%$ at $k=12$ and $10.40\%$ at $k=32$). On physical hardware, active gate driving continuously injects incoherent energy via depolarizing noise.
- **Correction:** Earlier text incorrectly cited the multi-excitation rate of Phase 7 ($25.4\%$). In Phase 8's own dataset:
  - **142 out of 512 shots (27.7%)** exhibit $\ge 2$ simultaneously excited satellites ($S_1, S_2, S_3$).
  - **241 out of 512 shots (47.1%)** exhibit $\ge 2$ excited qubits across all four measured transmons ($S_0, S_1, S_2, S_3$) at $k=12$.
  - At $k=32$ sync, multi-excitation across all 4 qubits remains high at **44.1%** (226/512 shots), compared to only **2.0%** (10/512 shots) in uncoupled `nosync`.

### Correction 3: Exact Value of Phase 7 Satellite Retention P(S3)
In the Phase 7 results table and summary (`tri_wheel`, `sync`, $k=32$), the single-satellite retention $P(S_3)$ was printed as $30.1\%$.
- Forensic re-computation from raw counts demonstrates that exactly 146 out of 512 shots were in $|1\rangle$:
  $$P(S_3) = \frac{146}{512} = \mathbf{28.515625\%} \approx 28.5\%$$
- No point in job `dbsam57v5hds73dio4i0` yields $30.1\%$. The table and narrative have been corrected to $28.5\%$.

### Correction 4: Backend Provenance and Aer Calibration Discrepancy
- **Backend Dispatch:** The experimental preregistration plans for Gyűrű (Phase 2, PLAN_RING_v1.2) and Csillag (Phase 3, PLAN_v1.5_FAST) specified `ibm_kingston`. On 2026-11-14, due to hardware availability and queue constraints, Phase 2 (Gyűrű), Phase 3 (Csillag v1.5), and Phase 4 (Kerék v1.2) were dispatched to `ibm_marrakesh`. Phase 1 (Küszöb) executed on `ibm_kingston` as originally planned. This is formally recorded as a planned-vs-executed backend deviation.
- **Aer Simulation Calibration Snapshot:** The $37.99\%$ Aer prediction for Phase 4 ($k=32$) was generated using an `ibm_kingston` calibration snapshot (`2026-11-11 20:51:59 UTC`), not `FakeMarrakesh`. Therefore, the $37.11\%$ vs $37.99\%$ correspondence is between `ibm_marrakesh` hardware and an `ibm_kingston` noise model.
- **Trajectory Discrepancy:** The close agreement at $k=32$ ($\Delta = -0.88\%$) is isolated to that specific step. Across the dynamical trajectory, substantial deviations occur: at $k=4$, hardware exceeds Aer by $+31.42$ percentage points ($50.00\%$ vs $18.58\%$), while at $k=8$, hardware undershoots Aer by $-31.01$ percentage points ($37.30\%$ vs $68.31\%$).

---

## 2. Software Deliverables & Verification Suite

1. **Audit Suite v2:** [`scripts/audit_excitation_v2.py`](../scripts/audit_excitation_v2.py) computes marginal checks, bit-order validations, and multi-excitation censuses across all branches and $k$-values, outputting to `data/audit_excitation_v2.json`. Includes `--ideal` for noiseless statevector verification.
2. **Automated Unit Tests:** [`tests/test_audit_excitation_v2.py`](../tests/test_audit_excitation_v2.py) contains 7 automated tests validating synthetic marginal identity, bit-order reversal detection, exact Phase 8 count numbers (136/234/125/17), Phase 7 provenance ($25.4\%$), Phase 9 rates, $P(S_3) = 146/512$, and ideal single-excitation conservation.
