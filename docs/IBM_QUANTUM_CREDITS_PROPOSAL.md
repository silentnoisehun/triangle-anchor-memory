# Research Proposal: IBM Quantum Credits Program

## 1. Project Title
**Persistent Chiral Excitation Pinning and Distributed Reservoir Confinement on IBM Heron Processors**

---

## 2. Principal Investigator & Affiliation
* **Name:** Róbert Máté
* **ORCID:** [0009-0003-3986-6039](https://orcid.org/0009-0003-3986-6039)
* **GitHub Repository:** [https://github.com/silentnoisehun/triangle-anchor-memory](https://github.com/silentnoisehun/triangle-anchor-memory)
* **Status:** Independent Quantum Researcher / Quantum Systems Architect

---

## 3. Executive Summary & Hardware Breakthroughs

Superconducting transmon quantum processors operating in dissipative open environments suffer from local Markovian energy relaxation ($T_1$) and dephasing ($T_2^*$). Traditional active quantum error correction (QEC) requires substantial physical qubit overhead and continuous syndrome measurement backaction.

In this preregistered experimental research project, we designed, simulated, and physically demonstrated **chiral excitation pinning and non-equilibrium reservoir confinement** on utility-scale superconducting processors (IBM Heron r2, `ibm_marrakesh` and `ibm_kingston`) across **1011 physical circuits**. By coupling transmon clusters symmetrically to perimeter anchors under calibrated Peierls phase modulation, we engineered continuous destructive interference into radiative bath modes, trapping excitation energy within multi-qubit subspaces.

### Hardware-Confirmed Results on IBM Heron r2:
Across 9 physical hardware phases organized into Stage I (Core Discovery, Phases 1--6) and Stage II (Mesh Scaling, Phases 7--9), with all quantitative decision boundaries cryptographically locked via prospective SHA-256 parameter freezes:

1. **Threshold Phase Lock (Küszöb v1.3):** Job `dbr1fl6jjaos73ai51pg` on `ibm_kingston`. **`ROGZUL`** (+42.4% raw contrast, Wilson 99% lower bound margin +39.1% with $L_{99} \ge 0.50$). Machine qualification gate passed.
2. **Negative Control (Gyűrű v1.2):** Job `dbs8ijvv5hds73dilt40` on `ibm_marrakesh`. 24 circuits, confirmed **`NULL`** (unanchored ring undergoes rapid thermal decay, ruling out false-positive artifacts).
3. **Open Hydrodynamic Star (Csillag v1.5 FAST):** 4 chunks on `ibm_marrakesh`. 757 circuits, verified return time scaling ratios $P_1$ ($1 : 0.69 : 0.56$ vs predicted $1 : 0.71 : 0.58$) and non-Markovian memory recurrence.
4. **Closed-Loop Wheel (Kerék v1.2):** Job `dbs9bbvv5hds73dimmfg` on `ibm_marrakesh`. 117 circuits, **ANOMALOUS EXCITATION PINNING CONFIRMED ($Z = 13.63$, $P < 10^{-15}$)**. Sustained macroscopic $37.1\%$ excitation retention plateau at $k=32$ Trotter steps vs $8.98\%$ collapse on unanchored rings ($\Delta = +28.1\%$, and $+25.6\%$ vs bare transmon $11.5\%$).
5. **Dual-Wheel Synchronous Mesh:** Job `dbs9v0ujjaos73ajufr0` on `ibm_marrakesh`. 7-qubit cluster (Q125, Q117, Q126, Q124, Q123, Q122, Q136). Confirmed inter-cell quantum conduction ($P(S_2) = 0.3586 \ge 0.15$), Kuramoto-Huygens equipartition ($|P(S_1) - P(S_2)| = 0.0059 \le 0.15$), and collective network retention ($0.4805 \ge 0.35$).
6. **Pump-and-Decouple Autonomous Hold:** Job `dbsa7vpabdes73fqts9g` on `ibm_marrakesh`. 21 circuits. Verified complete Write $\rightarrow$ Decouple $\rightarrow$ Autonomous Hold cycle: handover at $k=8$ ($|P(S_1)-P(S_2)| = 0.0605$, $P(S_2) = 0.3438$), autonomous hold at $k=32$ ($P(S_2) = 0.2754$). **$+15.62\%$ protection advantage** over idle transmon decay!
7. **Tri-Wheel 10-Qubit Bus:** Job `dbsam57v5hds73dio4i0` on `ibm_marrakesh`. 18 circuits. Verified end-to-end multi-cell transport across 10 native qubits: excitation injected at $S_1$ (Q105) conducted through central relay $S_2$ (Q125) into receiver $S_3$ (Q123) with $P(S_3) = 0.3008$ vs nosync $0.0170$, achieving 3-way equipartition ($S_1 \approx 35.9\%, S_2 \approx 25.2\%, S_3 \approx 30.5\%$) and **$67.0\%$ collective retention** at $k=32$!
8. **13-Qubit 2D Space-Fabric:** Job `dbsap8ok09pc73avuql0` on `ibm_marrakesh`. 18 circuits. Proved 4-hub omni-directional 2D emission ($S_1 \approx 36.1\%, S_2 \approx 37.3\%, S_3 \approx 31.1\%$) with $120^\circ$ isotropic symmetry, locking into an **$83.4\%$ macroscopic bound state** across the entire 13-qubit fabric at $k=32$.
9. **A HÁLÓZAT — Distributed Autonomous Reservoir Mesh:** Job `dbsaruujjaos73ajvhtg` on `ibm_marrakesh`. 21 circuits. Demonstrated multi-node 2D broadcast followed by global decoupling at $k=8$. Three isolated satellite cells across the 2D plane autonomously sustained collective excitation retention at **$72.07\%$** through $k=32$ (~200 physical gates), securing a **$+26.17\%$ protection advantage** over idle transmon environmental relaxation ($45.90\%$)!

---

## 4. Technical Feasibility & Zero-SWAP Lattice Mapping
* **Target Architecture:** IBM Heron r2 processors (`ibm_marrakesh`, `ibm_kingston`), 156-qubit heavy-hex lattice.
* **Demonstrated Mapping:** Direct physical nearest-neighbor links on heavy-hex:
  - Wheel 1: Hub 125, spokes 117, 126
  - Bridge: Shared transmon 124 (physically adjacent to both Hub 125 and Hub 123)
  - Wheel 2: Hub 123, spokes 122, 136
* **Transpilation:** Executed strictly with `optimization_level=0` to preserve dynamical timing and physical lattice geometry. Zero SWAP overhead for the entire 13-qubit cluster.

---

## 5. Requested Compute Allocation & Research Objectives
* **Requested Compute Allocation:** **3 to 5 hours of dedicated QPU time** on IBM Heron processors.
* **Scaling Objectives with Requested Credits:**
  1. **Full Quantum State Tomography Across Disconnected Nodes:** Map the multi-qubit density matrix of the decoupled satellite nodes to quantify entanglement entropy and decoherence-free subspace (DFS) encoding efficiency.
  2. **Multi-Plaquette Honeycomb Lattice Scaling (16 to 24 qubits):** Extend from a 13-qubit cluster to multi-cell planar meshes to test scaling laws of subradiant dissipation suppression.
  3. **Extended Lifetime Bounds ($k > 100$ cycles):** Test plateau stability beyond 100 Trotter cycles (~600 physical gates) with randomized compiling and dynamical decoupling (DD) pulse interleaving.

---

## 6. Open Science, Archiving & Dissemination
* All raw hardware counts, transpiled QASM circuits, simulation engines, and sentinel evaluators are published open-source on GitHub under the MIT License.
* Cryptographically preregistered with SHA-256 hashes before QPU execution.
* Archived via CERN Zenodo with permanent DOI: [10.5281/zenodo.24226150](https://doi.org/10.5281/zenodo.24226150), directly linked to PI ORCID (`0009-0003-3986-6039`).
* Preprint submitted: *"Persistent Chiral Excitation Pinning and Distributed Reservoir Confinement in Driven Transmon Clusters"*.
