# Research Proposal: IBM Quantum Credits Program

## 1. Project Title
**Triangle-Anchor Quantum Memory: Coherent Excitation Trapping and Subradiant Return Dynamics on IBM Heron Architecture**

---

## 2. Principal Investigator & Affiliation
* **Name:** Róbert Máté
* **ORCID:** [0009-0003-3986-6039](https://orcid.org/0009-0003-3986-6039)
* **GitHub Repository:** [https://github.com/silentnoisehun/triangle-anchor-memory](https://github.com/silentnoisehun/triangle-anchor-memory)
* **Status:** Independent Quantum Researcher / Theoretical and Computational Framework Developer

---

## 3. Executive Summary & Preliminary Hardware Breakthrough
Superconducting quantum processors (transmons) operating in open environments typically experience local Markovian decoherence, dissipating single-qubit excitation according to individual $T_1$ and $T_2^*$ relaxation times. 

In this preregistered experimental study, we investigated whether a three-anchor star/wheel topology ($S$ coupled symmetrically to three perimeter transmons $A_1, A_2, A_3$ with Peierls phase modulation) can engineer a subradiant bound state in the continuum (BIC). Through collective destructive interference of emission into dissipative channels and constructive interference at the central node ($S=125$), this configuration mimics phase-locking synchronization (reminiscent of coupled Kuramoto-Huygens oscillators), suppressing radiative decay and trapping coherent quantum state information.

### Hardware-Confirmed Preliminary Results (IBM Heron r2, `ibm_marrakesh`):
All preliminary phases were preregistered with SHA-256 cryptographic hashes and executed on utility-scale hardware:
1. **Threshold Phase Lock (Küszöb v1.3):** Confirmed on hardware (+39.1% excitation retention difference on $k=8$ rounds, Wilson 99% lower bound > 0.5).
2. **Negative Control (Gyűrű v1.2):** 24 circuits, confirmed `NULL` (textbook unanchored dissipation, ruling out false-positive anomalies).
3. **Open Hydrodynamic Star (Csillag v1.5 FAST):** 757 circuits, verified return time scaling ratios $P_1$ ($1 : 0.69 : 0.56$ matching theoretical prediction $1 : 0.71 : 0.58$) and amplitude hierarchy $P_2$.
4. **Closed-Loop Wheel (Kerék v1.2):** 117 circuits, **ANOMALOUS EXCITATION RETENTION CONFIRMED ($Z = 13.63$, $P < 10^{-15}$)**. The closed-loop wheel maintained $+16.1\%$ excitation retention at $k=32$ rounds ($AUC = 0.4615$), contrasting against the predicted collapse ($AUC_{Aer} = -0.2598$) seen in unanchored ring controls ($AUC = 0.3006$).

---

## 4. Technical Feasibility & Utility-Scale Requirements
* **Target Hardware:** IBM Heron r2 (`ibm_marrakesh` / `ibm_kingston`), heavy-hex lattice.
* **Physical Qubit Cluster:** Core site $S=125$, symmetric anchors $A_1=117$, $A_2=124$, $A_3=126$.
* **Hardware Validation Pre-check:** All 4 preliminary phases already successfully compiled, executed, and evaluated on live QPU.
* **Execution Mode:** `SamplerV2` with zero-optimization gate preserving layout (`opt_level=0`) and calibrated dynamical decoupling.
* **Scaling Objective:** Scale from single-cell 4-qubit wheel to coupled multi-cell topological honeycomb lattices (12 to 24 qubits).

---

## 5. Requested Allocation & Justification
* **Requested Compute Time:** **3 to 5 hours of dedicated QPU time** on utility-scale Heron systems.
* **Justification:**
  - The standard Open Plan (10 min/month) was successfully used to demonstrate the preliminary $13.63\sigma$ effect on a single 4-qubit cell.
  - Investigating multi-cell coupled synchronization, topological boundary protection, and scaling to multi-ring lattices across 12-24 qubits requires continuous, multi-round parameter sweeps (thousands of circuits at 4096 shots).
  - Dedicated access is vital to confirm whether topological excitation trapping scales with cluster size, opening a pathway to passive, autonomous quantum memories that require no active syndrome measurement.

---

## 6. Open Science & Dissemination Plan
* All circuits, raw hardware counts, and analysis pipelines are open-source on GitHub under MIT / Apache licenses.
* Permanent archiving via CERN Zenodo with immutable DOI, directly attributed to PI's ORCID (`0009-0003-3986-6039`).
* High-resolution hardware return plots and statistical significance logs prepared for submission to arXiv / quantum physics journals.
