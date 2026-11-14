# PLAN_DUAL_WHEEL v1.0 — Synchronous Quantum Mesh (Star-Ring-Wheel-Sync)

**Dátum:** 2026-11-14 · **Szerző / PI:** Róbert Máté ([ORCID: 0009-0003-3986-6039](https://orcid.org/0009-0003-3986-6039))  
**Célgép:** IBM Heron r2 (`ibm_marrakesh`), 156-qubit heavy-hex lattice.  
**Fizikai elrendezés (7 qubit):**
- Kerék 1: $S_1 = 125$, $A_1 = 117$, $A_2 = 126$
- Közös Csatoló Híd: $A_{shared} = 124$
- Kerék 2: $S_2 = 123$, $B_1 = 122$, $B_2 = 136$

---

## 1. Hipotézis és Pontos Jóslatok

Ha két ellentétesen cirkuláló kerék ($m_1 = +1, m_2 = -1$) a fizikai $124$-es hídon keresztül csatolódik (Kuramoto-Huygens fáziszár):

1. **Koherens Átfolyási Jóslat (Sync Conduction):**
   - $P(S_2 = 1, k \ge 4) \ge 0.15$ a Sync módban (a gerjesztés átáramlik a hídon).
   - $P(S_2 = 1) \le 0.05$ a No-Sync (izolált) kontrollban (readout alapzaj).

2. **Szinkron Ekvipartíció ($k=8$):**
   - A két központ eléri a fáziszárt egyensúlyt:
     $$|P(S_1) - P(S_2)|_{k=8} \le 0.15$$

3. **Kollektív Háló-Retenció ($k=32$):**
   - A kétcsomópontos kollektív megtartás $P(S_1 = 1 \lor S_2 = 1)_{k=32} \ge 0.35$ (szignifikánsan meghaladja az egyedi lecsengési szintet).

---

## 2. Kísérleti Mátrix (18 áramkör)
- **Karok:**
  1. `sync`: Két kerék ellentétes fázissal + híd-csatolás aktív.
  2. `nosync`: Két kerék, de a híd-csatolás kikapcsolva (negatív kontroll).
- **Lépésrács ($k$):** $[0, 4, 8, 12, 16, 20, 24, 28, 32]$ (9 pont).
- **Lövésszám:** 512 shot / áramkör.
