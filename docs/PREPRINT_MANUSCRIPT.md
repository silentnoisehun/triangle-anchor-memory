# Topological Phase-Locking and Autonomous Excitation Retention in IBM Heron Heavy-Hex Superconducting Qubits

**Author:** Róbert Máté ([ORCID: 0009-0003-3986-6039](https://orcid.org/0009-0003-3986-6039))  
**Permanent DOI:** [10.5281/zenodo.24226150](https://doi.org/10.5281/zenodo.24226150)  
**Contact:** `silentnoisehun@gmail.com`  
**Affiliation:** Independent Quantum Researcher, Budapest, Hungary  
**Repository:** [github.com/silentnoisehun/triangle-anchor-memory](https://github.com/silentnoisehun/triangle-anchor-memory)  
**Date:** November 14, 2026

---

## Abstract

Preserving quantum coherence against dissipative decay without the active syndrome extraction overhead of quantum error correction (QEC) is a central challenge in scalable quantum technology. Here, we demonstrate topological phase-locking and coherent excitation trapping on utility-scale superconducting quantum processors (IBM Heron r2, `ibm_marrakesh` and `ibm_kingston`). Across a six-phase, cryptographically preregistered experimental campaign (with SHA-256 parameter locks prior to physical execution), we show that a closed-loop wheel topology—comprising a central transmon symmetrically coupled to perimeter anchors under Peierls phase modulation—stabilizes an excitation plateau at $\sim 37\%$ over 32 Trotter steps ($\sim 200$ physical two-qubit gates), exhibiting anomalous retention with statistical significance $Z = 13.63$ ($P < 10^{-15}$) relative to unanchored ring controls. Extending this to a seven-qubit dual-wheel mesh, we demonstrate inter-cell Kuramoto-Huygens synchronization and directional conduction ($P(S_2) = 0.3586$, $|P(S_1) - P(S_2)| = 0.0059$). Finally, executing a complete quantum DRAM cycle (Write $\rightarrow$ Decouple $\rightarrow$ Hold), we physically decouple the source and communication bridge at $k=8$; the isolated receiving wheel autonomously retains its excitation state ($P(S_2) = 0.2754$ at $k=32$), demonstrating a **$+15.62\%$ protection advantage** over bare transmon environmental relaxation ($11.91\%$). These results establish a pathway toward passive, topology-protected quantum memories on planar superconducting lattices.

---

## 1. Introduction

Superconducting transmons are leading physical building blocks for scalable quantum computing. However, open quantum systems remain fundamentally limited by local Markovian energy relaxation ($T_1$) and dephasing ($T_2^*$). Standard active quantum error correction incurs substantial qubit overhead, continuous syndrome measurement backaction, and complex classical decoding latency.

Alternative paradigms inspired by non-Hermitian photonics and topological physics exploit bound states in the continuum (BICs) and collective interference phenomena such as subradiance and synchronization. If destructive interference suppresses radiation into the dissipative environment while constructive phase interference refocuses quantum amplitudes at protected lattice nodes, coherent states can be dynamically trapped.

In this work, we experimentally demonstrate this principle on physical IBM Heron r2 superconducting processors arranged in a 156-qubit heavy-hex lattice. Through a preregistered sequence of six experimental phases, we confirm:
1. Machine qualification thresholds (`ROGZUL`),
2. Unanchored ring decay baselines (`NULL`),
3. Hydrodynamic recurrence scaling ($P_1, P_2$),
4. Anomalous wheel excitation retention ($Z = 13.63, P < 10^{-15}$),
5. Dual-cell synchronization ($|P(S_1) - P(S_2)| = 0.0059$),
6. Autonomous memory retention after physical channel decoupling ($\Delta = +15.62\%$).

---

## 2. Experimental Summary & Hardware Evidence

| Phase / Experiment | Circuits | Backend | Hardware Job ID | Verdict | Physical & Statistical Outcome |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Phase 1: Küszöb (Threshold)** | 17 | `ibm_kingston` | `dbr1fl6jjaos73ai51pg` | **`ROGZUL`** | $+39.1\%$ excitation retention with 3-anchor; gate passed. |
| **Phase 2: Gyűrű v1.2 (Control Ring)** | 24 | `ibm_marrakesh` | `dbs8ijvv5hds73dilt40` | **`NULL`** | Textbook negative control: without hub-spoke coupling, bare ring collapses rapidly. |
| **Phase 3: Csillag v1.5 (Hydrodynamics)** | 757 | `ibm_marrakesh` | `dbs8j2habdes…` (4 chunks) | **$P_1$ & $P_2$ OK** | Return ratios $1 : 0.69 : 0.56$ match theoretical prediction ($1 : 0.71 : 0.58$). |
| **Phase 4: Kerék v1.2 (Wheel Anchor)** | 117 | `ibm_marrakesh` | `dbs9bbvv5hds73dimmfg` | **`ANOMALIA`** | **$Z = 13.63$ ($P < 10^{-15}$)**: macroscopic $+42.1\%$ plateau retention at $k=32$ vs unanchored ring. |
| **Phase 5: Dual-Wheel Mesh** | 18 | `ibm_marrakesh` | `dbs9v0ujjaos73ajufr0` | **`CONFIRMED`** | Coherent conduction $P(S_2)=0.3586 \ge 0.15$; Equipartition $|P(S_1)-P(S_2)| = 0.0059 \le 0.15$; Collective retention $0.4805 \ge 0.35$. |
| **Phase 6: Pump-and-Decouple (DRAM)** | 21 | `ibm_marrakesh` | `dbsa7vpabdes73fqts9g` | **`CONFIRMED`** | Handover at $k=8$ verified; Autonomous hold at $k=32$: $P(S_2)=0.2754$. **$+15.62\%$ protection advantage** over idle transmon decay! |
| **Phase 7: Tri-Wheel 10-Qubit Bus** | 18 | `ibm_marrakesh` | `dbsam57v5hds73dio4i0` | **`CONFIRMED`** | End-to-end multi-cell transport $P(S_3)=0.3008$; 3-way equipartition ($S_1 \approx 35.9\%, S_2 \approx 25.2\%, S_3 \approx 30.5\%$); **$67.0\%$ collective retention** at $k=32$! |

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

---

## 5. Discussion & Significance

Unlike active surface codes which require continuous measurement and classical syndrome processing, the topological wheel architecture provides passive excitation trapping through engineered interference. 

The successful completion of all six preregistered hardware phases demonstrates:
1. Transmons can be topologically protected against energy dissipation on standard planar architectures.
2. Inter-cell excitation transfer can be coordinated via Kuramoto phase synchronization.
3. Decoupled autonomous cells can store transmitted quantum populations without continuous external driving.

---

## Data Availability & Cryptographic Verification

All raw hardware count dictionaries, job manifests, transpiled circuits, and analysis scripts are publicly available at [github.com/silentnoisehun/triangle-anchor-memory](https://github.com/silentnoisehun/triangle-anchor-memory) under the MIT License and permanently archived with DOI on Zenodo.
