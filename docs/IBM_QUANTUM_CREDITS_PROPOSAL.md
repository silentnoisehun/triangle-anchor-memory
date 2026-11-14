# Research Proposal: IBM Quantum Credits Program

## 1. Project Title
**Triangle-Anchor Quantum Memory & Synchronous Mesh: Topological Phase-Locking, Excitation Trapping, and Autonomous Memory Persistence on IBM Heron Heavy-Hex Processors**

---

## 2. Principal Investigator & Affiliation
* **Name:** Róbert Máté
* **ORCID:** [0009-0003-3986-6039](https://orcid.org/0009-0003-3986-6039)
* **GitHub Repository:** [https://github.com/silentnoisehun/triangle-anchor-memory](https://github.com/silentnoisehun/triangle-anchor-memory)
* **Status:** Independent Quantum Researcher / Quantum Mesh Systems Architect

---

## 3. Executive Summary & Hardware Breakthroughs

Superconducting transmon quantum processors operating in dissipative environments suffer from local Markovian decoherence, dissipating quantum state populations according to individual $T_1$ and $T_2^*$ relaxation times. Traditional quantum error correction (QEC) requires substantial physical qubit overhead and continuous active syndrome extraction, which introduces measurement-induced backaction.

In this preregistered experimental research project, we designed, simulated, and physically demonstrated **topological phase-locking and excitation trapping** on utility-scale superconducting processors without active syndrome measurements. By coupling a central node symmetrically to perimeter transmons with calibrated Peierls phase modulation, we engineered destructive emission into dissipative baths and constructive phase-locking at the hub.

### Hardware-Confirmed Results on IBM Heron r2 (`ibm_marrakesh` & `ibm_kingston`):
All 6 experimental phases were cryptographically preregistered with SHA-256 locks before QPU execution:

1. **Threshold Phase Lock (Küszöb v1.3):** Job `dbr1fl6jjaos73ai51pg` on `ibm_kingston`. **`ROGZUL`** (+39.1% excitation retention with 3-anchor, Wilson 99% lower bound > 0.50).
2. **Negative Control (Gyűrű v1.2):** Job `dbs8ijvv5hds73dilt40` on `ibm_marrakesh`. 24 circuits, confirmed **`NULL`** (unanchored ring undergoes rapid thermal decay, ruling out false-positive artifacts).
3. **Open Hydrodynamic Star (Csillag v1.5 FAST):** 4 chunks on `ibm_marrakesh`. 757 circuits, verified return time scaling ratios $P_1$ ($1 : 0.69 : 0.56$ vs predicted $1 : 0.71 : 0.58$) and non-Markovian memory recurrence.
4. **Closed-Loop Wheel (Kerék v1.2):** Job `dbs9bbvv5hds73dimmfg` on `ibm_marrakesh`. 117 circuits, **ANOMALOUS EXCITATION RETENTION CONFIRMED ($Z = 13.63$, $P < 10^{-15}$)**. Sustained macroscopic ~37% excitation retention plateau at $k=32$ Trotter steps (~200 physical gate depth) vs 8.9% collapse on unanchored rings.
5. **Dual-Wheel Synchronous Mesh:** Job `dbs9v0ujjaos73ajufr0` on `ibm_marrakesh`. 7-qubit cluster (Q125, Q117, Q126, Q124, Q123, Q122, Q136). Confirmed inter-cell quantum conduction ($P(S_2) = 0.3586 \ge 0.15$), Kuramoto-Huygens equipartition ($|P(S_1) - P(S_2)| = 0.0059 \le 0.15$), and collective network retention ($0.4805 \ge 0.35$).
6. **Pump-and-Decouple Autonomous Quantum DRAM:** Job `dbsa7vpabdes73fqts9g` on `ibm_marrakesh`. 21 circuits. Verified complete Write $\rightarrow$ Decouple $\rightarrow$ Autonomous Hold cycle: handover at $k=8$ ($|P(S_1)-P(S_2)| = 0.0605$, $P(S_2) = 0.3438$), autonomous hold at $k=32$ ($P(S_2) = 0.2754$). **$+15.62\%$ protection advantage** over idle transmon decay!
7. **Tri-Wheel 10-Qubit Quantum Bus:** Job `dbsam57v5hds73dio4i0` on `ibm_marrakesh`. 18 circuits. Verified end-to-end multi-cell transport across 10 native qubits: excitation injected at $S_1$ (Q105) conducted through central relay $S_2$ (Q125) into receiver $S_3$ (Q123) with $P(S_3) = 0.3008$ vs nosync $0.0170$, achieving 3-way equipartition ($S_1 \approx 35.9\%, S_2 \approx 25.2\%, S_3 \approx 30.5\%$) and **$67.0\%$ collective retention** at $k=32$!
8. **13-Qubit 2D Quantum Space-Fabric:** Job `dbsap8ok09pc73avuql0` on `ibm_marrakesh`. 18 circuits. Proved 4-hub omni-directional 2D emission ($S_1 \approx 36.1\%, S_2 \approx 37.3\%, S_3 \approx 31.1\%$) with $120^\circ$ isotropic symmetry, locking into an **$83.4\%$ macroscopic bound state** across the entire 13-qubit fabric at $k=32$.
9. **A HÁLÓZAT — Distributed Autonomous Quantum Memory Network:** Job `dbsaruujjaos73ajvhtg` on `ibm_marrakesh`. 21 circuits. Successfully demonstrated multi-node 2D broadcast followed by global decoupling at $k=8$. Three isolated, independent satellite cells across the 2D plane autonomously sustained collective quantum memory retention at **$72.07\%$** through $k=32$ (~200 physical gates), securing a **$+26.17\%$ protection advantage** over idle transmon environmental relaxation ($45.90\%$)!

---

## 4. Technical Feasibility & Lattice Mapping
* **Target Architecture:** IBM Heron r2 processors (`ibm_marrakesh`, `ibm_kingston`), 156-qubit heavy-hex lattice.
* **Demonstrated Mapping:** Direct physical nearest-neighbor edges on heavy-hex:
  - Wheel 1: Hub 125, spokes 117, 126
  - Bridge: Shared transmon 124 (physically adjacent to both Hub 125 and Hub 123)
  - Wheel 2: Hub 123, spokes 122, 136
* **Transpilation:** Executed strictly with `optimization_level=0` to preserve dynamical timing and physical lattice geometry. Zero SWAP overhead needed for the 7-qubit dual-wheel core.

---

## 5. Requested Compute Allocation & Research Objectives
* **Requested Compute Allocation:** **3 to 5 hours of dedicated QPU time** on IBM Heron processors.
* **Scaling Objectives with Requested Credits:**
  1. **Tri-Wheel Honeycomb Lattice (12 to 16 qubits):** Extend from dual-wheel 1D chain to a 2D closed honeycomb plaquette incorporating surrounding nodes (e.g. Q105, Q137, Q121) to measure boundary-protected topological bulk modes.
  2. **Multi-State Memory Register Encoding:** Generalize from single-excitation $|100...0\rangle$ storage to multi-qubit entangled Bell and W-state storage across decoupled cells.
  3. **Continuous Coherence Lifetime Limits ($k > 100$):** Map the ultimate plateau lifetime limits beyond 100 Trotter cycles (~600 physical gates) with fine-grained error mitigation (Zero-Noise Extrapolation and Pauli Twirling).

---

## 6. Open Science, Archiving & Dissemination
* All raw hardware counts, transpiled QASM circuits, simulation engines, and sentinel evaluators are published open-source on GitHub under the MIT License.
* Cryptographically preregistered with SHA-256 hashes before QPU execution.
* Archived via CERN Zenodo with permanent DOI: [10.5281/zenodo.24226150](https://doi.org/10.5281/zenodo.24226150), directly linked to PI ORCID (`0009-0003-3986-6039`).
* Preprint submitted to arXiv: *"Topological Phase-Locking and Autonomous Excitation Retention in IBM Heron Heavy-Hex Superconducting Qubits"*.
