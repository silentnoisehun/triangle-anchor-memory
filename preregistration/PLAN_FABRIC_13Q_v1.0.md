# PLAN_FABRIC_13Q v1.0 — 13-Qubit 2D Quantum Space-Fabric (Breathing Soliton & Omni-Directional Conduction)

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

Ez a kísérlet a **2D Kvantum Tér-Szövet (2D Quantum Space-Fabric)** alapvető fizikai működését demonstrálja a heavy-hex hálózaton:
1. **Izotróp 2D Kvantum-Szökőkút ($k=12$):** A központi magba ($S_0$) injektált gerjesztés a három 120°-os szimmetriájú fizikai hídon át egyszerre áramlik ki mindhárom környező szatellit magba ($S_1, S_2, S_3$), és ott izotróp egyensúlyt alakít ki ($P(S_1) \approx P(S_2) \approx P(S_3) \ge 0.15$).
2. **2D Kvantum Lélegző Szoliton (Refókuszálás $k=28$-nál):** A fázisforgatás hatására a szétterjedt gerjesztés a peremről koherensen visszacsatolódik, és a központi magban fókuszált csúcsot alkot ($P(S_0) \ge 0.50$).
3. **Zárt Kontroll (`nosync`):** A hidak lezárása esetén a szatellitekbe zéró gerjesztés jut ($P(S_1) = P(S_2) = P(S_3) \le 0.05$).

---

## 2. Formális Jóslatok és Verifikációs Kritériumok

1. **Izotróp 2D Emisszió ($k=12$):**
   Mindhárom szatellit mag egyszerre és szimmetrikusan veszi át a gerjesztést:
   $$\min(P(S_1), P(S_2), P(S_3))_{k=12} \ge 0.15$$
   és az eltérésük kicsi:
   $$\max(|P(S_1)-P(S_2)|, |P(S_2)-P(S_3)|, |P(S_1)-P(S_3)|)_{k=12} \le 0.10$$

2. **2D Koherens Refókuszálás ($k=28$):**
   A gerjesztés visszahullik a központba, fókuszált maximumot adva:
   $$P(S_0)_{k=28} \ge 0.50$$

3. **Csatorna Izoláció (`nosync`):**
   $$\text{Mean}_{k \ge 8} P(S_1 \lor S_2 \lor S_3)_{\text{nosync}} \le 0.05$$

---

## 3. Kísérleti Mátrix (18 áramkör)

- **Karok:**
  1. `sync`: Teljes 13-qubites 2D tér-szövet aktív hidakkal.
  2. `nosync`: Csak a központi mag aktív, hidak zárva (negatív kontroll).
- **Lépésrács ($k$):** $[0, 4, 8, 12, 16, 20, 24, 28, 32]$ (9 ellenőrzőpont).
- **Lövésszám:** 512 shot / áramkör (összesen 18 futás, várható futási idő QPU-n ~10-12 másodperc).
