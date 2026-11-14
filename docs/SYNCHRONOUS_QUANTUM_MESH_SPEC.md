# Synchronous Quantum Mesh Specification (Star-Ring-Wheel-Sync)

**Verzió:** v1.0-DRAFT  
**Koncepció és Tervezés:** Róbert Máté ([ORCID: 0009-0003-3986-6039](https://orcid.org/0009-0003-3986-6039))  
**Fizikai Platform:** IBM Heron r2 (156-qubit heavy-hex lattice)

---

## 1. Architektúra: A 4 Elem Egysége

A Triangle-Anchor Kvantum Memória kísérletsorozat kimérte a 4 elemi komponenst:
1. **A Csillag (Star):** Hidrodinamikus gerjesztés-terítés a központi qubitből ($S$).
2. **A Gyűrű (Ring):** Peierls-fázisú keringenés ($m = \pm 1$), amely megakadályozza a statikus spin-relaxációt.
3. **A Kerék (Wheel):** Zárt hurkú horgonyzás, amely $Z = 13.63$-as anomális gerjesztés-megtartási platót ($~37\%$) hoz létre.
4. **A Szinkronizáció (Sync):** Több összekapcsolt kerék Kuramoto-Huygens típusú fáziszárása.

```
       [ Wheel 1: S1=125 ]                    [ Wheel 2: S2=123 ]
          /     |     \                          /     |     \
     (117)    (126)   (124) <── SHARED ───>   (124)  (122)   (136)
       \        /       │        ANCHOR          \     /       │
        ========        │                         =====        │
      Ring 1 (m=+1) ────┴──────────────────────── Ring 2 (m=-1)┴─── Sync
```

---

## 2. Heavy-Hex Csatolási Topológia az IBM Heron r2-n

Az IBM Heron r2 processzor (`ibm_marrakesh`) fizikai rácsán a csomópontok természetes méhsejt (hexagon) láncot alkotnak:
- **Kerék 1 Központja:** $S_1 = 125$ (fokszám: 3, szomszédok: $117, 124, 126$)
- **Közös Csatoló Horgony:** $A_{shared} = 124$ (összeköti $125$-öt és $123$-at)
- **Kerék 2 Központja:** $S_2 = 123$ (fokszám: 3, szomszédok: $124, 122, 136$)

Ez a geometria **természetes kétcellás kvantum-tranzisztort / fázis-szinkronizált kettős oszcillátort** képez:
- Nincs szükség virtuális swap-láncokra a két cella között: a $124$-es qubit fizikai éllel kapcsolódik mindkét központhoz!
- A $124$-es csatoló-qubiten a két ellentétesen cirkuláló áram ($m_1 = +1$, $m_2 = -1$) fázis-interferenciát hoz létre, megkötve a gerjesztést a két cella között.

---

## 3. Dinamikai Működés: Kuramoto Kvantum-szinkronizáció

A rendszer Hamilton-operátora a forgó fázis-térben:
$$H_{mesh} = \sum_{i=1}^2 H_{wheel}^{(i)} + J_{sync} \left( a_{124}^\dagger a_{124} \right) + \sum_{\langle i, j \rangle} K_{ij} \sin(\theta_i - \theta_j)$$

### Védelmi Mechanizmus (Autonomous Passive Protection):
1. **Zaj-immunitás:** Ha a Kerék 1-et lokális fluktuáció (pl. flux-zaj vagy dekoherencia) éri, a Kerék 2-ből érkező koherens fázis-áram a $124$-es közös hídon keresztül visszahúzza azt a szinkron állapotba.
2. **Kiterjesztett Élettartam ($k > 32$):** A kétcellás szinkronizáció megduplázza a topológiai csapda effektív térfogatát, lehetővé téve a retenciós plató fennmaradását $k = 64$ vagy $k = 128$ lépésig.
3. **Zéró-Szindróma Dekódolás:** A védelemhez semmilyen közbenső mérésre vagy külső klasszikus dekóderre nincs szükség — a fáziszár tiszta unitér dinamikával jön létre.

---

## 4. Kísérleti Protokoll & Metrikák
- **Bemenet:** $|1\rangle_{S1} |0\rangle_{S2}$ (injektálás az első központba).
- **Megfigyelt Mennyiségek:**
  - $P(S_1 = 1, k)$ és $P(S_2 = 1, k)$ — a gerjesztés átadása és szinkron oszcillációja.
  - $C_{sync}(k) = \langle Z_{S1} Z_{S2} \rangle - \langle Z_{S1} \rangle \langle Z_{S2} \rangle$ — a két központ közötti összefonódási és fázis-korreláció.
  - Retenciós idő: $\tau_{sync}$ összevetve a magányos kerékkel ($\tau_{wheel}$).
