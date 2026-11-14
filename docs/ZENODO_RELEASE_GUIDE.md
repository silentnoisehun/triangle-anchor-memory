# Zenodo DOI Release & Archiving Guide

Ez az útmutató leírja, hogyan lehet 2 perc alatt megszerezni a permanens, cikkekben és pályázatokban hivatalosan hivatkozható **Zenodo DOI-t** a legfrissebb kiadáshoz a saját ORCID-odhoz (`0009-0003-3986-6039`) kapcsolva.

---

## 1. Lépés: Bejelentkezés a Zenodo-ra
1. Nyisd meg a [zenodo.org](https://zenodo.org/) oldalt.
2. Kattints a **Log in** gombra a jobb felső sarokban.
3. Válaszd a **Log in with GitHub** opciót (azzal a fiókkal, ahol a `silentnoisehun` repó található).

---

## 2. Lépés: GitHub Repó összekapcsolása
1. Menj a profilod legördülő menüjében a **GitHub** menüpontra: [zenodo.org/account/settings/github](https://zenodo.org/account/settings/github).
2. Keresd meg a listában a `silentnoisehun/triangle-anchor-memory` repót.
3. Kapcsold a kapcsolót **ON** (zöld) állásba.

---

## 3. Lépés: Release létrehozása GitHubon
1. Nyisd meg a repót: [github.com/silentnoisehun/triangle-anchor-memory/releases/new](https://github.com/silentnoisehun/triangle-anchor-memory/releases/new).
2. Hozz létre egy új taget: `v2.3.0`.
3. Release title: `v2.3.0: Full 9-Phase Hardware Proof on IBM Heron (1011 Circuits)`.
4. Leírás: Másold be a README összefoglalóját, vagy egyszerűen:
   *Preregistered quantum hardware experiment series across 9 phases (1011 physical circuits) on IBM Heron (ibm_marrakesh and ibm_kingston). Verifies chiral current inversion, non-equilibrium population pinning (Z = 13.63), and distributed reservoir mesh decoupling.*
5. Kattints a **Publish release** gombra!

---

## 4. Eredmény: Automatikus DOI Generálás
A Zenodo másodperceken belül:
- Észleli az új release-t,
- Beolvassa a repóban lévő `.zenodo.json` és `CITATION.cff` fájlokat,
- Automatikusan hozzárendeli a szerző nevéhez és az ORCID-odhoz (`0009-0003-3986-6039`),
- Kiállítja a végleges, megváltoztathatatlan **DOI azonosítót** (`10.5281/zenodo.24226150`).
