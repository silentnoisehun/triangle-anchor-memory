# triangle-anchor-memory: Quantum Hardware Experiment Series & Comprehensive Noise Audit on IBM Heron

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24226150.svg)](https://doi.org/10.5281/zenodo.24226150)
[![Release](https://img.shields.io/github/v/release/silentnoisehun/triangle-anchor-memory?color=blue)](https://github.com/silentnoisehun/triangle-anchor-memory/releases/tag/v3.1.0)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Experimental Evaluation of Driven Superconducting Circuits, Multi-Qubit Noise Dynamics, and Simulation Baseline Discrepancies on IBM Heron Processors (1011 Circuits)**  
A Preregistered Open-Data Hardware Campaign on 156-Qubit Superconducting Quantum Processors (`ibm_marrakesh` and `ibm_kingston`).

- **Archival DOI:** [10.5281/zenodo.24226150](https://doi.org/10.5281/zenodo.24226150)
- **Principal Investigator:** Róbert Máté ([ORCID: 0009-0003-3986-6039](https://orcid.org/0009-0003-3986-6039))
- **Hardware Backends:** IBM Heron r2 (`ibm_marrakesh` and `ibm_kingston`), heavy-hex lattice.
- **Repository:** [github.com/silentnoisehun/triangle-anchor-memory](https://github.com/silentnoisehun/triangle-anchor-memory)
- **Status:** All 9 Phases Completed; Rigorous Physical & Noise Audit Integrated (`scripts/audit_excitation_and_aer.py`).

---

## Executive Summary & Core Physical Findings / Vezetői Összefoglaló és Fizikai Tények

This project executed a 9-phase preregistered experimental campaign (1011 physical quantum circuits, 512–4096 shots per circuit) on IBM Heron superconducting processors to investigate driven loop topologies.

Following rigorous post-execution physical auditing directly against the raw measurement bitstrings and textbook noisy Aer simulations, the experimental facts are:

1. **The 37% "Retention Plateau" is Textbook Depolarizing Gate Noise:**  
   In Phase 4 (Kerék, $k=32$, ~200 gate depth), the measured central qubit population on hardware is **$37.11\%$** (190/512 shots). The standard Qiskit Aer noisy simulation (`FakeMarrakesh` gate and readout noise) predicted **$37.99\%$** ($\Delta = -0.88\%$, within $1\sigma$ shot noise). The continuous drive depolarizes the qubit towards the mixed state ($P \to 0.5$) rather than sustaining an anomalous quantum bound state.
2. **Absence of Chiral Flux Advantage:**  
   The non-rotating static control (`static`, zero Peierls flux) yielded **$45.51\%$** (233/512) on hardware—higher than the rotating chiral drive ($37.11\%$). Driving the loop with synthetic flux provides no excitation trapping advantage over a static configuration.
3. **The $Z = 13.63$ "Anomaly" is a Simulation Baseline Artifact:**  
   The $Z = 13.63$ statistical metric was produced because the preregistered baseline simulation lacked realistic idle $T_1$ relaxation for the idle/unanchored control circuits (leaving them at ~55% in Aer). On actual hardware, idle transmons suffered natural thermal decay down to ~9–11%. Comparing a hardware difference ($37\% - 9\% = +28\%$) against a mismatched simulation difference ($38\% - 55\% = -17\%$) generated a large, purely mathematical artifact.
4. **Non-Conservation of Excitation Number (Noise-Pumped Excitations):**  
   In multi-qubit readout phases (Phases 7, 8, 9), circuits initialized with **exactly one excitation** ($X$ gate) exhibit extensive multi-excitation bitstrings ($N_\text{exc} \ge 2$). In Phase 9 (`dist_mesh`, $k=32$), **$32.8\%$** of the shots contain 2, 3, or 4 simultaneous excitations (rising to **$55.7\%$** under continuous drive). The apparent "collective retention" ($72.1\%$) predominantly counts incoherent excitations pumped into the lattice by gate depolarizing errors.
5. **Loss of Transverse Phase Coherence:**  
   Transverse phase tomography ($|+\rangle$ initialization) demonstrates that phase coherence rapidly decays to $|\text{coh}_\perp| \approx 0.070$ at $k=32$. The circuit does not preserve quantum phase or arbitrary superpositions.

---

## Comprehensive Audit Data

### 1. Excitation Number Breakdown (Hamming Weight Distribution)
*Audit script:* `scripts/audit_excitation_and_aer.py`  
*Single excitation injected at $t=0$.*

| Phase / Experiment | Mode ($k=32$) | $N=0$ (Lost) | $N=1$ (Single) | $N \ge 2$ (Noise-Pumped) | Total Shots |
|---|---|:---:|:---:|:---:|:---:|
| **Phase 8 (Tri-Wheel, 3 Cores)** | `nosync` (idle) | 62.3% (319) | 35.7% (183) | **2.0%** (10) | 512 |
| **Phase 8 (Tri-Wheel, 3 Cores)** | `sync` (driven) | 33.0% (169) | 41.6% (213) | **25.4%** (130) | 512 |
| **Phase 9 (Mesh, 4 Qubits)** | `hold_idle` | 39.3% (201) | 45.7% (234) | **15.0%** (77) | 512 |
| **Phase 9 (Mesh, 4 Qubits)** | `hold_mesh` | 21.5% (110) | 45.7% (234) | **32.8%** (168) | 512 |
| **Phase 9 (Mesh, 4 Qubits)** | `continuous` | 11.5% (59) | 32.8% (168) | **55.7%** (285) | 512 |

*Finding:* Under active gate driving, multi-excitation generation escalates from 2.0% to 25.4% (Phase 8) and up to 55.7% (Phase 9). The "104.5% sum" ($S_1 + S_2 + S_3 = 36.1\% + 37.3\% + 31.1\%$) in Phase 8 is physically explained by the 25.4% multi-excitation occurrence.

---

### 2. Hardware vs. Aer Noisy Simulation (Phase 4: Kerék)
*Comparing `wheel_raw_counts.json` directly to preregistered `wheel_freeze_data.json`.*

| Step $k$ | Aer Predicted $P(1)$ | Hardware Measured $P(1)$ | Difference (HW − Aer) |
|:---:|:---:|:---:|:---:|
| $k=0$ | 97.73% | 95.51% (489/512) | −2.22% |
| $k=4$ | 18.58% | 50.00% (256/512) | +31.42% |
| $k=8$ | 68.31% | 37.30% (191/512) | −31.01% |
| $k=12$ | 31.05% | 41.21% (211/512) | +10.16% |
| $k=16$ | 51.83% | 34.77% (178/512) | −17.07% |
| $k=20$ | 36.99% | 40.23% (206/512) | +3.25% |
| $k=24$ | 43.41% | 35.16% (180/512) | −8.25% |
| $k=28$ | 37.70% | 44.14% (226/512) | +6.45% |
| **$k=32$** | **37.99%** | **37.11%** (190/512) | **−0.88%** |

*Finding:* At step $k=32$, the hardware value is within 0.88% of the textbook Aer depolarizing noise simulation.

---

## Experimental Overview (All 9 Phases)

| Phase | Circuits | Backend | Hardware Job ID | Physical Verdict & Nature |
| :--- | :---: | :---: | :---: | :--- |
| **Phase 1: Küszöb** | 17 | `ibm_kingston` | `dbr1fl6jjaos73ai51pg` | **Passed:** Hardware contrast qualification gate ($+42.4\%$ raw contrast). |
| **Phase 2: Gyűrű v1.2** | 24 | `ibm_marrakesh` | `dbs8ijvv5hds73dilt40` | **Textbook Null:** Bare unanchored loop decays rapidly ($P \le 0.26$ at $k=16$). |
| **Phase 3: Csillag v1.5** | 757 | `ibm_marrakesh` | `dbs8j2habdes…` (4 chunks) | **Textbook Star:** Branching return ratios ($1 : 0.69 : 0.56$) match $1/\sqrt{N}$ lattice geometry. |
| **Phase 4: Kerék v1.2** | 117 | `ibm_marrakesh` | `dbs9bbvv5hds73dimmfg` | **Textbook Noise:** Plató at $37.11\%$ matches Aer noise model ($37.99\%$). Static control gives $45.51\%$. $Z=13.63$ is a simulation baseline artifact. |
| **Phase 5: Dual-Wheel** | 18 | `ibm_marrakesh` | `dbs9v0ujjaos73ajufr0` | **Conduction:** Driven inter-cell transfer observed; population spreads across nodes. |
| **Phase 6: Decouple** | 21 | `ibm_marrakesh` | `dbsa7vpabdes73fqts9g` | **Driven Hold:** $P(S_2)=27.54\%$ ($141/512$). Coincidental integer identical to Phase 9. |
| **Phase 7: Tri-Wheel Bus** | 18 | `ibm_marrakesh` | `dbsam57v5hds73dio4i0` | **Multi-Node Transport:** $P(S_3)=30.1\%$; multi-excitation accumulation observed. |
| **Phase 8: Space-Fabric** | 18 | `ibm_marrakesh` | `dbsap8ok09pc73avuql0` | **Noise Pumping:** $S_1+S_2+S_3 = 104.5\%$ explained by $25.4\%$ multi-excitation shots. |
| **Phase 9: Dist. Mesh** | 21 | `ibm_marrakesh` | `dbsaruujjaos73ajvhtg` | **Network Noise:** $72.07\%$ union retention driven by $32.8\%$ multi-excitation states. |

---

## Verification & Audit Scripts

The repository is equipped with fail-closed audit tools to verify raw counts, SHA-256 hashes, and noise dynamics directly:

```bash
# 1. Cryptographic and circuit integrity audit (1011 circuits, 68 SHA-256 hashes)
python scripts/audit_full_integrity.py

# 2. Physical and noise audit: excitation conservation & Aer comparison
python scripts/audit_excitation_and_aer.py

# 3. Physical mechanism diagnostics (chiral current & phase tomography)
python scripts/diagnose_mechanism.py
```

---

# 🇭🇺 Magyar Dokumentáció

## Részletes Fizikai és Hibaelemzés

A 9 fázisból álló kísérletsorozat (1011 fizikai áramkör az IBM Heron `ibm_marrakesh` és `ibm_kingston` gépein) a zárt hurkú, hajtott szupravezető áramkörök dinamikáját vizsgálta.

A mérési adatok (`counts`) és a zajos szimulációk összevetése alapján a fizikai valóság a következő:

### 1. A 37%-os plató tankönyvi kapuzaj
A 4. fázisban (Kerék, $k=32$, ~200 kapu mélység) a hardveren mért mag-populáció **$37.11\%$** (190/512). A Qiskit Aer zajmodellje (depolarizáló kapuhiba és kiolvasási hiba) erre **$37.99\%$**-ot jósolt. Az eltérés mindössze **$-0.88\%$**, ami a statisztikai shot-zajon ($1\sigma$) belül van. A hajtás nem egy egzotikus kvantum-kötött állapotot tart fenn, hanem a depolarizáció a kevert állapot ($P \to 0.5$) felé húzza a qubitet.

### 2. Nincs királis fluxus-előny
Az álló, nem forgó kontroll áramkör (`static`, nulla Peierls fluxus) a hardveren **$45.51\%$**-os értéket adott $k=32$-nél—magasabbat, mint a forgatott hurok ($37.11\%$). A szintetikus fluxus jelenléte semmilyen kimutatható többlettartást nem biztosít.

### 3. A $Z = 13.63$ "Anomália" egy referencia-hiba
A $Z = 13.63$ érték abból adódott, hogy az előzetesen lefagyasztott Aer szimuláció a magára hagyott kontroll áramköröknél nem tartalmazott valós üresjárati $T_1$ lecsengést (így az Aer-ben 55%-on maradtak). A valós hardveren viszont a magára hagyott transzmon természetes $T_1$ ideje miatt lecsurgott ~9–11%-ra. Amikor a hardveres különbséget ($37\% - 9\% = +28\%$) kivonták az elméleti szimuláció hibás különbségéből ($38\% - 55\% = -17\%$), ez egy hatalmas, pusztán matematikai műterméket hozott létre.

### 4. A gerjesztésszám nem maradt meg (Parazita zajgerjesztések)
A többqubites fázisokban (7., 8., 9. fázis), ahol a rendszerbe **egyetlen gerjesztést** írtunk be ($X$ kapu), a kimeneti eloszlásban tömegesen jelentek meg több-gerjesztéses állapotok ($N_\text{exc} \ge 2$). 
- A 9. fázisban a leválasztott hálózatnál a lövések **$32.8\%$**-ában, folyamatos hajtásnál **$55.7\%$**-ában 2, 3 vagy 4 gerjesztés volt jelen egyszerre.
- A 8. fázisban a műholdak összege azért adott **$104.5\%$**-ot, mert a lövések **$25.4\%$**-ában egyszerre több qubit volt 1-es.
A látszólagos "kollektív megtartás" tehát nem az eredeti gerjesztés tárolása, hanem a kapuzaj által pumpált parazita gerjesztések mérése.

### 5. Koherencia hiánya
Az állapot-tomográfia megmutatja, hogy a transzverzális fáziskoherencia $k=32$-re $|\text{coh}_\perp| \approx 0.070$-ra zuhan. A hurok nem képes kvantumbit-fázis vagy tetszőleges szuperpozíció tárolására.

---

## Licenc és Hivatkozás

Ez a szoftver és hardver adatcsomag nyílt forráskódú az MIT Licenc alatt.

```bibtex
@misc{mate2026heron_audit,
  author = {Róbert Máté},
  title = {Quantum Hardware Experiment Series & Comprehensive Noise Audit on IBM Heron Superconducting Processors},
  year = {2026},
  publisher = {Zenodo},
  doi = {10.5281/zenodo.24226150},
  url = {https://github.com/silentnoisehun/triangle-anchor-memory},
  note = {ORCID: 0009-0003-3986-6039}
}
```
