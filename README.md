# triangle-anchor-memory

**Háromszög-horgony memória** — preregisztrált kvantumkísérlet IBM Heron-chipre:
egy központi qubit (S) három,
rögzített kezdőállapotú szomszédos horgonyhoz (A1, A2, A3) részleges
SWAP-csatolásokkal („gumikkal") kötve — a kérdés az, hogy ezzel a
geometriával a S-be írt gerjesztés **visszaáramlása** erősödik-e és
gyorsul-e. A teljes, kötelező érvényű tervet lásd:
[`preregistration/PLAN_v1.0.md`](preregistration/PLAN_v1.0.md).

A kísérlettervet **Máté Róbert** ötlete alapján a Control Agent szigorította;
futtatás előtt rögzítve, döntési szabályai utólag nem módosíthatók.

## Állapot: 0. fázis készül

- [x] Repo-váz (ez a fájl, `.gitignore`, `data/` megjelölve nem-ignoroltnak)
- [x] `preregistration/PLAN_v1.0.md` — a terv szó szerinti másolata (SHA-256: `12b22f18c468f05ab5ca10ed0bbb0819ed85e21564f3a3780b51c25508e38775`)
- [x] `src/` csomag: `config`, `circuits`, `sim`, `analysis`, `run` (beküldő), `freeze` (0. fázis fagyasztó)
- [x] `dryrun.py` — QPU nélkül minden végigfuttatható
- [x] 0. fázis szimuláció lezajlott (zajtalan + zajos, **MINTA** zajparaméterekkel)
- [x] `preregistration/frozen_params.json` — φ = π/16, K = 32, csúcs-keresési ablakok, várt görbék, hash-el lezárva
- [ ] QPU-futtatás (1. fázis) — **NEM az agent dolga**: a Control Agent végzi audit után

**A QPU-futtatás még nem történt meg.** A token soha nem kerül fájlba; a
`src/run.py` a tokent kizárólag az `IBM_QUANTUM_TOKEN` környezeti változóból
olvassa. A `data/` mappa szándékosan NINCS `.gitignore`-ban.

### A 0. fázis eredménye (szimuláció, nem hardver!)

- **Zajtalan:** a preregisztrált szabály szerint TEXTBOOK-MEGEROSITVE (P1: 16/11/9 lépés,
  arányok 1.00 / 0.6875 / 0.5625 a `1 : 0.71 : 0.58 ±20%` sávban; P2: CI-alsó ≈ +0.95;
  P3: a `cut` 2 lépéssel eltolódva, CI = [2.00, 2.00]).
- **Pozitív kontroll (csatolások kikapcsolva):** NULL — az elemző helyesen ismeri fel.
- **Zajos (MINTA T1/T2/ε, NEM chip-pillanatfelvétel!):** TEXTBOOK-MEGEROSITVE jött ki a
  minta-paraméterekkel; a minta T2/t_össz ~ 0,3, így a zaj csekély. A leendő
  snapshot.json behelyettesítése után ez megváltozhat; hardver-eredményként **soha**
  nem közölhető.
- **frozen_params.json SHA-256:** `e1d7a78888c531ba8ae7e5f84ed090649f5156774eabd763c8772d5d02d09429`
  (ellenőrzés: `src/analysis.py` minden futtatáskor; a hash-fájl: `preregistration/frozen_params.sha256`)
- [x] Control Agent audit (2026-11-11) — a run.py/kalibráció/snapshot kellékek kódbeli javításai elkészültek (lásd „1. fázis előkészítése"); QPU-hívást továbbra sem indítunk
- [x] `preregistration/ERRATA.md` — a PLAN_v1.0.md 195. sorának dokumentált eltérése (a fájlt nem módosítottuk)

A koherencia-ág eredményeit a `dryrun.py` külön, „MÁSODLAGOS" jelöléssel írja ki — a fő ítéletbe nem számítanak bele.

## 1. fázis előkészítése (Control Agent audit, 2026-11-11)

Az audit kizárólag kódbeli javításokat kért; QPU-hívás nem történt és nem is történhet innen.

1. **Backend- és qubit-választás (`src/run.py`):** valódi, `operational` Heron-backendek
   a futtató környezetből, csatorna `ibm_quantum_platform`. S kiválasztása a terv 3.1
   pontozása szerint — `min(T1,T2)/(1+20ε)` µs-ben, **ε = a qubit incidens 2Q-kapu-hibáinak
   maximuma** (dokumentált döntés; az `eps_readout` külön kerül a snapshotba, a pontozásnak
   nem része) —, S-nek ≥3 fizikai szomszédja kell legyen; pontszám = S-pont ×
   min(három horgony-pont). A rendszer rangsort ad (top 10) és a legjobbat választja;
   `IBM_QUANTUM_BACKEND` csak a rangsorolt Heron-backendek között engedélyezett felülbírálás.
   A végleges elrendezés a `transpile(..., initial_layout=[S,A1,A2,A3], optimization_level=0)`
   lépésben rögzítve — a 0. szint szándékos (az üres időrések időzítése nem optimalizálható el).
2. **Kalibráció ugyanabban a jobban, a karok ELÉ:** T1, Hahn-T2 és kiolvasás mind a 4
   qubitre (késleltetések: 0, 20, 50, 100, 150, 200, 300 µs) + φ_eff minden S–Ai párra
   (k = 0…32) = **163 kalibrációs áramkör**, utánuk a 594 kar seedelt shuffle-lel
   (SHUFFLE_SEED = 20261111) → **összesen 757 áramkör egy jobban** (terv: egyetlen job,
   egyetlen napi kalibráció).
3. **Pillanatkép a beküldéskor:** a `data/snapshot.json` a job indítása ELŐTT íródik —
   T1/T2/ε mind a 4 érintett qubitre, `dt_s`, teljes `coupling_map`, 2Q-párok hibái,
   kapuidők, backend-név és a kiválasztási rangsor. A fájl a `sim.validate_snapshot()`-en
   megy át beküldés előtt, tehát **egy az egyben behelyettesíthető** a zajmodellbe
   (`src/sim.py: load_noise_snapshot('data/snapshot.json')`).
4. **`fetch_raw_counts()` ténylegesen kiolvassa** a SamplerV2 countsait a job_meta
   `order` listájával azonos sorrendben, név szerint (`t1|S|d100us`, `phi_eff|A2|k9`,
   `n3|population|1|k17` …), teljességet ellenőriz (a 594 kar-slot mindegyike feltöltött?),
   `data/raw_counts.json`-t ír (atomikusan), és a hash-t `data/raw_counts.sha256`-ba.
   A `job_meta.json`-t SOHA nem írja újra. Üres helyőrző NINCS — hibás/szinkronvesztett
   eredmény esetén a szkript leáll, adatot nem ír.
5. **Új forrásfájl:** `src/circuits.py` → `build_pair_pswap_circuit()` (φ_eff kalibráció).

### Futásidő-becslés (757 áramkör × shots) — és hogy fér-e egy jobba

Az átlagos kapu-/mérési idő kar-áramkörönként, a 0. fázis minta-időtartamaival
(PSWAP/kitöltő slot = 0,3 µs, 1Q = 0,05 µs, kiolvasás ≈ 0,8–1 µs):

| rész | áramkörök | átlagos mélység* | lövés | kapuidő-összeg |
|---|---|---|---|---|
| Karok (6 kar × (2·33 + 33)) | 594 | ≈ 0,9 µs × E[k=16] + ≈ 1,3 µs ≈ **15,7 µs** | 4096 | ≈ 38 s |
| T1/Hahn-T2 (4 qubit × 7 késleltetés × 2) | 56 | Σ késleltetés = 820 µs/lövés/qubit | 4096 | ≈ 27 s |
| φ_eff (3 pár × 33 k) | 99 | Σ ≈ 158 µs/pár/lövés | 4096 | ≈ 2 s |
| Kiolvasás (8) | 8 | ≈ 1 µs | 4096 | < 1 s |
| **Összesen (tiszta kvantumidő)** | **757** | | | **≈ 67–70 s** |

Ez egy **alsó korlát** — nem tartalmazza a per-lövés állandó overhead-et (kiolvasási
befejezés, reset, átvitel, job-validáció). Ha a tényleges futásidejű overhead `α`
másodperc lövésenként, akkor a végrehajtási idő ≈ `70 s + 757 × 4096 × α`. Például
`α = 20 µs` → **≈ 2 perc**; `α = 100 µs` → **≈ 6,2 perc**; `α = 300 µs` →
**≈ 17 perc** (a sorban állás és a QPU napi kalibrációja szándékosan nincs benne; azt
előre nem lehet megbecsülni).

**Egy jobba fér?** Igen, a terv ezt követeli, és az áramkörszám (757) triviálisan a
szokásos per-job korlátok alatt van. A lövésszám × időtartam azonban **fiók/előfizetés-
függő**, és beküldés előtt a Control Agentnek ellenőriznie kell (IBM Quantum fiók-limits:
kör/job, lövés/job, végrehajtási falidő/job). **Ha nem fér: a karok maradnak EGY jobban,
és egyedül a shots csökkenthető (4096 → 2048/1024 — a futásidő lineárisan arányos,
statisztikai erő csökken).** Lövéscsökkentés előtt jelenteni kell a tulajdonosnak —
az nem a Control Agent vagy az agent önálló döntése.

A fagyasztott `preregistration/frozen_params.json` ettől érintetlen
(hash: `e1d7a788…`); a `PLAN_v1.0.md` eltérését a
[`preregistration/ERRATA.md`](preregistration/ERRATA.md) dokumentálja — a fájlt nem írtuk át.

## Gyors indítás (0. fázis, QPU nélkül)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m src.freeze     # EGYSZER: fagyasztás + hash (preregistration/)
.venv/bin/python dryrun.py         # elvárt: zajtalan → TEXTBOOK-MEGEROSITVE, kontroll → NULL
```

## Repo-váz (terv 7. fejezete szerint)

```
preregistration/   a terv + a 0. fázis utáni befagyasztott paraméterek (hash-el)
                   + ERRATA.md (a PLAN_v1.0.md 195. sorának dokumentált eltérése — a fájlt NEM módosítjuk)
src/config.py      φ, K, karok, referencia-döntési értékek, MINTA zajparaméterek
src/circuits.py    kar-építők + kalibrációs áramkörök (T1, Hahn-T2, kiolvasás, φ_eff) + φ_eff párkörök
src/sim.py         zajtalan + zajos (T1/T2/ε) szimuláció; várt görbék; pozitív kontroll
src/analysis.py    D(k), BLP, csúcskeresés, bootstrap CI, ítélet — a döntési szabályt
                   a preregistration/frozen_params.json-ból olvassa (hash-ellenőrzéssel)
src/run.py         beküldő — tokent CSAK környezeti változóból olvas (Control Agent audit után futtatható)
src/freeze.py      a 0. fázis fagyasztó-eszköze (egyszer fut le)
dryrun.py          QPU nélkül minden végigfuttat
data/              job_meta.json, raw_counts.json, snapshot.json, raw_counts.sha256 (NEM gitignore-olt!)
```

## Sémák

A leendő chip-pillanatkép (`snapshot.json`) sémája a `src/config.py`-ben
(`SNAPSHOT_SCHEMA_DOC`) rögzítve; a zajmodell egy az egyben behelyettesíthető
(a `src/sim.py: load_noise_snapshot(path=...)` path-argumentummal). A 0. fázis
zajos eredményei **MINTA paraméterekkel** készülnek és **nem** hardware-eredmények.

A `data/raw_counts.json` várt sémáját a [`data/README.md`](data/README.md) rögzíti.

## Szabályok (megszegésük = a feladat elbukott)

1. QPU-futtatást senki nem indít; tokent senki nem ír fájlba.
2. A döntési szabály a preregisztrált fájlból olvasódik; utólag nem módosítható.
3. `data/` sosem kerül `.gitignore`-ba.
4. Szimulációs eredmény soha nem kap „HARDWARE" címkét.
5. A 0. fázis eredményéig (φ, K, ablakok, görbék) a `frozen_params.json` lezárja a paramétereket.

## A Kerék-menet (forgó gyűrű által tartott középpont)

**Állapot: terv + 0. fázis — QPU még nem futott.** A Kerék-menet külön,
v1.1 amended tervre és saját fagyasztásra épül; a csillag- és a gyűrű-
anyaghoz nem nyúl.

- **Terv:** [`preregistration/PLAN_WHEEL_v1.0.md`](preregistration/PLAN_WHEEL_v1.0.md)
  (transport) és [`preregistration/PLAN_WHEEL_v1.1.md`](preregistration/PLAN_WHEEL_v1.1.md)
  (**amended**, a fagyasztás alapja; a v1.0 változatlanul hagyva — soha nem
  fagyott le; a v1.1 az első és eddigi egyetlen fagyasztott Kerék-verzió).
- **Fagyasztott paraméterek:** [`preregistration/frozen_wheel_params.json`](preregistration/frozen_wheel_params.json)
  (SHA-256: `frozen_wheel_params.sha256`, ellenőrzés: `src/wheel/analysis.py:check_frozen`).
  `ci_level = 0.99`, `correction = "holm"`, állítás-család:
  **W1, W2, W4-másodlagos, sötétállapot-teszt**.
- **Kód:** `src/wheel/` (áramkörök, snapshot-zajmodell, szimuláció, elemző,
  W3-számítás, kaputilus-tábla generátor); `dryrun_wheel.py` a gyökérnél.
- **A 0. fázis nettó üzenete (Aer/zajtalan szimuláció, NEM hardware):**
  - az ibm_kingston heavy-hex rácsban NINCS háromszög (0 db 3-klik; a
    125-ös középpont körül a gyűrű csak SWAP-hálózattal routolható,
    a csillag-menet layoutján — routing a tényeleges transzpilált
    áramkörökből, opt=0 mellett, minden karra azonos 700 CZ);
  - **W3 = SZÉTESŐ**: a várható 2Q-hiba 1.05 / teljes áramkör (küszöb 0.5);
    a tárolási padló (0.51–0.62) és a flux-lock (arány 214) teljesül.
    **A teljes QPU-job NEM tervezhető**; csak a kis kuszöb-job (gyűrű
    önmagában, néhány lépés) jöhet szóba — és az is kizárólag a
    tulajdonos/Control Agent beküldésével; a kerék-állitas a következő,
    erősebb csatolású qubit-négyesre vagy javított routingra vár;
  - a szimuláció a Maya-előrejelzés (küllők kioltják egymást; W1/W2
    várhatóan NULL) oldalára hajlik, és ezt a várakozást a terv és a
    fagyasztott fájl is rögzíti a tulajdonos erős várakozása mellett —
    a mérés dönt, ha mérés lesz;
  - a pozitív kontroll (beépített Ry-stabilizáló hatás) az elemző által
    kimutatható; a `cut` (kitört gyűrű) negatív kontrollként NULL-t ad.
- **Szimulációs eredmény sosem hardware-eredmény; a QPU nem futott; az agent
  QPU-t nem indított és nem fog.**

```bash
.venv/bin/python dryrun_wheel.py   # QPU nélkül: zajtalan + Aer-routolt "mérés",
                                    # pozitív/negatív kontroll, W3-verdikt → elvárt: PASS
```
