# PLAN_DIST_MESH v1.0 — Distributed Autonomous Quantum Memory Network (2D Distributed Quantum DRAM)

**Dátum:** 2026-11-14 · **Szerző / PI:** Róbert Máté ([ORCID: 0009-0003-3986-6039](https://orcid.org/0009-0003-3986-6039))  
**Célgép:** IBM Heron r2 (`ibm_marrakesh`), 156-qubit heavy-hex lattice.  
**Fizikai elrendezés (13 qubit, 100% natív élek, zéró SWAP):**
- Központi Mag (Master Router): $S_0 = 125$
- Hidak: $B_{NW} = 117$, $B_{NE} = 126$, $B_S = 124$
- Szatellit 1 (Észak-Nyugat): Mag $S_1 = 105$, küllők $A_1 = 104$, $A_2 = 106$
- Szatellit 2 (Észak-Kelet): Mag $S_2 = 127$, küllők $B_1 = 128$, $B_2 = 137$
- Szatellit 3 (Dél): Mag $S_3 = 123$, küllők $C_1 = 122$, $C_2 = 136$

---

## 1. Elméleti Hátter & Hipotézis

Ez a kísérlet a teljes kutatási program csúcsa: az **Elosztott Autonóm Kvantum-Memória Hálózat (Distributed Quantum DRAM)**:
1. **Írás & 2D Hálózati Sugárzás ($k \le 8$):** A központi mag ($S_0$) a 3 fizikai hídon át egyszerre sugározza szét a gerjesztést a három szatellit magba ($S_1, S_2, S_3$), elérve a 2D elosztott egyensúlyi állapotot $k=8$-nál.
2. **Globális Lekapcsolás ($k=8$):** A forrást ($S_0$) és az összes kommunikációs hidat ($117, 126, 124$) lekapcsoljuk (0 kapu, nulla külső energia, teljes fizikai izoláció).
3. **Elosztott Autonóm Tárolás ($k = 8 \dots 32$):** A három izolált szatellit cella a térben magára hagyva, saját belső zárt hurkaiban keringve **egyidejűleg és autonóm módon csapdába ejti és tárolja a szétsugárzott kvantuminformációt**.

### Formális Jóslatok és Verifikációs Kritériumok

1. **Sikeres Hálózati Feltöltés a Lekapcsolás Előtt ($k=8$):**
   A szatellit magok együttes populációja a lekapcsolási ponton:
   $$P(S_1 \lor S_2 \lor S_3)_{k=8} \ge 0.50$$

2. **Elosztott Autonóm Megtartás a Lekapcsolás Után ($k=32$):**
   A leválasztott hálózaton a három független szatellit cella megtartja a kollektív gerjesztést:
   $$P(S_1 \lor S_2 \lor S_3)_{\text{hold\_mesh}, k=32} \ge 0.40$$

3. **Topológiai Hálózati Előny a Tétlen Relaxációval Szemben ($k=32$):**
   Az autonóm hurkolt hálózat szignifikánsan felülmúlja a tétlen transzmon dekoherenciát:
   $$P(S_1 \lor S_2 \lor S_3)_{\text{hold\_mesh}, k=32} - P(S_1 \lor S_2 \lor S_3)_{\text{hold\_idle}, k=32} \ge 0.10$$

---

## 2. Kísérleti Mátrix (21 áramkör)

- **Három vizsgált kar:**
  1. `hold_mesh`: $k \le 8$ szinkron sugárzás, $k > 8$ globális lekapcsolás és 3-cellás autonóm tárolás.
  2. `hold_idle`: $k \le 8$ szinkron sugárzás, $k > 8$ tétlen transzmon relaxáció (negatív kontroll).
  3. `continuous`: Folyamatosan hajtott hálózat végig (referencia bázis).
- **Lépésrács ($k$):** $[8, 12, 16, 20, 24, 28, 32]$ (7 ellenőrzőpont).
- **Lövésszám:** 512 shot / áramkör (összesen 21 futás, várható futási idő QPU-n ~12-14 másodperc).
