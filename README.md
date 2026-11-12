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

## Állapot: BEKÜLDVE ÉS VISSZAVONVA (mérés nem történt)

**Beküldve 2026-11-11 20:52 UTC; 2026-11-12 tulajdonosi döntéssel
visszavonva (mind a 4 job CANCELLED); mérési adat nem keletkezett; az
állítás eldöntetlen; újraküldés csak külön tulajdonosi döntéssel.**

A négy job (dbqdaupabdes73fo2jrg, dbqdav7v5hds73dfs6mg,
dbqdavhabdes73fo2jug, dbqdavgk09pc73at2da0; ibm_kingston, S=125,
horgonyok 117/124/126; see `data/job_meta.json`) soha nem futott le —
**a mért eredmény nem létezik; semmilyen fizikai állítás nem fogalmazható
meg mérés alapján.** Az újraküldés a tulajdonos külön döntése, kedvezőbb
időpontban, lehetőleg időben tagolva (fair-share); az agent QPU-ra nem
küld. **Semmilyen QPU-futtatás nem indítható az újraküldési döntésig.**

A 0. fázis (szimuláció, ELŐZETES) lezárult; az eredményei Aer/zajtalan
szimulációk — nem hardver-eredmények:

- [x] Repo-váz (ez a fájl, `.gitignore`, `data/` megjelölve nem-ignoroltnak)
- [x] `preregistration/PLAN_v1.0.md` — a terv szó szerinti másolata (SHA-256: `12b22f18c468f05ab5ca10ed0bbb0819ed85e21564f3a3780b51c25508e38775`)
- [x] `src/` csomag: `config`, `circuits`, `sim`, `analysis`, `run` (beküldő), `freeze` (0. fázis fagyasztó)
- [x] `dryrun.py` — QPU nélkül minden végigfuttatható
- [x] 0. fázis szimuláció lezajlott (zajtalan + zajos, **MINTA** zajparaméterekkel)
- [x] `preregistration/frozen_params.json` — φ = π/16, K = 32, csúcs-keresési ablakok, várt görbék, hash-el lezárva
- [~] QPU-futtatás (1. fázis) — **2026-11-11 20:52 UTC-kor beküldve, 2026-11-12-én visszavonva**; mérés nem történt; újraküldés külön tulajdonosi döntéssel

**A QPU-futtatás ÉRVÉNYTELEN (mind a 4 job CANCELLED); mérési adat nem
keletkezett.** A token soha nem kerül fájlba; a `src/run.py` a tokent
kizárólag az `IBM_QUANTUM_TOKEN` környezeti változóból olvassa.
A `data/` mappa szándékosan NINCS `.gitignore`-ban.

### A 0. fázis eredménye (szimuláció, nem hardver!)

- **Zajtalan:** a preregisztrált szabály szerint TEXTBOOK-MEGEROSITVE (P1: 16/11/9 lépés,
  arányok 1.00 / 0.6875 / 0.5625 a `1 : 0.71 : 0.58 ±20%` sávban; P2: CI-alsó ≈ +0.95;
  P3: a `cut` 2 lépéssel eltolódva, CI = [2.00, 2.00]).
- **Pozitív kontroll (csatolások kikapcsolva):** NULL — az elemző helyesen ismeri fel.
- **Zajos (MINTA T1/T2/ε, NEM chip-pillanatfelvétel!):** TEXTBOOK-MEGEROSITVE jött ki a
  minta-paraméterekkel; a minta T2/t_össz ~ 0,3, így a zaj csekély. A leendő
  snapshot.json behelyettesítése után ez megváltozhat; hardver-eredményként **soha**
  nem közölhető.
- **frozen_params.json SHA-256 (v1.0, superseded, változatlan):** `e1d7a78888c531ba8ae7e5f84ed090649f5156774eabd763c8772d5d02d09429`
- **Jelenleg irányadó (v1.2 AMENDED, 99% CI + Holm, 2026-11-12):** `frozen_params_v1.2.json` — SHA-256 a
  `frozen_params_v1.2.sha256`-ben (ellenőrzés: `src/analysis.py` minden futtatáskor; a v1.0 fájlok byte-ra változatlanok)
- A v1.2 a 0. fázis szimulációit nem érinti — csak a döntési magasságot emeli (a csapat döntési szabálya
  minden kísérletre: ANOMALIA csak 99% CI + Holm után). A v1.2 dryrun-ja: **PASS** (zajtalan →
  TEXTBOOK-MEGEROSITVE; φ=0 kontroll → NULL; null-próba 0/300 hamis ANOMALIA és 0/300 hamis TEXTBOOK)
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

A fagyasztott `preregistration/frozen_params.json` (v1.0, történeti) ettől érintetlen
(hash: `e1d7a788…`); a `PLAN_v1.0.md` eltérését a
[`preregistration/ERRATA.md`](preregistration/ERRATA.md) dokumentálja — a fájlt nem írtuk át.
(A jelenleg irányadó fagyasztott fájl: `frozen_params_v1.2.json`, lásd fent.)

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
                   a preregistration/frozen_params_v1.2.json-ből olvassa (hash-ellenőrzéssel; fail-closed, v1.2 kötelező)
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
5. A 0. fázis eredményéig (φ, K, ablakok, görbék) a `frozen_params_v1.2.json` lezárja a paramétereket (v1.2 AMENDED: 99% CI + Holm; a v1.0 superseded).

## A Kerék-menet (forgó gyűrű által tartott középpont)

**Állapot: 0. fázis lefagyasztva, átnézésre vár, beküldés tilos.** A Kerék-menet külön,
v1.1 amended tervre és saját fagyasztásra épül; a csillag- és a gyűrű-
anyaghoz nem nyúl. **Semmilyen QPU-futtatás (teljes Kerék-job, küszöb-job,
gyűrű-job) nem indítható, amíg a 2026-11-12-i 99% CI + Holm amendment és
Maya (Control Agent) átnézése meg nem történt — az átnézésig TILOS.**
PLAN_WHEEL v1.2 most NEM készül (csak akkor, ha Maya átnézése hibát talál —
új hash, külön commit, a v1.1 megtartasávan).

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

## Küszöb-job (Ring-Ramsey) — az első beküldés ERROR 1515 (adat NINCS); v1.3 javítás kész, auditra vár

A Kerék W3 = SZÉTESŐ ágán (a teljes Kerék-QPU-job NEM tervezhető ezen a
négyesen) az egyetlen szóba jövő futtatás a küszöb-job; a csomagja és a
terve elkészült:

- **Terv:** [`preregistration/PLAN_KUSZOB_v1.3.md`](preregistration/PLAN_KUSZOB_v1.3.md)
  (v1.3 AMENDED, 2026-11-12: mérés-hiány javítás — új G8 mérés-kapu; minden egyéb a v1.2-ből öröklődik, ideértve a seed-hash `83f43b94…`-t).
  (a v1.1 AMENDED, 2026-11-12, Maya átnézése: a v1.0
  `initial_layout` [125,117,124,126] hibája javítva → **[117,124,125,126]**,
  `optimization_level = 0`; a döntési szabály (99% Wilson, (a)–(d)) nem
  változott, azóta is lefagyasztott elemzőben él; a v1.0-t és v1.1-et sem
  használhatja senki beküldésre). Ring-Ramsey echo: prep → Peierls-körök → prep†;
  `P_return = P(000)`; automatikus HALASZTÁS-triggerek.
- **Csomag:** [`submission/kuszob/`](submission/kuszob/) — builder
  (`build_kuszob.py`), 17 routolt áramkör (`circuits/`, QASM — v1.0, bitre
  változatlan), kaputilus-tábla, `job_meta.draft_v1.1.json`
  (`job_ids: []`; titkos shuffle seed — a repóban csak a sha256 hash-e:
  `6a68d507…`), lefagyasztott elemző (`analyze_kuszob.py`), agent-oldali
  ellenőrző (`verify_kuszob.py`, **PASS 82/82 + 3 Aer-próba**, 2026-11-12 —
  v1.1-ben új CZ-kapu: minden áramkör CZ-száma/CZ-párjai pontosan a
  manifesttel, eltérés ⇒ HALASZTÁS). Beküldő-szkript is **előkészítve**
  (`submit_kuszob.py` — dry-run: minden gate PASS; a 3 negatív teszt
  (seed-hash / CZ / backend-kapu) mind HALT-ot ad; `--submit` csak külön
  tulajdonosi döntéssel, interaktív megerősítéssel; **QPU nem indult**;
  hash + kapu-rögzítés: `submit_manifest_v1.1.json`).
- **A beküldést az agent SOSEM végzi el** — tulajdonosi/Control Agent
  felülvizsgálat és külön döntés szükséges. A Kerék-menet zárolva marad;
  a küszöb-job kimenete nem írja át a Kerék fagyasztott verdiktjeit.
- **2026-11-12 (v1.3):** az első beküldés (**job `dbqt3q9abdes73fosj8g`, 2026-11-12 14:49 UTC**; ibm_kingston, 17 áramkör, 4096 shot) **19:16 UTC-kor ERROR 1515-tel végzett, adat NÉLKÜL** („Circuits without measurements are not allowed" — a payload mérés nélküli áramköröket tartalmazott; szkript-ok: a v1.2 beküldő a `transpile_pruned()` mérés nélküli áramköreit küldte a `SamplerV2.run()`-nak). **A v1.3 javítás kész** (a payload a `build_kuszob.with_measurements()` után megy a backend-transzpilációra; ÚJ G8 mérés-kapu a run() ELŐTT, mind dry-run, mind submit úton; [PLAN_KUSZOB_v1.3](preregistration/PLAN_KUSZOB_v1.3.md)) — **auditra vár; újraküldés KÜLÖN tulajdonosi/Control Agent döntéssel**. Az agent QPU-t nem indított; tokent nem kezelt; a record-first rekordok (commit `e325f14`) megőrződnek. A v1.2 seed-amendment (hash `83f43b94f6ab5f75d26ffec94af9dceafdd56ae2a7592a2571a57a89dee4b31c`) változatlan érvényű. A küszöb-csomag döntési szabályai 99% CI-sek (PLAN_KUSZOB_v1.3,
  Wilson, egyoldalú; a 95%-szerű találatok forgásszögek, nem küszöbök; a
  `storage_ge_095_check` nevű mező valójában 0.9-os gép-egészség-előkapu,
  nem döntési szabály; a `dip_frac: 0.95` nem CI-döntés). A ROGZUL ítélet
  kötelező jelölése: „gep-alkalmassagi kapu, tankonyvi varakozas” —
  nem memória-teszt.

## Gyűrű-menet (valós háromszög) — v1.1 AMENDED — terv + 0. fázis — QPU még NEM futott

**Beküldési tilalom:** a gyűrűcsomag (mint a Kerék és a küszöb-csomag)
**nem mehet QPU-ra, amíg a 2026-11-12-i 99% CI + Holm amendment át nincs nézve
(Maya) és a tulajdonos külön nem dönt** — az átnézésig TILOS. A csomag
„ELŐKÉSZÍTVE — NEM BEKÜLDVE".

A csillag-menet (**2026-11-12-én tulajdonosi döntéssel visszavonva — semmilyen mérési
adat nem keletkezett; lásd fent**) és a Kerék-/Küszöb-menet
mellé a VALÓDI háromszögre vonatkozó önálló, új menet: a három gyűrű-qubit
Peierls-fluxussal kering; az irányt a fázis hordozza, nem a populáció —
a kérdés az, hogy a keringési irány maga mennyire tárolja a biteket.

- **Terv (jelenlegi):** [`preregistration/PLAN_RING_v1.1.md`](preregistration/PLAN_RING_v1.1.md)
  (**AMENDED**, a v1.0-t felülírja) — kiinduló kép, |k±⟩ sajátállapotok,
  Loschmidt-echo kiolvasás indoklással, C(k) = P(000;+)−P(000;−) kontraszt,
  kontrollok a/b/c/NC, pumpa §4, a döntési szabály bootstrap 2000 /
  **ci = 0.99** / **Holm** a claim-családon [R1, R2, pump, NC]; az ANOMALIA
  determinisztikus binomiális-sávos (z = Φ⁻¹(0.995) = 2.5758).
  A v1.0 (`PLAN_RING_v1.0.md`) **byte-ra változatlanul megmarad** — superseded.
- **Fagyasztott paraméterek (jelenlegi):** [`preregistration/frozen_ring_params_v1.1.json`](preregistration/frozen_ring_params_v1.1.json)
  (SHA-256: `frozen_ring_params_v1.1.sha256`; ellenőrzés: `src/ring/analysis.py:check_frozen`).
  `version = 1.1`, bootstrap ci = 0.99; `K = 32`, rács k ∈ {0,4,…,32}, kipróbálva és
  fagyasztva mind a 7 pump-pár (0/0.1/0.2/0.3 × φ ∈ {0, π/2}); Ω = 0.1387 rad/kör
  a kör-spektrumából. A v1.0 (`frozen_ring_params.json`) **superseded, változatlan**.
- **Kód:** `src/ring/` (áramkör-építők — Peierls-élek, prep/echo megosztva a
  kerék-modullal; szimuláció — exact + snapshot-zajú Aer (native
  illesztett-gyűrűbeli és heavy-hex-routolt recept); elemző — a fagyasztott
  fájlból olvassa a döntési szabályt), `dryrun_ring.py` a gyökérnél.
- **A 0. fázis nettó üzenete (Aer/zajtalan szimuláció, NEM hardware):**
  - a keringési irány ELKÉSZÍTÉSE és KIOLVASÁSA működik a modellben, de az
    ideális echo-metrika (P(000)) a fluxust NEM látja a fluxus-mentes
    referencián (static lapos≈1.0; lone/delayed=1.0; dokumentált, hogy az
    echo-fluxusvakság miatt a keringési ELŐNY helye a két irány közötti
    eltérés, C(k), és a valódi T1/T2-keret);
  - **routing-költség (TÉNYLEGES heavy-hex, S=125 hub, opt=0, seed 1234):
    k=32 → 341 CZ, várható 2Q-hiba ≈ 0.565 — a W3-jellegű 0.5-ös
    küszöb FÖLÖTT.** A teljes K=32 gyűrű-QPU-job ezen a négyesen NEM
    tervezhető koherensen; a k ≤ 16 tartomány (0.291) szóba jöhet; a
    gridöt NEM szűkítjük csendben — a döntés a tulajdonosé;
  - **a szimuláció a Maya-előrejelzés oldalára hajlik** (routed Aer:
    C(32) ≈ 0.21, τ ≈ 2.7 kör; native: C(32) ≈ 0.65, τ ≈ 14 kör) és ezt a
    terv és a fagyasztott fájl is rögzíti a tulajdonos erős várakozása
    mellett (a mérés dönt — ha mérés lesz);
  - **a pumpa-párok NINCSENEK nyereségben**: egyik (m ∈ {0.1…0.3},
    φ_p ∈ {0, π/2}) pár sem ver pumpa nélküli gyűrűt 99% CI-vel + Holm-nal (native
    Aer; a routed-ban a π/2-fázisú pár kicsit rosszabb; az exact ≤ 0.04
    stroboszkopikus különbséget mutat) — a saját ára 96 impulzus × 2e-4 ≈
    0.019, rendben a nyereség nulla alatt; a cáfolati feltétel szerint, ha
    a hardver ugyanezt hozza, a pumpa-ötlet erre a rendszerre megbukott és
    további paraméter-keresés TILOS;
  - a törött gyűrű (NC) és a csillag (visszaáramlás) a szimulációban egyaránt
    HINTÁZIK (oszcillál) — egyik sem keringési bit; az elemzőnek a
    broken-karra NULL-t vár (ez a pozitív kontroll).
- **Szimulációs eredmény sosem hardware-eredmény; a QPU nem futott; az agent
  QPU-t nem indított és nem fog.** A beküldés a tulajdonos/Control Agent
  döntése — a gyökér `dryrun_ring.py` PASS esetén sem; a gyűrű-job
  jelenleg csak ELŐKÉSZÍTÉS stádiumban van, a routing-költség miatt
  valószínűleg a teljes grid NEM megy QPU-ra.

```bash
.venv/bin/python dryrun_ring.py   # QPU nélkül: frozen-v1.1-ellenőrzés + zajtalan +
                                   # routed Aer "mérés", elemző, NC-kontroll,
                                   # null-próba (300×) → elvárt: PASS (13/13)
```
