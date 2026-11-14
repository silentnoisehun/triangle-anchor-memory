# Zenodo DOI Release & Archiving Guide

Ez az útmutató leírja, hogyan lehet 2 perc alatt megszerezni a permanens, cikkekben és pályázatokban hivatalosan hivatkozható **Zenodo DOI-t** a `v2.2.0-decouple` release-hez, a saját ORCID-odhoz (`0009-0003-3986-6039`) kapcsolva.

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
2. Válaszd ki a meglévő taget: `v2.2.0-decouple`.
3. Release title: `v2.2.0-decouple: Full 6-Phase Hardware Proof on IBM Heron`.
4. Leírás: Másold be a README összefoglalóját, vagy egyszerűen:
   *Preregistered quantum memory experiment series on IBM Heron (ibm_marrakesh). Includes all 6 phases: Threshold (ROGZUL), Ring (NULL), Star Hydrodynamics, Wheel Retention (Z=13.63), Dual-Wheel Sync Mesh, and Pump-and-Decouple Autonomous Memory (+15.6% vs idle).*
5. Kattints a **Publish release** gombra!

---

## 4. Eredmény: Automatikus DOI Generálás
A Zenodo másodperceken belül:
- Észleli az új release-t,
- Beolvassa a repóban lévő `.zenodo.json` és `CITATION.cff` fájlokat,
- Automatikusan hozzárendeli a szerző nevéhez és az ORCID-odhoz (`0009-0003-3986-6039`),
- Kiállítja a végleges, megváltoztathatatlan **DOI azonosítót** (pl. `10.5281/zenodo.XXXXXXX`).

Ezt a DOI-t közvetlenül be lehet illeszteni az ArXiv cikkbe és az IBM Quantum Credits pályázatba!
