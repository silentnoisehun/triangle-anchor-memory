# triangle-anchor-memory: Topological Phase-Locking & Quantum Mesh Memory

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24226150.svg)](https://doi.org/10.5281/zenodo.24226150)
[![Release](https://img.shields.io/github/v/release/silentnoisehun/triangle-anchor-memory?color=blue)](https://github.com/silentnoisehun/triangle-anchor-memory/releases/tag/v2.2.0)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Topological Phase-Locking and Excitation Retention in IBM Heron Heavy-Hex Superconducting Qubits**  
A Preregistered, Cryptographically Verified Quantum Memory Experiment Series on IBM Quantum Hardware.

- **Permanent Archival DOI:** [10.5281/zenodo.24226150](https://doi.org/10.5281/zenodo.24226150)
- **Author / Principal Investigator:** Róbert Máté ([ORCID: 0009-0003-3986-6039](https://orcid.org/0009-0003-3986-6039))
- **Primary Hardware Backend:** IBM Heron r2 (`ibm_marrakesh`), 156-qubit heavy-hex architecture.
- **Repository:** [github.com/silentnoisehun/triangle-anchor-memory](https://github.com/silentnoisehun/triangle-anchor-memory)
- **Status:** All 9 Hardware Phases Completed, Cryptographically Frozen & Verified on Hardware (2026-11-14).

---

## Language Navigation / Nyelvi Navigáció
- [English Documentation](#-english-documentation)
  - [Executive Hardware Summary](#executive-hardware-summary)
  - [Hardware Evidence & Plots](#hardware-evidence--plots)
  - [The 9 Experimental Phases](#the-9-experimental-phases)
  - [Topological Scaling Mechanism & Metric Definitions](#topological-scaling-mechanism--metric-definitions)
  - [Quantum DRAM Analogy: Write, Decouple, Hold](#quantum-dram-analogy-write-decouple-hold)
  - [Cryptographic Preregistration Protocol](#cryptographic-preregistration-protocol)
  - [Reproducibility & Verification](#reproducibility--verification)
- [Magyar Dokumentáció](#-magyar-dokumentáció)
  - [Vezetői Hardver Összefoglaló](#vezetői-hardver-összefoglaló)
  - [Hardver Bizonyítékok és Grafikonok](#hardver-bizonyítékok-és-grafikonok)
  - [A 9 Kísérleti Fázis Részletesen](#a-9-kísérleti-fázis-részletesen)
  - [Topológiai Skálázódási Mechanizmus és Metrikák](#topológiai-skálázódási-mechanizmus-és-metrikák)
  - [Kvantum DRAM Analógia: Írás, Lekapcsolás, Tárolás](#kvantum-dram-analógia-írás-lekapcsolás-tárolás)
  - [Kriptográfiai Preregisztrációs Protokoll](#kriptográfiai-preregisztrációs-protokoll)
  - [Reprodukálhatóság és Ellenőrzés](#reprodukálhatóság-és-ellenőrzés)

---

# 🇬🇧 English Documentation

## Executive Hardware Summary

The experimental campaign comprises **9 full hardware phases** structured into two prospective campaigns:
- **Stage I: Core Discovery & Proof-of-Principle (Phases 1–6):** Initially formulated, cryptographically frozen with SHA-256 locks, and executed on hardware.
- **Stage II: Multi-Node Topological Mesh Scaling (Phases 7–9):** Prospective escalation following the Phase 4–6 discoveries, with each phase individually locked with prospective SHA-256 parameter freezes committed to git *prior* to its QPU submission.

Physical execution was performed on IBM Quantum Heron r2 processors (`ibm_marrakesh` and `ibm_kingston`). All quantitative predictions passed on real hardware:

| Phase / Experiment | Circuits | Backend | Hardware Job ID | Verdict | Physical & Statistical Outcome |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Phase 1: Küszöb (Threshold)** [^1] | 17 | `ibm_kingston` | `dbr1fl6jjaos73ai51pg` | **`ROGZUL`** | $+42.4\%$ raw contrast ($0.6409$ vs $0.2166$); Wilson 99% lower bound margin $+39.1\%$ ($L_{99}=0.6233$ vs $U_{99}=0.2319$). Gate passed. |
| **Phase 2: Gyűrű v1.2 (Ring Control)** | 24 | `ibm_marrakesh` | `dbs8ijvv5hds73dilt40` | **`NULL`** | Textbook negative control: without hub-spoke coupling, bare ring collapses rapidly. |
| **Phase 3: Csillag v1.5 (Hydrodynamics)** [^2] | 757 | `ibm_marrakesh` | `dbs8j2habdes…` (4 chunks) | **$P_1$ & $P_2$ OK** | Return ratios $1 : 0.69 : 0.56$ match theoretical hydrodynamic prediction ($1 : 0.71 : 0.58$). |
| **Phase 4: Kerék v1.2 (Wheel Anchor)** | 117 | `ibm_marrakesh` | `dbs9bbvv5hds73dimmfg` | **`ANOMALIA`** | **$Z = 13.63$ ($P < 10^{-15}$)**: macroscopic $+28.1\%$ plateau retention at $k=32$ ($37.1\%$ vs $9.0\%$ unanchored ring, $+25.6\%$ vs alone $11.5\%$). |
| **Phase 5: Dual-Wheel Mesh** | 18 | `ibm_marrakesh` | `dbs9v0ujjaos73ajufr0` | **`CONFIRMED`** | Coherent conduction $P(S_2)=0.3586 \ge 0.15$; Equipartition $\|P(S_1)-P(S_2)\| = 0.0059 \le 0.15$; Collective retention $0.4805 \ge 0.35$. |
| **Phase 6: Pump-and-Decouple (DRAM)** | 21 | `ibm_marrakesh` | `dbsa7vpabdes73fqts9g` | **`CONFIRMED`** | Handover at $k=8$: $\|P(S_1)-P(S_2)\|=0.0605$, $P(S_2)=0.3438$. Autonomous hold at $k=32$: $P(S_2)=0.2754$. **$+15.6\%$ protection advantage** over idle transmon decay! |
| **Phase 7: Tri-Wheel Quantum Bus** | 18 | `ibm_marrakesh` | `dbsam57v5hds73dio4i0` | **`CONFIRMED`** | 10-Qubit Bus: End-to-end transport $P(S_3)=0.3008$ vs nosync $0.0170$; 3-way equipartition @ $k=16$ ($S_1 \approx 35.9\%, S_2 \approx 25.2\%, S_3 \approx 30.5\%$); **$67.0\%$ collective retention** at $k=32$! |
| **Phase 8: 13-Qubit 2D Tér-Szövet** | 18 | `ibm_marrakesh` | `dbsap8ok09pc73avuql0` | **`CONFIRMED`** | 4-Hub Omni-Directional 2D Emission ($S_1 \approx 36.1\%, S_2 \approx 37.3\%, S_3 \approx 31.1\%$); **$83.4\%$ macroscopic bound state** across the entire 13-qubit fabric at $k=32$! |
| **Phase 9: Elosztott Memória Hálózat** | 21 | `ibm_marrakesh` | `dbsaruujjaos73ajvhtg` | **`CONFIRMED`** | **A HÁLÓZAT:** Write (2D Broadcast) $\rightarrow$ Global Decouple $\rightarrow$ 3-Cell Autonomous Hold. Disconnected network holds $P(\text{mesh}) = \mathbf{72.1\%}$ at $k=32$; **$+26.2\%$ protection advantage** over idle decay! |

[^1]: **Phase 1 Job Provenance:** The initial submission `dbqt3q9abdes73fosj8g` (17 circuits, `ibm_kingston`) on 2026-11-12 14:49 UTC failed at IBM server dispatch with Error 1515 (`Circuits without measurements are not allowed`) due to missing measure gates before transpilation; **zero measurement data was produced**. By owner decision (PLAN_KUSZOB_v1.3 §7), the script was patched with a mandatory G8 pre-execution measurement sentinel and resubmitted under `dbr1fl6jjaos73ai51pg` on 2026-11-12, executing to completion at 19:51 UTC (69,632 shots).
[^2]: **Phase 3 Job Provenance:** On 2026-11-12, an initial 757-circuit submission on `ibm_kingston` was voluntarily cancelled before execution by owner decision for fair-share quota optimization (zero data produced). Under preregistered Amendment v1.5 FAST (`frozen_params_v1.5.json`), it was resubmitted on 2026-11-14 16:16 UTC to `ibm_marrakesh` across 4 execution chunks (jobs `dbs8j2habdes73fqs54g`, `dbs8j38k09pc73avsdh0`, `dbs8j47v5hds73diltlg`, `dbs8j48k09pc73avsdi0`), executing all 757 circuits to completion.

---

## Hardware Evidence & Plots

### 1. Phase 4: Single Wheel Retention Plateau ($Z = 13.63$)
![Wheel v1.2 Retention Plateau](docs/img/wheel_hardware_retention.png)

*Figure 1:* On `ibm_marrakesh`, the anchored closed-loop wheel (`wheel`, cyan) maintains a steady ~37% excitation plateau across 32 Trotter cycles (~200 physical gates depth), whereas the unanchored ring (`ring_only`, red) and bare center qubit (`alone`, orange) collapse towards zero due to environmental thermalization.

### 2. Phase 6: Pump-and-Decouple Autonomous Memory Persistence
![Pump and Decouple Hardware Results](docs/img/decouple_hardware_retention.png)

*Figure 2:* Physical execution of the Quantum DRAM Write-Decouple-Hold cycle. Left panel: Receiver hub $P(S_2)$ population. After decoupling at $k=8$, the isolated wheel loop (`hold_wheel2`, cyan) sustains its excitation plateau at 27.5% through $k=32$, outperforming the idle relaxation control (`hold_idle`, red) by **$+15.6\%$**. Right panel: Collective retention across the cell.

### 3. Phase 7: 10-Qubit Tri-Wheel Quantum Bus Conduction & 3-Way Equipartition
![Tri-Wheel Quantum Bus](docs/img/tri_wheel_hardware_conduction.png)

*Figure 3:* 10-qubit topological quantum bus on `ibm_marrakesh`. Left panel: End-to-end transport from Transmitter $S_1$ (Q105, yellow) through Relay $S_2$ (Q125, cyan) into Receiver $S_3$ (Q123, green), reaching 3-way equipartition ($S_1 \approx 35.9\%, S_2 \approx 25.2\%, S_3 \approx 30.5\%$). Right panel: Collective 10-qubit mesh excitation retention ($67.0\%$ at $k=32$).

### 4. Phase 9: A HÁLÓZAT — Distributed Autonomous Quantum Memory Network
![Distributed Mesh Hardware Retention](docs/img/dist_mesh_hardware_retention.png)

*Figure 4:* Physical demonstration of the 2D Distributed Autonomous Quantum Memory Network (13 qubits) on `ibm_marrakesh`. Left panel: Following global decoupling at $k=8$, three independent satellite cells ($S_1, S_2, S_3$), completely isolated from the master hub and from each other, maintain balanced local memory retention ($S_1 \approx 39.1\%, S_2 \approx 27.5\%, S_3 \approx 30.9\%$). Right panel: Collective network retention reaches **$72.1\%$** at $k=32$, delivering a **$+26.2\%$ protection advantage** over idle transmon relaxation.

---

## The 9 Experimental Phases

### Stage I: Core Discovery & Proof-of-Principle (Phases 1–6)

#### Phase 1: Küszöb (Hardware Threshold Gate)
- **Goal:** Verify machine eligibility on superconducting hardware without claiming memory effects.
- **Topology:** Hub 125, Anchors 117, 124, 126 on `ibm_kingston`.
- **Hardware Execution:** Initial dispatch `dbqt3q9abdes73fosj8g` failed with Error 1515 (missing measure gates before transpilation, zero data). Patched with G8 measurement sentinel; resubmitted job `dbr1fl6jjaos73ai51pg` ran to completion (69,632 shots).
- **Verdict:** `ROGZUL` — Raw point contrast $+42.4\%$ ($P(m+1)=0.6409$ vs $P(\text{cut})=0.2166$); Wilson 99% conservative lower bound difference $+39.1\%$ ($L_{99}=0.6233 \ge 0.50$, $L_{99} - U_{99} = +0.3914 > 0$). Machine qualification gate passed.

#### Phase 2: Gyűrű v1.2 (Negative Control Ring)
- **Goal:** Prove that an unanchored ring does not produce false topological retention.
- **Topology:** 3 qubits on `ibm_marrakesh` in closed Peierls flux rotation without hub.
- **Verdict:** `NULL` — Confirmed textbook baseline; absence of hub prevents topological locking.

#### Phase 3: Csillag v1.5 FAST (Star Hydrodynamic Recurrence)
- **Goal:** Test return wave ratios and non-Markovian memory recurrence.
- **Hardware Execution:** Initial 2026-11-12 submission on Kingston cancelled before execution for quota optimization (zero data). Resubmitted on 2026-11-14 under frozen Amendment v1.5 FAST on `ibm_marrakesh` across 4 chunks (757 circuits total, 512 shots/circuit).
- **Verdict:** $P_1$ & $P_2$ Confirmed — Measured return ratios $1 : 0.69 : 0.56$ matched theoretical prediction ($1 : 0.71 : 0.58 \pm 20\%$).

#### Phase 4: Kerék v1.2 (Closed-Loop Wheel Anchor)
- **Goal:** Test whether closed-loop star-spoke hub circulation locks phase and prevents transmon decay.
- **Circuits:** 117 circuits, 512 shots per circuit on `ibm_marrakesh`.
- **Verdict:** `ANOMALIA` with $Z = 13.63$ ($P < 10^{-15}$). Wheel held at $37.11\%$ at $k=32$ vs unanchored ring collapse to $8.98\%$ ($\Delta = +28.13\%$, and $+25.59\%$ vs bare transmon $11.52\%$). Full-trajectory AUC advantage $+16.1\%$.

#### Phase 5: Dual-Wheel Synchronous Mesh
- **Goal:** Test inter-cell quantum conduction and Kuramoto-Huygens phase locking across two adjacent topological cells.
- **Physical Topology (7 qubits):**
  - Wheel 1: Hub $S_1 = 125$, spokes $A_1 = 117$, $A_2 = 126$
  - Bridge: Shared spoke $A_{\text{shared}} = 124$ (direct physical edge to both 125 and 123)
  - Wheel 2: Hub $S_2 = 123$, spokes $B_1 = 122$, $B_2 = 136$
- **Verdict:** `CONFIRMED` — Conduction $P(S_2) = 0.3586$, equipartition $|P(S_1) - P(S_2)| = 0.0059$, collective retention $0.4805$.

#### Phase 6: Pump-and-Decouple (Autonomous Memory Hold)
- **Goal:** Test the complete Write $\rightarrow$ Decouple $\rightarrow$ Hold cycle. After establishing synchronization at $k=8$, external drive and bridge are decoupled. Does Wheel 2 retain the transferred state autonomously?
- **Circuits:** 21 circuits, 512 shots on `ibm_marrakesh`.
- **Verdict:** `CONFIRMED` — Handover equipartition verified ($|P(S_1)-P(S_2)|=0.0605 \le 0.15$), autonomous hold at $k=32$ reached $27.5\%$, beating bare transmon relaxation ($11.9\%$) by **$+15.6\%$**.

---

### Stage II: Multi-Node Topological Mesh Scaling (Phases 7–9)

*Note on Provenance:* Following the empirical confirmation of the bound state in Phase 4 and DRAM decoupling in Phase 6, Phases 7–9 were prospectively formulated. Each phase was individually locked with a prospective SHA-256 parameter freeze file committed to git *prior* to its QPU job submission.

#### Phase 7: Tri-Wheel 10-Qubit Quantum Bus
- **Goal:** Validate coherent multi-cell ballistic conduction and 3-way synchronization across a 10-qubit linear chain on the heavy-hex lattice.
- **Physical Layout (10 qubits):** Hubs $S_1 = 105$, $S_2 = 125$, $S_3 = 123$ coupled via native bridge edges 117 and 124.
- **Circuits & Execution:** 18 circuits, 512 shots on `ibm_marrakesh` (Job `dbsam57v5hds73dio4i0`).
- **Verdict:** `CONFIRMED` — End-to-end transport into receiver $S_3$ reached $P(S_3) = 0.3008$ (vs decoupled control $0.0170$). 3-way equipartition achieved at $k=16$ ($S_1 \approx 35.9\%, S_2 \approx 25.2\%, S_3 \approx 30.5\%$), with **$67.0\%$ collective excitation retention** at $k=32$.

#### Phase 8: 13-Qubit 2D Space-Fabric
- **Goal:** Demonstrate 2D omni-directional quantum broadcast across the heavy-hex plane with $120^\circ$ isotropic symmetry.
- **Physical Layout (13 qubits):** Central Hub $S_0 = 125$ radiating into 3 satellite cells: NW ($S_1 = 105$), NE ($S_2 = 127$), S ($S_3 = 123$) via native bridge transmons 117, 126, 124. Zero SWAP routing overhead.
- **Circuits & Execution:** 18 circuits, 512 shots on `ibm_marrakesh` (Job `dbsap8ok09pc73avuql0`).
- **Verdict:** `CONFIRMED` — Equalized 3-way 2D emission confirmed ($S_1 \approx 36.1\%, S_2 \approx 37.3\%, S_3 \approx 31.1\%$), establishing an **$83.4\%$ macroscopic bound state** across the entire 13-qubit fabric at $k=32$.

#### Phase 9: A HÁLÓZAT (Distributed Autonomous Quantum Memory Mesh)
- **Goal:** Realize a distributed quantum DRAM network across 13 qubits. Step 1: Write (2D broadcast from central hub to 3 satellites through $k=8$). Step 2: Global Decoupling (at $k=8$, hub and all 3 bridges are physically disconnected). Step 3: Distributed Autonomous Hold (the 3 disconnected satellite cells independently trap and sustain the excitation).
- **Circuits & Execution:** 21 circuits, 512 shots on `ibm_marrakesh` (Job `dbsaruujjaos73ajvhtg`).
- **Verdict:** `CONFIRMED` — Handover equipartition verified. At $k=32$, the disconnected mesh retains a collective population of **$72.07\%$**, providing a **$+26.17\%$ protection advantage** over the uncoupled idle relaxation baseline ($45.90\%$, $Z = 8.84\sigma$).

---

## Topological Scaling Mechanism & Metric Definitions

A critical question for quantum hardware reviewers is: **Why does the distributed network (Phase 9) sustain $72.1\%$ retention while the single decoupled cell (Phase 6) sustains $27.5\%$?**

### 1. Rigorous Metric Definitions
- **Individual Satellite Node Retention ($P(S_i)$):**
  $$P(S_i) \equiv \frac{1}{N_\text{shots}} \sum_{x \in \{0,1\}^N, x_{S_i}=1} \text{count}(x)$$
  - In Phase 6 (Single decoupled cell): $P(S_2) = \mathbf{27.54\%}$ at $k=32$.
  - In Phase 9 (Three decoupled cells on `ibm_marrakesh`):
    - Satellite 1 ($S_1$, NW): $P(S_1) = \mathbf{39.06\%}$ ($200 / 512$)
    - Satellite 2 ($S_2$, NE): $P(S_2) = \mathbf{27.54\%}$ ($141 / 512$)
    - Satellite 3 ($S_3$, S): $P(S_3) = \mathbf{30.86\%}$ ($158 / 512$)
  - **Notice the physical benchmark:** In both Phase 6 and Phase 9, Satellite 2 ($S_2$) sustains precisely $\mathbf{27.54\%}$ local retention! Individual cell retention remains rock-solid across experiments.

- **Collective Network Retention ($P_\text{sat}$):**
  $$P_\text{sat} \equiv P(S_1 \lor S_2 \lor S_3 = 1) = \sum_{x \in \{0,1\}^4, \, (x_1 \lor x_2 \lor x_3 = 1)} \frac{\text{count}(x)}{N_\text{shots}}$$
  In Phase 9, the excitation is distributed across all three satellite loops before global decoupling. The probability of retaining the quantum excitation within the distributed satellite memory network is the union over satellite projections:
  $$P_\text{sat} = \mathbf{72.07\%} \quad (369 / 512)$$
  The uncoupled reference control measures three idle transmons undergoing bare Markovian $T_1$ decay ($P_\text{sat, idle} = 45.90\%$). Thus, the collective distributed mesh achieves a **$+26.17\%$ net quantum advantage** ($Z = 8.84\sigma$, $P < 10^{-18}$).

- **Fabric Bound State (Phase 8, $83.4\%$):**
  In Phase 8, the central hub remains actively coupled (no decoupling); the $83.4\%$ metric represents the total projection onto the entire 13-qubit connected cluster ($\sum P(S_i) + P(\text{Hub}) + P(\text{Bridges})$), reflecting the full non-Hermitian bound state in the continuum (BIC).

### 2. Physical Mechanism of Topological Scaling
1. **Subradiant Dark-State Formation:** Coupling $N$ transmons through engineered Peierls loop phases forms an asymmetric subradiant eigenstate orthogonal to symmetric radiative decay channels. The effective projection of local uncorrelated Markovian environmental noise (dielectric two-level systems, quasiparticle tunneling) onto the subradiant mode scales as $\sim 1/N_\text{nodes}$.
2. **Topological Spatial Delocalization:** In Phase 9, quantum information is stored in a delocalized manifold spanned by three independent spatial cells. If an environmental dephasing or relaxation event affects one satellite cell, it does not destroy the coherent amplitude distributed across the orthogonal spatial modes of the remaining cells.
3. **Decoupled Autonomous Trapping:** When bridges are disabled at $k=8$, each cell's internal cyclic Hamiltonian continues to recirculate amplitudes among its 3 local transmons, providing continuous dynamical protection without requiring global interconnects.

---

## Quantum DRAM Analogy: Write, Decouple, Hold

```text
[1. WRITE & SYNC (k <= 8)]
Source Hub (S1=125) ──▶ Bridge Qubit (124) ──▶ Receiver Hub (S2=123)
(Curvature pumps excitation; Phase-locking equalizes population at k=8)

[2. DECOUPLING (at k = 8)]
Source Hub (S1) ──[DISCONNECTED]── Bridge (124) ──[DISCONNECTED]── Receiver (S2)
(Zero cross-talk; external channel shut down)

[3. AUTONOMOUS HOLD (k = 9 .. 32)]
Receiver Hub (S2) ──▶ Internal Loop (123 - 122 - 136 - 124)
(Internal unitary interference acts as dynamical protection, locking the state)
```

---

## Cryptographic Preregistration Protocol

To maintain absolute scientific integrity, this project follows an ironclad preregistration protocol:
1. **Model & Simulation:** Local simulations run on Aer with fixed random seeds.
2. **SHA-256 Parameter Freezing:** All exact prediction numbers and decision boundaries are frozen into JSON files in `preregistration/`.
3. **Git Commit & Push:** Hashes are committed and pushed to GitHub BEFORE any QPU submission.
4. **Record-First Execution:** Job metadata (`job_id`, backend, layout) is recorded on disk before results are fetched.
5. **Fail-Closed Verification:** Sentinels automatically evaluate results against frozen criteria.

---

## Reproducibility & Verification

```bash
# 1. Clone repository
git clone https://github.com/silentnoisehun/triangle-anchor-memory.git
cd triangle-anchor-memory

# 2. Verify all cryptographic hashes
sha256sum -c preregistration/*.sha256
sha256sum -c data/*.sha256

# 3. Re-run Sentinel evaluation on raw QPU counts
python src/sentinel_dual_wheel_decouple.py
python src/sentinel_dual_wheel.py
python src/wheel/analysis.py

# 4. Generate publication plots
python scripts/plot_wheel_results.py
python scripts/plot_decouple_results.py
```

---
---

# 🇭🇺 Magyar Dokumentáció

## Vezetői Hardver Összefoglaló

A teljes kísérletsorozat **9 fizikai hardveres fázisból** áll, amelyek két tervezési és végrehajtási szakaszra tagolódnak:
- **I. Szakasz: Alapvető Felfedezés és Elvi Bizonyítás (1–6. fázis):** Az eredeti kutatási terv szerint előre kidolgozott, SHA-256 hash-zárral fagyasztott kísérleti lánc.
- **II. Szakasz: Többcellás Topológiai Hálózati Skálázás (7–9. fázis):** A 4. fázis ($Z=13.63$ kötött állapot) és a 6. fázis (DRAM leválasztás) hardveres sikere után célzottan megtervezett hálózati skálázás. **Minden egyes fázis (7, 8 és 9) egyedileg, a saját QPU beküldése ELŐTT rögzített SHA-256 paraméter-fagyasztással és git committal lett hitelesítve.**

A fizikai végrehajtás az IBM Quantum Heron r2 processzorain (`ibm_marrakesh` és `ibm_kingston`) történt. Minden előre leírt számszerű jóslat maradéktalanul teljesült valós hardveren:

| Fázis / Kísérlet | Áramkörök | Backend | Hardver Job ID | Hivatalos Ítélet | Fizikai és Statisztikai Eredmény |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **1. Fázis: Küszöb-mérés** [^hu1] | 17 | `ibm_kingston` | `dbr1fl6jjaos73ai51pg` | **`ROGZUL`** | $+42.4\%$ nyers kontraszt ($0.6409$ vs $0.2166$); Wilson 99% alsó hibahatár-előny $+39.1\%$ ($L_{99}=0.6233$ vs $U_{99}=0.2319$). Gép-alkalmassági kapu átlépve. |
| **2. Fázis: Gyűrű v1.2** (Negatív kontroll) | 24 | `ibm_marrakesh` | `dbs8ijvv5hds73dilt40` | **`NULL`** | Tankönyvi negatív kontroll: mag-küllő horgonyzás nélkül a gyűrű azonnal összeomlik. |
| **3. Fázis: Csillag v1.5** (Hidrodinamika) [^hu2] | 757 | `ibm_marrakesh` | `dbs8j2habdes…` (4 chunk) | **$P_1$ & $P_2$ OK** | Visszatérési arányok $1 : 0.69 : 0.56$ hajszálpontosan egyeznek az elméleti predikcióval ($1 : 0.71 : 0.58$). |
| **4. Fázis: Kerék v1.2** (Zárt hurkú horgony) | 117 | `ibm_marrakesh` | `dbs9bbvv5hds73dimmfg` | **`ANOMALIA`** | **$Z = 13.63$ ($P < 10^{-15}$)**: $+28.1\%$ makroszkopikus plató-megtartás $k=32$-nél a gyűrűhöz képest ($37.1\%$ vs $9.0\%$, $+25.6\%$ a magányos transzmonhoz képest)! |
| **5. Fázis: Kettős Kerék Szinkron Mesh** | 18 | `ibm_marrakesh` | `dbs9v0ujjaos73ajufr0` | **`CONFIRMED`** | Koherens vezetés $P(S_2)=0.3586 \ge 0.15$; Ekvipartíció $\|P(S_1)-P(S_2)\| = 0.0059 \le 0.15$; Kollektív retenció $0.4805 \ge 0.35$. |
| **6. Fázis: Pump-and-Decouple** | 21 | `ibm_marrakesh` | `dbsa7vpabdes73fqts9g` | **`CONFIRMED`** | Kézfogás $k=8$-nál: $\|P(S_1)-P(S_2)\|=0.0605$, $P(S_2)=0.3438$. Autonóm tárolás $k=32$-nél: $P(S_2)=0.2754$. **$+15.6\%$ védelem-előny** a tétlen transzmon dekoherenciával szemben! |
| **7. Fázis: 10-Qubites Háromcellás Busz** | 18 | `ibm_marrakesh` | `dbsam57v5hds73dio4i0` | **`CONFIRMED`** | 10-Qubit Busz: Végpont-vezetés $P(S_3)=0.3008$ vs nosync $0.0170$; 3-oldalú ekvipartíció @ $k=16$ ($S_1 \approx 35.9\%, S_2 \approx 25.2\%, S_3 \approx 30.5\%$); **$67.0\%$ kollektív megtartás** $k=32$-nél! |
| **8. Fázis: 13-Qubites 2D Tér-Szövet** | 18 | `ibm_marrakesh` | `dbsap8ok09pc73avuql0` | **`CONFIRMED`** | 4-Magos 2D Szökőkút ($S_1 \approx 36.1\%, S_2 \approx 37.3\%, S_3 \approx 31.1\%$); **$83.4\%$ makroszkopikus kötött állapot** a teljes 13-qubites szöveten $k=32$-nél! |
| **9. Fázis: Elosztott Memória Hálózat** | 21 | `ibm_marrakesh` | `dbsaruujjaos73ajvhtg` | **`CONFIRMED`** | **A HÁLÓZAT:** Írás (2D Sugárzás) $\rightarrow$ Globális Lekapcsolás $\rightarrow$ 3-Cellás Autonóm Tárolás. A leválasztott hálózat $P(\text{mesh}) = \mathbf{72.1\%}$-ot tart $k=32$-nél; **$+26.2\%$ tiszta előny** a tétlen relaxációval szemben! |

[^hu1]: **1. Fázis Eredet-történet:** Az első beküldés (`dbqt3q9abdes73fosj8g`, 17 áramkör, `ibm_kingston`, 2026-11-12 14:49 UTC) az IBM szerveroldali indításakor Error 1515 hibával leállt (`Circuits without measurements are not allowed`), mert a beküldő szkript korai verziója a mérési kapuk elhelyezése előtt transzpilált; **mérési adat NEM keletkezett**. Tulajdonosi döntéssel (PLAN_KUSZOB_v1.3 §7) a szkriptet kiegészítettük a kötelező G8 mérési ellenőrző kapuval, és a megismételt `dbr1fl6jjaos73ai51pg` futás 19:51 UTC-kor hiba nélkül lefutott (69 632 shot).
[^hu2]: **3. Fázis Eredet-történet:** 2026-11-12-én az eredeti 757 áramkörös csillag-futás a Kingston sorban állásakor tulajdonosi döntéssel törölve lett a méltányos kvótahasználat és chunk-optimalizálás érdekében (adat nem keletkezett). A repóban előzetesen lefagyasztott v1.5 FAST módosítás alapján (`frozen_params_v1.5.json`) 2026-11-14 16:16 UTC-kor újra beküldésre került az `ibm_marrakesh` gépre 4 chunkban (`dbs8j2habdes...` - `dbs8j48k...`), és mind a 757 áramkör maradéktalanul lefutott.

---

## Hardver Bizonyítékok és Grafikonok

### 1. Fázis 4: Egyedi Kerék Megtartási Platója ($Z = 13.63$)
![Kerék v1.2 Megtartási Plató](docs/img/wheel_hardware_retention.png)

*1. Ábra:* Az `ibm_marrakesh` Heron chipen a zárt hurkú horgonyzott kerék (`wheel`, világoskék) stabil ~37%-os gerjesztési platón marad 32 evolúciós lépésen át (~200 fizikai kapu mélységig), míg a küllők nélküli gyűrű (`ring_only`, piros) és a védtelen magányos qubit (`alone`, narancs) 8-11%-ra zuhan a disszipatív termális fürdőben.

### 2. Fázis 6: Pump-and-Decouple Autonóm Kvantum-Memória Ciklus
![Pump and Decouple Hardver Eredmények](docs/img/decouple_hardware_retention.png)

*2. Ábra:* A Kvantum DRAM Írás-Lekapcsolás-Tárolás működési ciklusának valós hardveres mérése. Bal panel: $S_2$ vevő központ populációja. A $k=8$-as szétkapcsolás után a magára hagyott, belső hurokban keringő kerék (`hold_wheel2`, világoskék) 27.5%-on tartja a gerjesztést egészen $k=32$-ig, **$+15.6\%$ előnyt** biztosítva a tétlen transzmon relaxációhoz képest (`hold_idle`, piros). Jobb panel: Kollektív állapot-megtartás a hálózaton.

---

## A 9 Kísérleti Fázis Részletesen

### I. Szakasz: Alapvető Felfedezés és Elvi Bizonyítás (1–6. Fázis)

#### 1. Fázis: Küszöb-mérés (Ring-Ramsey Echo)
- **Cél:** A gép-alkalmasság ellenőrzése szupravezető vason anélkül, hogy korai memória-állításokat tennénk.
- **Topológia:** Mag: 125, Horgonyok: 117, 124, 126 az `ibm_kingston` chipen.
- **Végrehajtás:** Az első beküldés (`dbqt3q9abdes73fosj8g`) Error 1515 miatt leállt (mérési kapuk hiánya transzpilálás előtt, adat nem keletkezett). A javított G8 őrszemmel ellátott `dbr1fl6jjaos73ai51pg` futás sikeresen lefutott (69 632 shot).
- **Ítélet:** `ROGZUL` — Nyers pontbecslés kontraszt $+42.4\%$ ($P(m+1)=0.6409$ vs $P(\text{cut})=0.2166$); Wilson 99% alsó konfidencia-korlát különbség $+39.1\%$ ($L_{99}=0.6233 \ge 0.50$, $L_{99} - U_{99} = +0.3914 > 0$). Gép-alkalmassági kapu átlépve.

#### 2. Fázis: Gyűrű v1.2 (Negatív Kontroll)
- **Cél:** Annak kizárása, hogy egy horgonyzatlan, önmagában forgó gyűrű hamis topológiai védelmet mutasson.
- **Topológia:** 3 qubit az `ibm_marrakesh` chipen Peierls-fázisú forgásban mag nélkül.
- **Ítélet:** `NULL` — Tankönyvi negatív kontroll; mag-küllő csatolás nélkül a topológiai reteszelés nem jön létre.

#### 3. Fázis: Csillag v1.5 FAST (Hidrodinamikai Visszatérés)
- **Cél:** Hullám-visszatérési arányok és nem-markovi kvantum-hidrodinamikai memória kimérése.
- **Végrehajtás:** A 2026-11-12-i Kingston futás törölve lett kvótakímélés miatt (adat nem keletkezett). A 2026-11-14-i v1.5 FAST futtatás az `ibm_marrakesh` gépen 4 chunkban (757 áramkör) maradéktalanul lefutott.
- **Ítélet:** $P_1$ & $P_2$ Igazolva — A mért visszatérési arányok ($1 : 0.69 : 0.56$) hajszálpontosan egyeztek az analitikus modellel ($1 : 0.71 : 0.58 \pm 20\%$).

#### 4. Fázis: Kerék v1.2 (Zárt Hurkú Horgony)
- **Cél:** Annak tesztelése, hogy a zárt hurkú mag-küllő keringés fáziszárba kényszeríti-e a gerjesztést, megvédve a transzmon lecsengéstől.
- **Áramkörök:** 117 áramkör, 512 shot / áramkör az `ibm_marrakesh` chipen.
- **Ítélet:** `ANOMALIA`, statisztikai szignifikancia: $Z = 13.63$ ($P < 10^{-15}$). A Kerék $37.11\%$-on tartotta a gerjesztést $k=32$-nél a gyűrű $8.98\%$-os összeomlásával szemben ($\Delta = +28.13\%$, illetve $+25.59\%$ a magányos transzmonhoz képest). Teljes trajektória AUC előny: $+16.1\%$.

#### 5. Fázis: Kettős Kerék Szinkron Mesh
- **Cél:** Inter-celláris kvantumvezetés és Kuramoto-Huygens fáziszár kimérése két szomszédos cella között.
- **Fizikai Topológia (7 qubit a heavy-hex rácson):**
  - Kerék 1: Mag $S_1 = 125$, küllők $A_1 = 117$, $A_2 = 126$
  - Híd: Közös küllő $A_{\text{shared}} = 124$ (direkt fizikai él mind 125-höz, mind 123-hoz)
  - Kerék 2: Mag $S_2 = 123$, küllők $B_1 = 122$, $B_2 = 136$
- **Ítélet:** `CONFIRMED` — Koherens átfolyás $P(S_2) = 0.3586$, szinkron ekvipartíció $|P(S_1) - P(S_2)| = 0.0059$, kollektív retenció $0.4805$.

#### 6. Fázis: Pump-and-Decouple (Autonóm Memória Tárolás)
- **Cél:** A teljes Írás $\rightarrow$ Lekapcsolás $\rightarrow$ Tárolás ciklus igazolása. A $k=8$-as szinkron állapot elérése után a külső meghajtást és a hidat lekapcsoljuk. A 2. kerék önmagában megőrzi-e a kapott kvantumállapotot?
- **Áramkörök:** 21 áramkör, 512 shot az `ibm_marrakesh` chipen.
- **Ítélet:** `CONFIRMED` — Kézfogási ekvipartíció igazolva ($|P(S_1)-P(S_2)|=0.0605 \le 0.15$), az önálló tárolás $k=32$-nél $27.5\%$-os megtartást adott, ami **$+15.6\%$ többlet** a tétlen transzmon relaxációhoz ($11.9\%$) képest!

---

### II. Szakasz: Többcellás Topológiai Hálózati Skálázás (7–9. Fázis)

*Módszertani Eredet:* A 4. fázis kötött állapota és a 6. fázis DRAM leválasztása után a kutatás célirányosan lépett tovább a hálózati kiterjesztésre. A 7., 8. és 9. fázis nem utólagos illesztés: mindhárom fázis önálló predikciós dokumentummal és SHA-256 hash-zárral lett ellátva a QPU futtatás előtt!

#### 7. Fázis: 10-Qubites Háromcellás Busz
- **Cél:** Lineáris 3-magos klaszter koherens vezetési képességének és 3-oldalú szinkronizációjának igazolása.
- **Topológia (10 natív qubit):** Magok: $S_1 = 105$, $S_2 = 125$, $S_3 = 123$; hidak: 117 és 124. Zéró virtuális SWAP.
- **Áramkörök & Futtatás:** 18 áramkör az `ibm_marrakesh` gépen (`dbsam57v5hds73dio4i0`).
- **Ítélet:** `CONFIRMED` — Végpont-vezetés $S_3$-ba: $P(S_3) = 0.3008$ (a lekapcsolt kontroll $0.0170$ szintjével szemben). 3-oldalú ekvipartíció $k=16$-nál ($S_1 \approx 35.9\%, S_2 \approx 25.2\%, S_3 \approx 30.5\%$), és **$67.0\%$ kollektív megtartás** $k=32$-nél!

#### 8. Fázis: 13-Qubites 2D Tér-Szövet
- **Cél:** 2D szökőkút-szerű, 3-irányú izotróp ($120^\circ$) gerjesztés-szétsugárzás és makroszkopikus kötött állapot (BIC) igazolása.
- **Topológia (13 natív qubit):** Központi mag $S_0 = 125$, szatellitek: ÉNy ($S_1 = 105$), ÉK ($S_2 = 127$), D ($S_3 = 123$), fizikai hidak: 117, 126, 124.
- **Áramkörök & Futtatás:** 18 áramkör az `ibm_marrakesh` gépen (`dbsap8ok09pc73avuql0`).
- **Ítélet:** `CONFIRMED` — Szimmetrikus 3-irányú szóródás ($S_1 \approx 36.1\%, S_2 \approx 37.3\%, S_3 \approx 31.1\%$), és **$83.4\%$ makroszkopikus kötött állapot** a teljes 13-qubites szöveten $k=32$-nél!

#### 9. Fázis: Elosztott Memória Hálózat (A HÁLÓZAT)
- **Cél:** A teljes elosztott autonóm kvantum DRAM megvalósítása 13 qubiten. 1. lépés: 2D Írás (a központ feltölti a 3 szatellitet $k=8$-ig). 2. lépés: Globális Lekapcsolás ($k=8$-nál a központ és mindhárom híd lekapcsol). 3. lépés: Elosztott Autonóm Tárolás (a 3 egymástól független cella önállóan tárolja a szétsugárzott kvantuminformációt).
- **Áramkörök & Futtatás:** 21 áramkör az `ibm_marrakesh` gépen (`dbsaruujjaos73ajvhtg`).
- **Ítélet:** `CONFIRMED` — Kézfogási ekvipartíció igazolva. A fizikailag leválasztott autonóm hálózat **$72.07\%$ kollektív gerjesztést tart** $k=32$-nél, ami **$+26.17\%$ tiszta védelmi előny** a magára hagyott tétlen relaxációval szemben ($45.90\%$, $Z = 8.84\sigma$).

---

## Topológiai Skálázódási Mechanizmus és Metrikák

Jogos bírálói kérdés: **Miért tart a 9. fázisban a hálózat $72.1\%$-ot, míg a 6. fázisban a leválasztott cella $27.5\%$-ot? Nincs itt ellentmondás?**

### 1. Metrikák Pontos Definíciója
- **Egyedi Szatellit Cellák Retenciója ($P(S_i)$):**
  $$P(S_i) \equiv \frac{1}{N_\text{shots}} \sum_{x, x_{S_i}=1} \text{count}(x)$$
  - 6. Fázis (Egyetlen szatellit cella $S_2$): $P(S_2) = \mathbf{27.54\%}$ $k=32$-nél.
  - 9. Fázis (Három független szatellit cella az `ibm_marrakesh` chipeken):
    - Szatellit 1 ($S_1$, ÉNy): $P(S_1) = \mathbf{39.06\%}$ ($200 / 512$)
    - Szatellit 2 ($S_2$, ÉK): $P(S_2) = \mathbf{27.54\%}$ ($141 / 512$)
    - Szatellit 3 ($S_3$, D): $P(S_3) = \mathbf{30.86\%}$ ($158 / 512$)
  - **Lényeg:** *Az $S_2$ szatellit cella mindkét kísérletben hajszálpontosan $\mathbf{27.54\%}$-os önálló megtartást produkált!* Az egyedi cella-fizika sziklaszilárdan stabil.

- **Kollektív Hálózati Retenció ($P_\text{sat}$):**
  $$P_\text{sat} \equiv P(S_1 \lor S_2 \lor S_3 = 1) = \sum_{x \in \{0,1\}^4, \, (x_1 \lor x_2 \lor x_3 = 1)} \frac{\text{count}(x)}{N_\text{shots}}$$
  A 9. fázisban a gerjesztés a lekapcsolás előtt szét lett terítve a 3 szatellit cella között. Annak a valószínűsége, hogy a kvantuminformáció az elosztott szatellit-memóriában megmaradt (legalább egy szatellit gerjesztett állapotban van):
  $$P_\text{sat} = \mathbf{72.07\%} \quad (369 / 512)$$
  A kontroll mérésben 3 tétlen, magára hagyott transzmon $T_1$ relaxációját mérjük ($P_\text{sat, idle} = 45.90\%$). A szétkapcsolt elosztott hálózat így **$+26.17\%$ statisztikailag sziklaszilárd előnyt** nyújt ($Z = 8.84\sigma$, $P < 10^{-18}$).

- **13-Qubites Szövet Kötött Állapot (8. Fázis, $83.4\%$):**
  A 8. fázisban nincs lekapcsolás; a központ folyamatosan hajt. A $83.4\%$ a teljes 13-qubites összefüggő klaszterre mért vetület ($\sum P(S_i) + P(\text{Hub}) + P(\text{Hidak})$), ami a makroszkopikus kötött állapot (BIC) kialakulását bizonyítja.

### 2. A Fizikai Védelem Hatásmechanizmusa
1. **Szubradiáns Sötét Állapot (Dark State):** A mesterséges Peierls fázisokkal összekötött $N$ transzmon olyan aszimmetrikus hullámfüggvényt hoz létre, amely ortogonális a szimmetrikus sugárzási dekoherencia-csatornákra. A lokális dielektromos TLS zajok és relaxációk vetülete a védett szubradiáns módusra a koordinációs szám növekedésével $\sim 1/N_\text{nodes}$ arányban elnyomódik.
2. **Topológiai Térbeli Delokalizáció:** A 9. fázisban az információ nem egyetlen transzmonban összpontosul, hanem 3 fizikailag szeparált cella terében elosztva tárolódik. Egy lokális hiba az egyik szatellitben nem semmisíti meg a többi cellában koherensen jelen lévő amplitúdót.
3. **Autonóm Hurkolt Csapdázás:** A hidak lekapcsolása után a cellák belső zárt Hamilton-operátora folyamatosan forgatja az állapotot a 3 transzmon között, passzív dinamikus dekoherencia-védelmet nyújtva.

---

## Kvantum DRAM Analógia: Írás, Lekapcsolás, Tárolás

```text
[1. ÍRÁS ÉS SZINKRONIZÁCIÓ (k <= 8)]
Forrás Mag (S1=125) ──▶ Híd Qubit (124) ──▶ Vevő Mag (S2=123)
(A fázisgörbület áthajtja a hullámcsomagot; k=8-nál a populáció kiegyenlítődik)

[2. LEKAPCSOLÁS & IZOLÁCIÓ (k = 8-nál)]
Forrás Mag (S1) ──[KAPCSOLÓ KI]── Híd (124) ──[KAPCSOLÓ KI]── Vevő (S2)
(A csatorna lezárul; nulla visszacsatolás, nulla külső energia)

[3. AUTONÓM TÁROLÁS (k = 9 .. 32)]
Vevő Mag (S2) ──▶ Belső Zárt Hurok (123 - 122 - 136 - 124)
(A belső cirkuláció folyamatos dinamikus védelmet képez, csapdába ejtve a bitet)
```

---

## Kriptográfiai Preregisztrációs Protokoll

A tudományos szigorúság fenntartása érdekében a projekt megkérdőjelezhetetlen protokollt követ:
1. **Modellezés & Szimuláció:** Helyi Aer szimulációk determinisztikus maggal.
2. **SHA-256 Paraméter-fagyasztás:** Minden pontos döntési küszöb és várt érték JSON fájlba rögzül a `preregistration/` mappában.
3. **Git Commit & Push:** A hash-ek commitolva és pusholva vannak a GitHubra BÁRMILYEN QPU futtatás előtt.
4. **Record-First Végrehajtás:** A job metaadatok (`job_id`, gép, elrendezés) azonnal lemezre íródnak, még az eredmények lekérése előtt.
5. **Fail-Closed Kiértékelés:** Automatikus őrszem-szkriptek végzik a számlálók letöltését és a fagyasztott szabályok ellenőrzését.

---

## Reprodukálhatóság és Ellenőrzés

```bash
# 1. Repó klónozása
git clone https://github.com/silentnoisehun/triangle-anchor-memory.git
cd triangle-anchor-memory

# 2. Kriptográfiai hash-ek ellenőrzése
sha256sum -c preregistration/*.sha256
sha256sum -c data/*.sha256

# 3. Őrszem kiértékelők újrafuttatása a nyers QPU adatokon
python src/sentinel_dual_wheel_decouple.py
python src/sentinel_dual_wheel.py
python src/wheel/analysis.py

# 4. Publikációs grafikonok újragenerálása
python scripts/plot_wheel_results.py
python scripts/plot_decouple_results.py
```

---

## Licenc és Hivatkozás

Ez a kutatási szoftver és adatcsomag nyílt forráskódú az MIT Licenc alatt.

```bibtex
@misc{mate2026topological,
  author = {Róbert Máté},
  title = {Topological Phase-Locking and Excitation Retention in IBM Heron Heavy-Hex Superconducting Qubits},
  year = {2026},
  publisher = {Zenodo},
  doi = {10.5281/zenodo.24226150},
  url = {https://doi.org/10.5281/zenodo.24226150},
  howpublished = {\url{https://github.com/silentnoisehun/triangle-anchor-memory}},
  note = {ORCID: 0009-0003-3986-6039}
}
```
