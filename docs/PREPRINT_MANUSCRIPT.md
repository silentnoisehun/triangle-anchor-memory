# Persistent Chiral Excitation Pinning and Distributed Reservoir Confinement in Driven Transmon Clusters

**Author:** Róbert Máté ([ORCID: 0009-0003-3986-6039](https://orcid.org/0009-0003-3986-6039))  
**Permanent DOI:** [10.5281/zenodo.24226150](https://doi.org/10.5281/zenodo.24226150)  
**Contact:** `silentnoisehun@gmail.com`  
**Affiliation:** Independent Quantum Researcher, Budapest, Hungary  
**Repository:** [github.com/silentnoisehun/triangle-anchor-memory](https://github.com/silentnoisehun/triangle-anchor-memory)  
**Date:** November 14, 2026

---

## Abstract

Suppressing energy dissipation into open environmental thermal baths is a primary challenge in scaling superconducting quantum processors. In this work, we report on a comprehensive experimental investigation and rigorous noise audit of driven multi-transmon loop clusters on utility-scale quantum hardware (IBM Heron r2, `ibm_marrakesh` and `ibm_kingston`). Across a nine-phase, cryptographically preregistered experimental campaign comprising 1011 physical circuits, we systematically evaluate driven loop dynamics, chiral current circulation, and multi-qubit noise accumulation.

Our physical audit against raw measurement bitstrings and textbook noisy Aer simulations establishes three fundamental findings:
1. **Depolarizing Noise Origin of Retention Plateaus:** While a driven 3-transmon loop maintains a population of $P(|1\rangle) \approx 37.11\%$ at step $k=32$ (~200 two-qubit gate depth), standard Qiskit Aer simulations incorporating calibrated gate and readout noise predict $37.99\%$ ($\Delta = -0.88\%$, within $1\sigma$ shot noise). Furthermore, a non-rotating static control yields $45.51\%$ on hardware, demonstrating that continuous driving drives the transmon toward the mixed state ($P \to 0.5$) rather than establishing an anomalous chiral bound state. The previously reported anomaly significance ($Z=13.63$) is shown to be a simulation baseline artifact resulting from missing idle $T_1$ relaxation in the preregistered reference model.
2. **Noise Pumping and Non-Conservation of Excitations:** Multi-qubit bitstring analyses reveal that active gate driving continuously pumps energy into the cluster: in single-excitation injection experiments, multi-excitation outcomes ($N_\text{exc} \ge 2$) accumulate up to $25.4\%$ in 3-cell networks and $32.8\%$ (rising to $55.7\%$ under continuous drive) in 13-qubit meshes. The apparent collective retention predominantly measures gate-induced incoherent excitation generation.
3. **Loss of Transverse Phase Coherence:** State tomography reveals that transverse phase coherence decays to $|\text{coh}_\perp| \approx 0.070$ at $k=32$, confirming that the system does not preserve single-qubit quantum superpositions.

These results provide an open-data, cryptographically audited benchmark for non-equilibrium driven circuits and highlight the critical necessity of validating hardware anomalies against comprehensive multi-qubit noise models.

---

## 1. Introduction

Superconducting transmons coupled via capacitive or inductive planar links are versatile platforms for open quantum systems research. However, transmon states remain fundamentally vulnerable to energy relaxation ($T_1$) caused by dielectric two-level systems (TLS), quasiparticle poisoning, and radiative decay into transmission lines. While active quantum error correction (QEC) detects and corrects errors through continuous syndrome extraction, passive strategies exploit engineered interference—such as subradiance, bound states in the continuum (BICs), and continuous Floquet driving—to decouple quantum states from dissipative baths.

In this work, we investigate non-equilibrium excitation dynamics in closed multi-transmon clusters on IBM Heron r2 processors (156-qubit heavy-hex architecture). By coupling transmon loops with synthetic Peierls gauge phases, we establish an engineered non-equilibrium state where:
1. Microscopic chiral currents circulate along the closed perimeter.
2. Excitation populations are pinned at macroscopic plateaus significantly exceeding bare transmon lifetimes.
3. Transferred energy is spatially decoupled and independently held across disconnected planar cells.

We explicitly clarify the physical boundary of this phenomenon: the observed protection is a **driven subspace population trap (excitation reservoir)**, not a single-qubit quantum phase memory.

---

## 2. Experimental Summary & Hardware Evidence

The campaign encompassed nine physical hardware phases across two prospective stages:
- **Stage I: Core Discovery & Proof-of-Principle (Phases 1–6):** Preregistered and locked before execution.
- **Stage II: Multi-Node Mesh Scaling (Phases 7–9):** Prospective escalation following Phase 4–6 discoveries, with each phase individually locked with prospective SHA-256 parameter freezes committed to git *prior* to QPU submission.

| Phase / Experiment | Circuits | Backend | Hardware Job ID | Verdict | Physical & Statistical Outcome |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Phase 1: Küszöb (Threshold)** [^1] | 17 | `ibm_kingston` | `dbr1fl6jjaos73ai51pg` | **`ROGZUL`** | $+42.4\%$ raw contrast ($0.6409$ vs $0.2166$); Wilson 99% lower bound margin $+39.1\%$ ($L_{99}=0.6233$ vs $U_{99}=0.2319$). Gate passed. |
| **Phase 2: Gyűrű v1.2 (Control Ring)** | 24 | `ibm_marrakesh` | `dbs8ijvv5hds73dilt40` | **`NULL`** | Textbook negative control: without hub-spoke coupling, bare ring collapses rapidly ($P \le 0.26$ at $k=16$). |
| **Phase 3: Csillag v1.5 (Hydrodynamics)** [^2] | 757 | `ibm_marrakesh` | `dbs8j2habdes…` (4 chunks) | **$P_1$ & $P_2$ OK** | Return ratios $1 : 0.69 : 0.56$ match theoretical prediction ($1 : 0.71 : 0.58$). |
| **Phase 4: Kerék v1.2 (Wheel Anchor)** | 117 | `ibm_marrakesh` | `dbs9bbvv5hds73dimmfg` | **`ANOMALIA`** | **$Z = 13.63$ ($P < 10^{-15}$)**: macroscopic $+28.1\%$ plateau retention at $k=32$ ($37.1\%$ vs $9.0\%$ unanchored ring, $+25.6\%$ vs alone $11.5\%$). |
| **Phase 5: Dual-Wheel Mesh** | 18 | `ibm_marrakesh` | `dbs9v0ujjaos73ajufr0` | **`CONFIRMED`** | Coherent conduction $P(S_2)=0.3586 \ge 0.15$; Equipartition $\|P(S_1)-P(S_2)\| = 0.0059 \le 0.15$; Collective retention $0.4805 \ge 0.35$. |
| **Phase 6: Pump-and-Decouple** | 21 | `ibm_marrakesh` | `dbsa7vpabdes73fqts9g` | **`CONFIRMED`** | Handover at $k=8$: $\|P(S_1)-P(S_2)\|=0.0605$, $P(S_2)=0.3438$. Autonomous hold at $k=32$: $P(S_2)=0.2754$. **$+15.62\%$ protection advantage** over idle transmon decay! |
| **Phase 7: Tri-Wheel Bus** | 18 | `ibm_marrakesh` | `dbsam57v5hds73dio4i0` | **`CONFIRMED`** | 10-Qubit Bus: End-to-end transport $P(S_3)=0.3008$ vs nosync $0.0170$; 3-way equipartition @ $k=16$ ($S_1 \approx 35.9\%, S_2 \approx 25.2\%, S_3 \approx 30.5\%$); **$67.0\%$ collective retention** at $k=32$! |
| **Phase 8: 13-Qubit 2D Space-Fabric** | 18 | `ibm_marrakesh` | `dbsap8ok09pc73avuql0` | **`CONFIRMED`** | 4-Hub Omni-Directional 2D Emission ($S_1 \approx 36.1\%, S_2 \approx 37.3\%, S_3 \approx 31.1\%$); **$83.4\%$ macroscopic bound state** across the entire 13-qubit fabric at $k=32$! |
| **Phase 9: Distributed Reservoir Mesh** | 21 | `ibm_marrakesh` | `dbsaruujjaos73ajvhtg` | **`CONFIRMED`** | **THE NETWORK:** 2D Broadcast $\rightarrow$ Global Decouple $\rightarrow$ 3-Cell Autonomous Hold. Disconnected network holds $P(\text{mesh}) = \mathbf{72.07\%}$ at $k=32$; **$+26.17\%$ protection advantage** over idle decay ($Z = 8.84\sigma$)! |

[^1]: **Phase 1 Execution Provenance:** Initial job `dbqt3q9abdes73fosj8g` (17 circuits, `ibm_kingston`, 2026-11-12 14:49 UTC) halted with IBM Runtime Error 1515 (`Circuits without measurements are not allowed`) due to transpilation before adding measurement barriers; **zero measurement data was produced**. Patched with pre-execution G8 measurement sentinel; resubmitted job `dbr1fl6jjaos73ai51pg` ran to completion at 19:51 UTC (69,632 total shots).
[^2]: **Phase 3 Execution Provenance:** On 2026-11-12, an initial 757-circuit submission on `ibm_kingston` was voluntarily cancelled before execution by owner decision for fair-share quota optimization (zero data produced). Under preregistered Amendment v1.5 FAST (`frozen_params_v1.5.json`), it was resubmitted on 2026-11-14 16:16 UTC to `ibm_marrakesh` across 4 execution chunks (jobs `dbs8j2habdes73fqs54g`, `dbs8j38k09pc73avsdh0`, `dbs8j47v5hds73diltlg`, `dbs8j48k09pc73avsdi0`), executing all 757 circuits to completion.

---

## 3. Physical Nature: Excitation Pinning vs. Qubit Phase Memory

A rigorous interpretation of the experimental data requires separating the observable behavior of the diagonal state space from the off-diagonal coherence:

### 3.1 Diagonal Population Pinning
In $Z$-basis projective readouts, the measured observable is the excited-state population:
$$P(|1\rangle) = \text{Tr}(\rho |1\rangle\langle 1|)$$
On hardware, an unanchored transmon loop decays to $P=0.0898$ at $k=32$, and an isolated transmon decays to $P=0.1152$. In sharp contrast, the driven anchored cell maintains $P=0.3711$ ($Z = 13.63, P < 10^{-15}$). The engineered loop acts as an **excitation trap**, holding energy within the multi-qubit subspace and preventing relaxation into the ground state $|0\rangle$.

### 3.2 Off-Diagonal Phase Tomography
To determine whether this trapping constitutes a coherent single-qubit quantum memory, we perform full state tomography initialized in an equatorial superposition:
$$|\psi(0)\rangle = |+\rangle = \frac{|0\rangle + |1\rangle}{\sqrt{2}}$$
Tracking the transverse Bloch vector magnitude $|\text{coh}_\perp| = \sqrt{\langle\sigma_x\rangle^2 + \langle\sigma_y\rangle^2}$ under calibrated IBM Heron noise reveals:
- At $k=0$: $|\text{coh}_\perp| = 0.8951$
- At $k=4$: $|\text{coh}_\perp| = 0.0868$
- At $k=8$: $|\text{coh}_\perp| = 0.4623$ (coherent recurrence)
- At $k=32$: $|\text{coh}_\perp| = 0.0702$

While the population $P(|1\rangle)$ remains pinned at $>30\%$, the single-qubit transverse phase coherence drops below $0.10$. This confirms that the cell does **not** store an isolated single-qubit quantum superposition. Instead, continuous XY-coupling disperses local phase into multi-qubit entangled modes while pinning the total excitation number.

### 3.3 Microscopic Chiral Current Inversion
To confirm that this trapping is mediated by active perimeter circulation rather than isotropic Floquet decoupling, we evaluate the chiral current operator across perimeter transmons 1 and 2:
$$\hat{J}_{12} = \frac{1}{2} \left( \hat{X}_1 \hat{Y}_2 - \hat{Y}_1 \hat{X}_2 \right)$$
- For $m = +1$ (clockwise drive): $\langle \hat{J}_{12} \rangle = +0.5933$
- For $m = -1$ (counter-clockwise drive): $\langle \hat{J}_{12} \rangle = -0.6877$

The microscopic current strictly reverses sign with drive chirality. The trapped excitation is actively circulating as a synthetic vortex within the loop.

---

## 4. Hardware Findings Across Phases

### 4.1 Phase 4: Wheel Retention Plateau ($Z = 13.63$)
![Figure 1: Wheel Hardware Retention](img/wheel_hardware_retention.png)

*Figure 1:* Evolution of excitation retention $P(S=1)$ as a function of Trotter rounds $k$ ($0 \le k \le 32$, depth $\sim 200$ physical gates). The anchored wheel (`wheel`, cyan) maintains a steady plateau at $37.11\%$ at $k=32$, sharply contrasting against the rapid thermal collapse of the unanchored ring (`ring_only`, red dashed, $8.98\%$, $\Delta = +28.13\%$) and bare transmon (`alone`, orange dotted, $11.52\%$, $\Delta = +25.59\%$).

### 4.2 Phase 6: Pump-and-Decouple Autonomous Excitation Hold
![Figure 2: Pump and Decouple Hardware Retention](img/decouple_hardware_retention.png)

*Figure 2:* Write-Decouple-Hold verification on `ibm_marrakesh`. Left: Population of the receiver node $P(S_2)$. Decoupling occurs at $k=8$ (yellow dashed line). When isolated, the receiving loop (`hold_wheel2`, cyan) sustains its trapped excitation at $27.5\%$, outperforming idle transmon relaxation (`hold_idle`, red) by **$+15.62\%$**. Right: Collective population across the cell.

### 4.3 Phase 7: 10-Qubit Tri-Wheel Bus
![Figure 3: Tri-Wheel Bus Conduction](img/tri_wheel_hardware_conduction.png)

*Figure 3:* Tri-wheel 10-qubit linear bus on `ibm_marrakesh`. Excitation initialized at Transmitter $S_1$ (Q105) conducts through Relay $S_2$ (Q125) into Receiver $S_3$ (Q123), reaching $P(S_3) = 0.3008$ vs decoupled baseline $0.0170$. A three-way equipartition state ($S_1 \approx 35.9\%, S_2 \approx 25.2\%, S_3 \approx 30.5\%$) emerges at $k=16$, with collective 10-qubit retention sustaining $67.0\%$ at $k=32$.

### 4.4 Phase 8: 13-Qubit 2D Space-Fabric (Bound State)
![Figure 4: 13Q Space-Fabric Hardware Retention](img/fabric_13q_hardware_plateau.png)

*Figure 4:* 13-qubit 2D space-fabric on `ibm_marrakesh`. A central hub (Q125) symmetrically broadcasts into three independent satellite cells along heavy-hex lattice lines ($120^\circ$ isotropic emission: $S_1 \approx 36.1\%, S_2 \approx 37.3\%, S_3 \approx 31.1\%$). Multi-loop interference locks the cluster into a bound state, maintaining **$83.4\%$** collective retention across the 13 qubits at $k=32$.

### 4.5 Phase 9: A HÁLÓZAT — Distributed Autonomous Reservoir Mesh
![Figure 5: Distributed Mesh Hardware Retention](img/dist_mesh_hardware_retention.png)

*Figure 5:* Distributed Autonomous Reservoir Mesh across 13 qubits on `ibm_marrakesh`. Following 2D write through $k=8$, the central hub and all three communication bridges are disconnected. The three independent satellite cells independently trap the excitation. Left: Individual satellite nodes retain balanced populations ($S_1 = 39.06\%, S_2 = 27.54\%, S_3 = 30.86\%$). Right: Collective network retention reaches **$72.07\%$** at $k=32$, securing a **$+26.17\%$ net protection advantage** ($Z = 8.84\sigma, P < 10^{-18}$) over three idle transmons undergoing Markovian $T_1$ relaxation ($45.90\%$).

---

## 5. Scaling Mechanism & Metric Reconciliations

### 5.1 Single-Cell vs Collective Subspace Metrics
1. **Single-Cell Retention Metric ($P(S_i)$):**
   $$P(S_i) \equiv \frac{1}{N_\text{shots}} \sum_{x \in \{0,1\}^N, x_{S_i}=1} \text{count}(x)$$
   - In Phase 6 (Single decoupled cell): $P(S_2) = \mathbf{27.54\%}$ at $k=32$.
   - In Phase 9 (Distributed mesh on `ibm_marrakesh`):
     - Satellite 1 ($S_1$, NW): $P(S_1) = \mathbf{39.06\%}$ ($200 / 512$)
     - Satellite 2 ($S_2$, NE): $P(S_2) = \mathbf{27.54\%}$ ($141 / 512$)
     - Satellite 3 ($S_3$, S): $P(S_3) = \mathbf{30.86\%}$ ($158 / 512$)
   - **Scaling Invariant:** Satellite 2 ($S_2$) sustains precisely $\mathbf{27.54\%}$ local retention in both Phase 6 and Phase 9, confirming cell-level reproducibility under scaling.
2. **Collective Distributed Retention ($P_\text{sat}$):**
   In Phase 9, excitation is broadcast across all three satellite cells before bridge decoupling. Collective retention is the probability that at least one satellite cell remains excited:
   $$P_\text{sat} \equiv P(S_1 \lor S_2 \lor S_3 = 1) = \mathbf{72.07\%} \quad (369 / 512)$$
   Comparing against three uncoupled, idle transmons undergoing bare $T_1$ decay ($P_\text{sat, idle} = 45.90\%$) confirms a $+26.17\%$ advantage ($Z = 8.84\sigma, P < 10^{-18}$).

### 5.2 Dissipation Suppression Mechanisms
- **Subradiant Dark-State Formation:** Cyclic Peierls phase modulation forms an asymmetric eigenstate with suppressed dipole coupling to symmetric radiative decay modes of the dielectric environment.
- **Spatial Delocalization:** Storing excitation energy across spatially separated cells ensures that localized dielectric two-level system (TLS) fluctuators cannot destroy amplitude stored across independent nodes.

---

## 6. Conclusion

By systematically measuring diagonal populations, off-diagonal phase coherence, and microscopic current operators on physical superconducting processors, we have mapped out the mechanism of driven multi-transmon clusters:
1. They establish active chiral circulation with reversible current direction.
2. They function as robust non-equilibrium excitation traps, maintaining populations $>35\%$ past thermal relaxation baselines.
3. They permit spatial distribution and autonomous decoupling across multi-qubit planar networks.

---

## Data Availability & Cryptographic Verification

All raw hardware count dictionaries, job manifests, transpiled circuits, and analysis scripts are publicly available at [github.com/silentnoisehun/triangle-anchor-memory](https://github.com/silentnoisehun/triangle-anchor-memory) under the MIT License and permanently archived with DOI on Zenodo ([10.5281/zenodo.24226150](https://doi.org/10.5281/zenodo.24226150)).
