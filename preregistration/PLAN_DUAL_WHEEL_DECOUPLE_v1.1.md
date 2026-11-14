# PLAN_DUAL_WHEEL_DECOUPLE v1.1 — Pump-and-Decouple Autonomous Memory Persistence

**Dátum:** 2026-11-14 · **Szerző / PI:** Róbert Máté ([ORCID: 0009-0003-3986-6039](https://orcid.org/0009-0003-3986-6039))  
**Célgép:** IBM Heron r2 (`ibm_marrakesh`), 156-qubit heavy-hex lattice.  
**Fizikai elrendezés (7 qubit):**
- Kerék 1: $S_1 = 125$, $A_1 = 117$, $A_2 = 126$
- Közös Csatoló Híd: $A_{shared} = 124$
- Kerék 2: $S_2 = 123$, $B_1 = 122$, $B_2 = 136$

---

## 1. Elméleti Hátter & Hipotézis

A Phase 5 sikeresen igazolta a **folyamatosan csatolt szinkron vezetést** ($P(S_2) = 0.3586$, $P(S_1 + S_2) = 0.4805$).
Jelen kiegészítő kísérlet (Amendment v1.1) a valódi **kvantum-memória működési ciklust** teszteli:
1. **Írás / Szinkron pumpálás ($k \le 8$):** A forrás ($S_1$) a közös hídon át áttölti a koherens gerjesztést a vevő kerékbe ($S_2$), elérve a szinkron ekvipartíciót ($k=8$-nál).
2. **Lekapcsolás & Izoláció ($k > 8$):** Az inter-kerék csatolót és a forrást ($S_1$) fizikailag lekapcsoljuk (0 interakció, identity kapuk).
3. **Önálló Memória Megtartás ($k = 8 \dots 32$):** A lekapcsolt Kerék 2 saját belső mag-küllő hurka önmagában tovább kering.

### Formális Jóslatok és Verifikációs Kritériumok

1. **Kézfogási Ekvipartíció a Lekapcsolás Előtt ($k=8$):**
   $$|P(S_1) - P(S_2)|_{k=8} \le 0.15 \quad \text{és} \quad P(S_2)_{k=8} \ge 0.20$$
   *(Bizonyítja a sikeres feltöltést a lekapcsolás pillanatában).*

2. **Autonóm Memória Megtartás ($k=32$ a leválasztott Kerék 2-n):**
   A `hold_wheel2` karon az $S_2$ központ megtartja a gerjesztési platót a $k=32$ mélységig:
   $$P(S_2)_{\text{hold\_wheel2}, k=32} \ge 0.25$$

3. **Topológiai Előny a Tétlen Relaxációval Szemben ($k=32$):**
   A cirkuláló zárt hurok szignifikánsan jobban megőrzi az állapotot, mint a tétlen transzmon dekoherencia:
   $$P(S_2)_{\text{hold\_wheel2}, k=32} - P(S_2)_{\text{hold\_idle}, k=32} \ge 0.05$$

4. **Csatorna Izoláció ($k \ge 12$):**
   A lekapcsolás után a Kerék 1 izolált marad, a híd lezárása megakadályozza a visszacsatolást.

---

## 2. Kísérleti Mátrix (21 áramkör)

- **Három vizsgált kar:**
  1. `hold_wheel2`: $k \le 8$ szinkron pumpa, $k > 8$ izolált autonóm kerék-forgás a 2. cellán.
  2. `hold_idle`: $k \le 8$ szinkron pumpa, $k > 8$ tétlen transzmon relaxáció (negatív kontroll).
  3. `continuous`: Folyamatos csatolt szinkron hálózat végig (pozitív referencia).
- **Lépésrács ($k$):** $[8, 12, 16, 20, 24, 28, 32]$ (7 ellenőrzőpont).
- **Lövésszám:** 512 shot / áramkör (összesen 21 futás, várható futási idő QPU-n ~15 másodperc).
