# Topological Phase-Locking and Autonomous Excitation Retention in IBM Heron Heavy-Hex Superconducting Qubits

**Author:** Róbert Máté ([ORCID: 0009-0003-3986-6039](https://orcid.org/0009-0003-3986-6039))  
**Permanent DOI:** [10.5281/zenodo.24226150](https://doi.org/10.5281/zenodo.24226150)  
**Contact:** `silentnoisehun@gmail.com`  
**Affiliation:** Independent Quantum Researcher, Budapest, Hungary  
**Repository:** [github.com/silentnoisehun/triangle-anchor-memory](https://github.com/silentnoisehun/triangle-anchor-memory)  
**Date:** November 14, 2026

---

## Abstract

Preserving quantum coherence against dissipative decay without the active syndrome extraction overhead of quantum error correction (QEC) is a central challenge in scalable quantum technology. Here, we demonstrate topological phase-locking, coherent excitation trapping, and distributed autonomous quantum memory on utility-scale superconducting quantum processors (IBM Heron r2, `ibm_marrakesh` and `ibm_kingston`). Across a nine-phase, cryptographically preregistered experimental campaign structured into two prospective stages (Stage I: Core Discovery, Phases 1–6; Stage II: Mesh Scaling, Phases 7–9; each locked with prospective SHA-256 parameter commitments prior to QPU execution), we establish that a closed-loop wheel topology stabilizes an excitation plateau at $\sim 37\%$ over 32 Trotter steps ($\sim 200$ physical two-qubit gates), exhibiting anomalous retention with statistical significance $Z = 13.63$ ($P < 10^{-15}$) relative to unanchored ring controls. Extending this to a seven-qubit dual-wheel mesh, we demonstrate inter-cell Kuramoto-Huygens synchronization and directional conduction ($P(S_2) = 0.3586$, $|P(S_1) - P(S_2)| = 0.0059$). Executing a complete quantum DRAM cycle (Write $\rightarrow$ Decouple $\rightarrow$ Hold), we physically decouple the communication bridge at $k=8$; the isolated receiving wheel autonomously retains its excitation state ($P(S_2) = 0.2754$ at $k=32$), demonstrating a **$+15.62\%$ protection advantage** over bare transmon environmental relaxation ($11.91\%$). Scaling this principle to a 13-qubit 2D lattice on `ibm_marrakesh`, we demonstrate omni-directional 3-way broadcast, followed by global decoupling of the central hub and bridges at $k=8$. The three completely disconnected satellite cells independently store the distributed excitation, sustaining a collective network retention of **$72.07\%$** through $k=32$ ($\mathbf{+26.17\%}$ net advantage over uncoupled idle decay, $Z = 8.84\sigma$). These findings establish a rigorous experimental foundation for passive, topology-protected distributed quantum memories on planar superconducting architectures.

---

## 1. Introduction

Superconducting transmons are leading physical building blocks for scalable quantum computing. However, open quantum systems remain fundamentally limited by local Markovian energy relaxation ($T_1$) and dephasing ($T_2^*$). Standard active quantum error correction incurs substantial qubit overhead, continuous syndrome measurement backaction, and complex classical decoding latency.

Alternative paradigms inspired by non-Hermitian photonics and topological physics exploit bound states in the continuum (BICs) and collective interference phenomena such as subradiance and synchronization. If destructive interference suppresses radiation into the dissipative environment while constructive phase interference refocuses quantum amplitudes at protected lattice nodes, coherent states can be dynamically trapped.

In this work, we experimentally demonstrate this principle on physical IBM Heron r2 superconducting processors arranged in a 156-qubit heavy-hex lattice. Through a prospective sequence of nine experimental phases, we confirm:
1. Machine qualification thresholds (`ROGZUL`),
2. Unanchored ring decay baselines (`NULL`),
3. Hydrodynamic recurrence scaling ($P_1, P_2$),
4. Anomalous wheel excitation retention ($Z = 13.63, P < 10^{-15}$),
5. Dual-cell synchronization ($|P(S_1) - P(S_2)| = 0.0059$),
6. Autonomous single-cell memory retention after physical channel decoupling ($\Delta = +15.62\%$),
7. Tri-wheel 10-qubit ballistic bus transport and 3-way synchronization ($P(S_3) = 0.3008$),
8. 13-qubit 2D space-fabric isotropic emission and macroscopic BIC bound state ($83.4\%$),
9. Distributed autonomous quantum memory mesh with global decoupling ($72.07\%$ collective hold, $+26.17\%$ advantage vs idle decay).

---

## 2. Experimental Summary & Hardware Evidence

The nine experimental phases were organized into two prospective stages:
- **Stage I: Core Discovery & Proof-of-Principle (Phases 1–6):** Initially formulated and preregistered before any QPU submission.
- **Stage II: Multi-Node Topological Mesh Scaling (Phases 7–9):** Formulated as a prospective escalation following the Phase 4–6 discoveries, with each phase individually locked with prospective SHA-256 parameter freezes committed to git *prior* to its QPU submission.

| Phase / Experiment | Circuits | Backend | Hardware Job ID | Verdict | Physical & Statistical Outcome |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Phase 1: Küszöb (Threshold)** [^1] | 17 | `ibm_kingston` | `dbr1fl6jjaos73ai51pg` | **`ROGZUL`** | $+39.1\%$ excitation retention with 3-anchor ($P > 0.64$ vs $0.21$). Hardware health gate passed. |
| **Phase 2: Gyűrű v1.2 (Control Ring)** | 24 | `ibm_marrakesh` | `dbs8ijvv5hds73dilt40` | **`NULL`** | Textbook negative control: without hub-spoke coupling, bare ring collapses rapidly. |
| **Phase 3: Csillag v1.5 (Hydrodynamics)** [^2] | 757 | `ibm_marrakesh` | `dbs8j2habdes…` (4 chunks) | **$P_1$ & $P_2$ OK** | Return ratios $1 : 0.69 : 0.56$ match theoretical prediction ($1 : 0.71 : 0.58$). |
| **Phase 4: Kerék v1.2 (Wheel Anchor)** | 117 | `ibm_marrakesh` | `dbs9bbvv5hds73dimmfg` | **`ANOMALIA`** | **$Z = 13.63$ ($P < 10^{-15}$)**: macroscopic $+42.1\%$ plateau retention at $k=32$ vs unanchored ring. |
| **Phase 5: Dual-Wheel Mesh** | 18 | `ibm_marrakesh` | `dbs9v0ujjaos73ajufr0` | **`CONFIRMED`** | Coherent conduction $P(S_2)=0.3586 \ge 0.15$; Equipartition $\|P(S_1)-P(S_2)\| = 0.0059 \le 0.15$; Collective retention $0.4805 \ge 0.35$. |
| **Phase 6: Pump-and-Decouple (DRAM)** | 21 | `ibm_marrakesh` | `dbsa7vpabdes73fqts9g` | **`CONFIRMED`** | Handover at $k=8$ verified; Autonomous hold at $k=32$: $P(S_2)=0.2754$. **$+15.62\%$ protection advantage** over idle transmon decay! |
| **Phase 7: Tri-Wheel 10-Qubit Bus** | 18 | `ibm_marrakesh` | `dbsam57v5hds73dio4i0` | **`CONFIRMED`** | End-to-end multi-cell transport $P(S_3)=0.3008$; 3-way equipartition ($S_1 \approx 35.9\%, S_2 \approx 25.2\%, S_3 \approx 30.5\%$); **$67.0\%$ collective retention** at $k=32$! |
| **Phase 8: 13-Qubit 2D Space-Fabric** | 18 | `ibm_marrakesh` | `dbsap8ok09pc73avuql0` | **`CONFIRMED`** | 4-Hub Omni-Directional 2D Emission ($S_1 \approx 36.1\%, S_2 \approx 37.3\%, S_3 \approx 31.1\%$); **$83.4\%$ macroscopic bound state** across the entire 13-qubit fabric at $k=32$! |
| **Phase 9: Distributed Autonomous Mesh** | 21 | `ibm_marrakesh` | `dbsaruujjaos73ajvhtg` | **`CONFIRMED`** | **A HÁLÓZAT:** Write (2D Broadcast) $\rightarrow$ Global Decouple $\rightarrow$ 3-Cell Autonomous Hold. Disconnected network holds $P(\text{mesh}) = \mathbf{72.07\%}$ at $k=32$; **$+26.17\%$ protection advantage** over idle decay ($Z = 8.84\sigma$)! |

[^1]: **Phase 1 Execution Provenance:** Initial job `dbqt3q9abdes73fosj8g` (17 circuits, `ibm_kingston`, 2026-11-12 14:49 UTC) halted with IBM Runtime Error 1515 (`Circuits without measurements are not allowed`) due to transpilation before adding measurement barriers; **zero measurement data was produced**. Patched with pre-execution G8 measurement sentinel; resubmitted job `dbr1fl6jjaos73ai51pg` ran to completion at 19:51 UTC (69,632 total shots).
[^2]: **Phase 3 Execution Provenance:** On 2026-11-12, an initial 757-circuit submission on `ibm_kingston` was voluntarily cancelled before execution by owner decision for fair-share quota optimization (zero data produced). Under preregistered Amendment v1.5 FAST (`frozen_params_v1.5.json`), it was resubmitted on 2026-11-14 16:16 UTC to `ibm_marrakesh` across 4 execution chunks (jobs `dbs8j2habdes73fqs54g`, `dbs8j38k09pc73avsdh0`, `dbs8j47v5hds73diltlg`, `dbs8j48k09pc73avsdi0`), executing all 757 circuits to completion.

---

## 3. Lattice Geometry & Hamiltonian

We utilize a 7-qubit cluster mapped directly onto physical adjacent links on the IBM Heron heavy-hex lattice (zero virtual SWAP overhead):

```text
       (A1 = 117)             (B1 = 122)
          \                      /
           \                    /
(A2 = 126) ─ (S1 = 125) ─ [Shared = 124] ─ (S2 = 123) ─ (B2 = 136)
```

The unitary evolution operator per round $r$ consists of spoke couplings and ring couplings modulated by Peierls phases $\Phi = \pi/16$ and flux $\Phi_F = \pm \pi/6$:
$$U_{\text{edge}}(\theta, \phi) = \begin{pmatrix} 1 & 0 & 0 & 0 \\ 0 & \cos\theta & -i e^{i\phi}\sin\theta & 0 \\ 0 & -i e^{-i\phi}\sin\theta & \cos\theta & 0 \\ 0 & 0 & 0 & 1 \end{pmatrix}$$

Opposite topological winding numbers ($m_1 = +1$, $m_2 = -1$) are assigned to Wheel 1 and Wheel 2 to facilitate chiral phase-locking across the central bridge.

---

## 4. Hardware Findings

### 4.1 Phase 4: Wheel Retention Plateau ($Z = 13.63$)
![Figure 1: Wheel Hardware Retention](img/wheel_hardware_retention.png)

*Figure 1:* Evolution of excitation retention $P(S=1)$ as a function of Trotter rounds $k$ ($0 \le k \le 32$, depth $\sim 200$ physical gates). The closed-loop anchored wheel (`wheel`, cyan) maintains an anomalous plateau around $37\%$, sharply contrasting against the rapid thermal collapse of the unanchored ring (`ring_only`, red dashed) and bare transmon (`alone`, orange dotted). Anomaly significance: $Z = 13.63$, $P < 10^{-15}$.

### 4.2 Phase 6: Quantum DRAM Write $\rightarrow$ Decouple $\rightarrow$ Hold Cycle
![Figure 2: Pump and Decouple Hardware Retention](img/decouple_hardware_retention.png)

*Figure 2:* Quantum DRAM Pump-and-Decouple verification on `ibm_marrakesh`. Left: Population of the receiver node $P(S_2)$. Decoupling occurs at $k=8$ (yellow dashed line). When isolated, the wheel loop (`hold_wheel2`, cyan) sustains its trapped excitation at $27.5\%$, outperforming idle transmon relaxation (`hold_idle`, red) by **$+15.62\%$**. Right: Collective population across the cell.

### 4.3 Phase 7: 10-Qubit Tri-Wheel Quantum Bus
![Figure 3: Tri-Wheel Quantum Bus Conduction](img/tri_wheel_hardware_conduction.png)

*Figure 3:* Tri-wheel 10-qubit linear bus on `ibm_marrakesh`. Excitation initialized at Transmitter $S_1$ (Q105) conducts through Relay $S_2$ (Q125) into Receiver $S_3$ (Q123), reaching $P(S_3) = 0.3008$ vs decoupled baseline $0.0170$. A three-way equipartition state ($S_1 \approx 35.9\%, S_2 \approx 25.2\%, S_3 \approx 30.5\%$) emerges at $k=16$, with collective 10-qubit retention sustaining $67.0\%$ at $k=32$.

### 4.4 Phase 8: 13-Qubit 2D Space-Fabric (BIC Bound State)
![Figure 4: 13Q Space-Fabric Hardware Retention](img/fabric_13q_hardware_plateau.png)

*Figure 4:* 13-qubit 2D space-fabric on `ibm_marrakesh`. A central hub (Q125) symmetrically broadcasts into three independent satellite cells along heavy-hex lattice lines ($120^\circ$ isotropic emission: $S_1 \approx 36.1\%, S_2 \approx 37.3\%, S_3 \approx 31.1\%$). Constructive multi-loop interference locks the cluster into a macroscopic bound state in the continuum (BIC), maintaining **$83.4\%$** collective retention across the 13 qubits at $k=32$.

### 4.5 Phase 9: A HÁLÓZAT — Distributed Autonomous Quantum Memory Mesh
![Figure 5: Distributed Mesh Hardware Retention](img/dist_mesh_hardware_retention.png)

*Figure 5:* Distributed Autonomous Quantum Memory Mesh across 13 qubits on `ibm_marrakesh`. Following 2D write through $k=8$, the central hub and all three communication bridges are disconnected. The three independent satellite cells independently trap the excitation. Left: Individual satellite nodes retain balanced populations ($S_1 = 24.80\%, S_2 = 26.76\%, S_3 = 20.51\%$). Right: Collective network retention reaches **$72.07\%$** at $k=32$, securing a **$+26.17\%$ net protection advantage** ($Z = 8.84\sigma, P < 10^{-18}$) over three idle transmons undergoing Markovian $T_1$ relaxation ($45.90\%$).

---

## 5. Topological Scaling Mechanism & Metric Reconciliations

A critical aspect of peer review is reconciling the observed retention numbers across scaling steps: **Why does the distributed network (Phase 9) sustain $72.07\%$ retention while the isolated single cell (Phase 6) sustains $27.54\%$?**

### 5.1 Single-Cell vs Collective Subspace Metrics
The apparent jump is strictly a consequence of well-defined subspace projections:
1. **Single-Cell Retention Metric ($P(S_i)$):**
   $$P(S_i) \equiv \frac{1}{N_\text{shots}} \sum_{x \in \{0,1\}^N, x_{S_i}=1} \text{count}(x)$$
   - In Phase 6 (Single decoupled cell): $P(S_2) = 27.54\%$ at $k=32$.
   - In Phase 9 (Distributed mesh): $P(S_1) = 24.80\%$, $P(S_2) = 26.76\%$, $P(S_3) = 20.51\%$.
   - **Crucial Invariant:** Local excitation retention in *each individual satellite cell* is virtually identical across both experiments ($\sim 21\% - 27\%$). The physics of local cell trapping is invariant under scaling.
2. **Collective Distributed Retention ($P_\text{mesh}$):**
   In Phase 9, excitation is broadcast across all three satellite cells before bridge decoupling. Within the single-excitation subspace, the collective retention of the stored state within the distributed memory mesh is:
   $$P_\text{mesh} = \sum_{i=1}^3 P(S_i) = 24.80\% + 26.76\% + 20.51\% = 72.07\%$$
   The appropriate reference control is three uncoupled, idle transmons undergoing bare $T_1$ decay ($P_\text{idle, 3q} = 45.90\%$). The distributed autonomous mesh provides a $+26.17\%$ advantage ($Z = 8.84\sigma$).
3. **Macroscopic Fabric Bound State ($83.4\%$ in Phase 8):**
   In Phase 8, the central hub remains actively driven (no decoupling); the $83.4\%$ metric represents the total projection onto the entire 13-qubit connected cluster ($\sum P(S_i) + P(\text{Hub}) + P(\text{Bridges})$), verifying continuous non-Hermitian bound-state trapping.

### 5.2 Dissipation Suppression via Subradiance
The physical mechanism enabling enhanced multi-node protection is subradiant dark-state interference:
- In an $N$-node topological cluster, cyclic Peierls phase modulation forms an asymmetric eigenstate with vanishing dipole coupling to the symmetric modes of the dissipative dielectric environment.
- Uncorrelated local Markovian relaxation channels on individual qubits couple to the protected collective mode with an effective projection scaling as $\sim 1/N_\text{nodes}$.
- Furthermore, spatial delocalization across disconnected planar cells ensures that localized dielectric two-level system (TLS) fluctuators cannot destroy the orthogonal coherent amplitude stored across the remaining distributed cells.

---

## 6. Discussion & Significance

Unlike active surface codes which require continuous syndrome measurement and high physical qubit overhead, topological wheel networks provide passive excitation trapping through engineered interference. 

The successful completion of all nine prospective hardware phases across two stages demonstrates:
1. Superconducting transmons can be topologically protected against energy dissipation on standard planar architectures.
2. Inter-cell excitation transfer can be coordinated via Kuramoto phase synchronization.
3. Decoupled autonomous cells can store transmitted quantum populations without continuous external driving.
4. Distributed multi-cell meshes scale collective retention through subradiant dark-state protection and topological spatial redundancy.

---

## Data Availability & Cryptographic Verification

All raw hardware count dictionaries, job manifests, transpiled circuits, and analysis scripts are publicly available at [github.com/silentnoisehun/triangle-anchor-memory](https://github.com/silentnoisehun/triangle-anchor-memory) under the MIT License and permanently archived with DOI on Zenodo.
