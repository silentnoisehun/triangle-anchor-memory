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

## 3. Executive Summary & Scientific Merit
Superconducting quantum processors (transmons) operating in open environments typically experience local Markovian decoherence, dissipating single-qubit excitation according to individual $T_1$ and $T_2^*$ relaxation times. 

In this preregistered experimental study, we investigate whether a three-anchor star topology ($S$ coupled symmetrically to three perimeter transmons $A_1, A_2, A_3$ with Peierls phase modulation) can engineer a subradiant bound state in the continuum (BIC). Through collective destructive interference of emission into dissipative channels and constructive interference at the central node ($S=125$), this configuration mimics phase-locking synchronization (reminiscent of coupled Kuramoto-Huygens oscillators), suppressing radiative decay and trapping coherent quantum state information.

To ensure strict scientific integrity, the experiment is preregistered with cryptographic SHA-256 parameter locks and incorporates a negative control (Ring topology v1.2) to mathematically distinguish genuine topological excitation trapping from compilation artifacts or drift.

---

## 4. Technical Feasibility & Utility-Scale Requirements
* **Target Hardware:** IBM Heron r2 (`ibm_kingston`), heavy-hex lattice.
* **Physical Qubit Cluster:** Core site $S=125$, symmetric anchors $A_1=117$, $A_2=124$, $A_3=126$.
* **Hardware Validation Pre-check:** Threshold validation on Kingston $[117, 124, 125, 126]$ has already been confirmed on hardware (pass criteria met).
* **Execution Mode:** `SamplerV2` with calibrated dynamical decoupling and measurement mitigation.
* **Circuit Parameters:** 
  - Star v1.4: 757 transpiled circuits across equalized arm delays ($\Delta = 0$ dt), 4096 shots/circuit.
  - Ring v1.2 (Negative Control): 24 circuits, $k \le 16$, max 176 CZ gates.

---

## 5. Requested Allocation & Justification
* **Requested Compute Time:** **3 to 5 hours of dedicated QPU time** on utility-scale Heron systems (`ibm_kingston`).
* **Justification:**
  - Standard Open Plan (10 min/month) is severely insufficient for high-statistics (4096 shots), multi-parameter topological sweep (757 circuits requiring ~18 minutes of pure microwave pulse duration per full run, plus calibration runs).
  - Dedicated allocation will enable full Phase 1 (Star v1.4), Phase 2 (Ring v1.2 negative control benchmark), and Phase 3 (Wheel topology closed-loop synchronization).

---

## 6. Open Science & Dissemination Plan
* All circuits, transpilation graphs, and analysis pipelines are open-source on GitHub.
* Natively formatted with `CITATION.cff` linked to PI's ORCID (`0009-0003-3986-6039`).
* Upon execution, all raw bitstring counts and analysis outputs will be archived via CERN Zenodo with an immutable, permanent Digital Object Identifier (DOI).
* A preprint documenting the hardware-measured return curves and comparison to the Lindblad master equation will be submitted to arXiv.
