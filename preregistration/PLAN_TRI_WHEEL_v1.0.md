# PLAN_TRI_WHEEL v1.0 — Tri-Wheel Quantum Bus (3-Cell Topological Mesh)

**Dátum:** 2026-11-14 · **Szerző / PI:** Róbert Máté ([ORCID: 0009-0003-3986-6039](https://orcid.org/0009-0003-3986-6039))  
**Célgép:** IBM Heron r2 (`ibm_marrakesh`), 156-qubit heavy-hex lattice.  
**Fizikai elrendezés (10 qubit, 100% natív élek):**
- Kerék 1 (Adó): $S_1 = 105$, $A_1 = 104$, $A_2 = 106$, Híd 1 = $117$
- Kerék 2 (Relé): $S_2 = 125$, Híd 1 = $117$, $B_1 = 126$, Híd 2 = $124$
- Kerék 3 (Vevő): $S_3 = 123$, Híd 2 = $124$, $C_1 = 122$, $C_2 = 136$

---

## 1. Elméleti Hátter & Hipotézis

A 4. Fázis igazolta a Kerék topológiai retencióját ($Z = 13.63$), az 5. Fázis a kétcellás szinkron vezetést ($P(S_2) = 0.3586$), a 6. Fázis pedig az autonóm tárolást ($\Delta = +15.6\%$).

Jelen kísérlet a **3-cellás Kvantum-Busz (Topológiai Távvezeték / Repeater)** működését bizonyítja:
1. **Gerjesztés injektálása $S_1$-nél (105):** A bal szélső cella feltöltődik ($P(S_1)=1.0, P(S_2)=0, P(S_3)=0$).
2. **Kétlépcsős koherens transzport ($S_1 \rightarrow S_2 \rightarrow S_3$):** A gerjesztés a 117-es hídon át eléri a központi relét ($S_2 = 125$), majd a 124-es hídon át a célállomást ($S_3 = 123$).
3. **Háromoldalú Szinkron Ekvipartíció ($k \ge 12$):** A három ellentétes kiralitású hurok Kuramoto-fáziszárba áll, és mindhárom magban azonos valószínűségi plató alakul ki.

### Formális Jóslatok és Verifikációs Kritériumok

1. **Végpont-Vezetés a Távvezetéken (End-to-End Conduction to $S_3$):**
   A szinkronizált távvezetéken a gerjesztés átjut a 3. magba ($S_3 = 123$):
   $$\text{Mean}_{k \ge 8} P(S_3)_{\text{sync}} \ge 0.15$$
   míg a lezárt `nosync` kontrollban $P(S_3) \le 0.05$.

2. **Háromoldalú Ekvipartíció ($k=16$-nál):**
   A három központ közötti maximális eltérés a szinkron platón korlátos marad:
   $$\max(|P(S_1)-P(S_2)|, |P(S_2)-P(S_3)|, |P(S_1)-P(S_3)|)_{k=16} \le 0.15$$

3. **Kollektív 10-qubites Háló-Retenció ($k=32$):**
   A 3-cellás hálózat kollektív gerjesztése $k=32$ lépésnél:
   $$P(S_1 \lor S_2 \lor S_3)_{k=32} \ge 0.35$$

---

## 2. Kísérleti Mátrix (18 áramkör)

- **Karok:**
  1. `sync`: Három cella felváltva forgó fázissal (+1, -1, +1) + inter-hub csatolások aktívak.
  2. `nosync`: Három cella, de a hidak le vannak zárva (negatív kontroll).
- **Lépésrács ($k$):** $[0, 4, 8, 12, 16, 20, 24, 28, 32]$ (9 ellenőrzőpont).
- **Lövésszám:** 512 shot / áramkör (összesen 18 futás, várható futási idő QPU-n ~10-12 másodperc).
