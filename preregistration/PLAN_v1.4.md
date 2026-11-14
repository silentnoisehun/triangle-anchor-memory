# PLAN v1.4 — AMENDED (felülírja a v1.0-t, v1.1-et, v1.2-t és a v1.3-at)

**EZ A FÁJL AMENDMENT.** A `PLAN_v1.0.md`, a `PLAN_v1.1.md` és a `PLAN_v1.2.md`,
valamint a `frozen_params.json`, `frozen_params_v1.2.json` és a hozzájuk tartozó
`.sha256` fájlok **byte-ra változatlanul maradnak** — csendben átírni TILOS.
A v1.3 a v1.2-t **felülírja** (superseded). Ez az amendment **mérés ELŐTTI** —
a négy csillag-job a 2026-11-12-ei tulajdonosi döntéssel visszavonva (mind
CANCELLED), **mérési adat nem keletkezett**. Az újraküldés csak külön
tulajdonosi döntéssel, a `src/run.py`-n keresztül történhet.

**Forrás:** Maya beküldés előtti átnézése (2026-11-12 09:05 UTC),
`agent_feladat_csillag_v13.txt` formájában. A hiba: null-adaton
(coupling_scale = 0) 600 futásból **8 hamis ANOMALIA (1,33%; cél ≤ 1%)**.
Ok: `src/analysis.py` (~402. sor a v1.2-ben): ahol a bootstrap-mintában nincs
csúcs (A = NaN), a kód a mintát **kidobta**, és a 99%-os alsó határt csak a
véletlenül csúcsot adó mintákból számolta. A P3 shift-CI NaN-ja ugyanebből a
"nincs csúcs" jelzőértékből jön (`find_return_peak` None), nem számítási
hibából.

## Mi változott és miért (v1.2 → v1.3)

1. **Új fagyasztott fájl:** `preregistration/frozen_params_v1.4.json`
   (+ `frozen_params_v1.4.sha256`). Claim-család változatlanul
   `["P2", "P3", "anomaly"]`; `ci_level = 0.99`; `correction = "holm"`;
   `alpha = 0.01`. Az elemző (`src/analysis.py`) **ÉS** a dryrun
   (`dryrun.py`) **sha256-ja is bekerül** a frozen JSON `file_hashes`
   mezőjébe, és a verifikáció (`verify_frozen_fields`) **visszaellenőrzi**
   a fájlokat — eltérés esetén az elemzés nem fut le (fail-closed, Maya 5.).
2. **Anomália-ág javítása** (`src/analysis.py`):
   - Ha a pontbecslésben nincs csúcs: az ág eredménye **"nincs anomalia,
     ok: nincs csúcs"** (`peak_found: false` külön mezőben — sosem NaN egy CI-ben).
   - A csúcs nélküli bootstrap-minták **"nincs anomalia" mintákként
     számítanak** (A := −∞), **nem esnek ki**.
   - A percentilis **sosem interpolál végtelenek között**: az alsó
     határ `np.quantile(samples, q, method="lower")`-rel számoltatik
     a −∞-mintákkal **együtt**.
   - A p-érték: `(samples <= bound).mean()` az **ÖSSZES** mintán.
   - A bootstrap A-CI (`A_vissza_ci99`) szintén a −∞-mintákkal együtt,
     `method="lower"`-rel készül.
3. **Fail-closed szabály** (`src/analysis.py`):
   - Az elemző `np.errstate(all="raise")` alatt fut
     (`analyze_dataset` burkolta; a `main` lebegőpontos kivételre
     `ELEMZO-HIBA / ERVENYTELEN`-t ír és 3-as kóddal lép ki).
   - Ha egy **csúcsot váró karon** (a fagyasztott ablak nem null:
     `n1, n2, n3, cut, noisy`) a pontbecslés NaN → **ITÉLET =
     `ELEMZO-HIBA / ERVENYTELEN`**, nem NULL. (Az `n0` alapvonal ablak
     nélküli — nem csúcs-váró.)
   - A `"nincs csúcs"` külön mező (`peak_found: false`) a karonként és az
     anomália-részletben is; + `n_peakless_bootstrap` (hány bootstrap-minta
     volt csúcs nélküli).
4. **Karhossz-kiegyenlítés** (`src/circuits.py`, `src/kingston_routing.py`):
   minden karba üres várakozás (`delay ... unit="dt"`) szúratik a mérés elé,
   hogy minden kar ALAP-hossza a közös cél-idővel egyezzen, **k-nként**,
   mind a három (branch, init) csoporthoz és mindkét coupling_scale-en.
   A cél-idő alapból az `n3` kar ütemezett hossza; **dokumentált kivétel:**
   a `population / init="0"` csoportban a `noisy` kar horgony-H szintézise
   **minden k-ra pontosan 8 dt-vel (1 sx = 32 ns) hosszabb** az n3-nál —
   a leghosszabb kart utólag nem lehet rövidíteni, ezért ott a cél-idő a
   `noisy` hossza (mérés: a 0..32 k-k mindegyikére Δ = +8 dt; a többi
   csoportban n3 a leghosszabb). Így minden kar azonos hosszon fut minden
   k-ra. A dryrun **kötelező PASS-pontja:** transpile + ALAP után
   **|hossz(arm) − cél| ≤ 1 dt minden k-ra** (jelentésben:
   6 kar × 3 csoport × 33 k × 2 coupling_scale = 1188 sor).
5. **Dryrun-bővítés** (`dryrun.py`):
   - **≥ 600 null** (coupling_scale = 0.0) **ÉS ≥ 600 tankönyvi** újraminta
     (coupling_scale = 1.0), **FakeKingston-routolt Aer-valószínűségekből**,
     **4096 lövéssel**. A routed valószínűségek: transpile+ALAP
     (initial_layout=[125,117,124,126], optimization_level=0, ALAP, seed 1234)
     → a 156q körpéldány S–Ai qubitjeire kivágott helyi 4-qubitos áramkör
     → Aer `density_matrix` a FakeKingston-kalibrációból épített zajmodellel
     (sx/x/cz: termál relaxáció a kapuidőre + depolarizáció a target-hibával;
     rz zajtalan; kiolvasási hiba analitikus, szimmetrikus vetítése),
     majd binomiális szintézés 4096 lövéssel.
     **A teljes 156-qubitos density_matrix-szimuláció nem futtatható
     (memória) — ezért a 4q-re redukált, routed időzítést kivágásként
     átvevő megközelítés.**
   - **Követelmények:** hamis ANOMALIA ≤ 1% (**≤ 6/600**) **ÉS** hamis
     TEXTBOOK (null-on) ≤ 1% (**≤ 6/600**).
   - **Regressziós seedek rögzítve:** 9003, 9022, 9117, 9156, 9189, 9244,
     9489, 9574 — ezekben jelent meg a hamis ANOMALIA a v1.2 mérésében.
     Mindegyikük külön ellenőriztetik; **ha bármelyik ANOMALIA vagy
     TEXTBOOK: ÁLLJ MEG**.
   - **Ha bármely követelmény nem teljesül: ÁLLJ MEG és jelentsd —
     a küszöb utólagos lazítása TILOS.**
6. **A pozitív kontroll (φ=0) elvárása megváltozik** a fail-closed szabály
   miatt: a zajtalan kontroll `D(k) ≡ konstans`, nincs dip, nincs csúcs →
   a pontbecslések NaN → **ÍTÉLET = `ELEMZO-HIBA / ERVENYTELEN`** (vagy, ha a
   lövés-zaj szándékosan csúcsot ad, `NULL`). **TEXTBOOK és ANOMALIA SOHA.**
   A dryrun kapuja ezért: `verdict ∉ {TEXTBOOK, ANOMALIA}`. (A v1.2-ben az
   elvárt `NULL` volt; ez a fail-closed szabály közvetlen következménye,
   Maya átnézésének 3. pontjából — külön jelezve a jelentésben.)
7. **Beküldési tilalom változatlan:** újraküldés CSAK külön tulajdonosi
   döntéssel; az agent QPU-ra NEM küld; a token csak az
   `IBM_QUANTUM_TOKEN` környezeti változónév; a v1.3 merge-elése sem
   jogosít beküldésre. A `initial_layout = [125, 117, 124, 126]`, a
   `job_meta.json` és a record-first rend (új `job_meta`, a beküldött állapot
   külön commitba az eredmény letöltése előtt) a 6. pont szerinti **későbbi**
   tulajdonosi döntésre vár — MOST NEM történik.
8. **Semmi más nem változik:** φ = π/16, K = 32, ablakok, P1 (±20%
   pontbecslés-tűrés, NEM CI-döntés), P2/P3 szabályok, dip_frac = 0.95,
   bootstrap 2000× (seed 20261111, ci_level 0.99), koherencia-ág
   (MÁSODLAGOS, nem része a fő ítéletnek), az `n0` alapvonal, az
   `anomaly_reference` (populáció = minden kar 1.0, az unitér maximum),
   a claim-család és a Holm-szabály.

A továbbiakban a v1.2 szövege él, a fenti explicit módosításokkal.
Szimulációs eredmény SOHA nem kap „HARDWARE" címkét. NULL-t NULL-ként
jelentünk.

---

## A v1.3 szerinti döntési szabály (4. fejezet átírva)

- **ÍTÉLET-VÁLASZTÉK:** `TEXTBOOK-MEGEROSITVE` | `NULL` | `ANOMALIA` |
  **`ELEMZO-HIBA / ERVENYTELEN`**.
- **Fail-closed:** csúcsot váró kar (n1, n2, n3, cut, noisy) pontbecslés-NaN
  ⇒ `ELEMZO-HIBA / ERVENYTELEN`. A kód `np.errstate(all="raise")` alatt fut.
- **ANOMALIA:** kar A_vissza- bootstrap-CI alsó határa (az ÖSSZES minta,
  csúcs nélküliek A := −∞, `quantile(method="lower")`) meghaladja a fagyasztott
  unitér maximumot ÉS a claim Holm után szignifikáns. A "nincs csúcs" külön
  mező (`peak_found: false`); sosem NaN egy döntési CI-ben.
- **NULL (a geometria nem segít):** minden egyéb eset, ahol nincs
  ELEMZO-HIBA és nincs szignifikáns ANOMALIA — beleértve azt is, ha P1/P2/P3
  nem mindegyike teljesül.
- **TEXTBOOK–MEGERŐSÍTVE:** P1 ∧ P2 ∧ P3 mind teljesül (99% CI + Holm) és
  nincs ELEMZO-HIBA és nincs szignifikáns ANOMALIA.
- A koherencia-ág továbbra is MÁSODLAGOS, külön blokkban, nem része a fő
  ítéletnek.

## A v1.3 szerinti 0. fázis (5. fejezet átírva)

- Zajtalan és zajos (minta-pillanatkép) szimuláció minden karra, a
  karhosszal kiegyenlített áramkörökön (S0. fázis).
- Pozitív kontroll (coupling_scale = 0.0): a fail-closed szabály szerint
  `ELEMZO-HIBA / ERVENYTELEN` vagy `NULL`; TEXTBOOK/ANOMALIA tilos.
- **Karhossz-kapu:** transpile+ALAP után |hossz(arm) − cél| ≤ 1 dt, k = 0..32,
  minden (branch, init) csoportra és coupling_scale-re — a dryrun kötelező
  PASS-pontja.
- **Replay kapuk:** ≥ 600 null + ≥ 600 tankönyvi újraminta, FakeKingston-
  routolt Aer-valószínűségekből, 4096 lövés; hamis ANOMALIA ≤ 6/600, hamis
  TEXTBOOK ≤ 6/600 a null-oldalon; regressziós seedek ellenőrzése.
- A §6 Kockázatok listához: **új elem — a csúcs-nélküli bootstrap-minták
  kidobása hamis stignát adott (v1.2, 8/600); a v1.3 javítása ezen kapu
  (replay-kapuk) átengedtével érvényes.**

## Dokumentált korlátok (őszintén)

1. **A kitöltő `delay`-eken nem fut T1/T2 zaj ebben a verzióban** — a
   FakeKingston `target` sem hordoz delay-zajt. Az sx/x/cz kapuk NOISE-modellje
   valós (termál relaxáció a kapuidőre + depolarizáció), a kiolvasás hibás
   (szimmetrikus vetítés; az S qubit mérési hibája ≈ 8,4%). A karhossz-
   kiegyenlítés a szimulációban így **közvetlenül nem csökkenti** a
   zaj-kitettséget — hatása a hardver-egyenlőség megteremtése; a kapu az
   időzítést ellenőrzi. A delay-zaj a végső hardver-beküldés előtt (külön
   tulajdonosi döntésnél) pótolandó a T1/T2-adalékolással.
2. A **readout-vetítés szimmetrikus**; a target irányfüggő kiolvasási
   hibát nem ad.
3. A routed valószínűségek a **transzpilált gate-szekvenciából** származnak;
   a teljes 156-qubitos Density-Matrix szimuláció nem futtatható (memória) —
   a helyi 4-qubitos kivágás a layout (125/117/124/126) és az ALAP-időzítés
   megőrzésével készül.
4. Aer/szimuláció **nem** hardver-eredmény; az ítéletet a valós mérés dönti el
   (külön tulajdonosi döntésre).
5. Az `anomaly_reference` továbbra is **1.0 minden karon** (zajtalan unitér
   maximum) — fizikai zaj mellett az ANOMALIA konstrukció szerint alig érhető
   el; a replay-kapuk azt ellenőrzik, hogy a javított becslő sosem
   hallucinál csúcs hiányában.
6. A v1.2-höz képest a **szárazfutás viselkedése változott** (a zajtalan φ=0
   kontroll most `ELEMZO-HIBA / ERVENYTELEN`-t ad); ez a fail-closed szabály
   közvetlen következménye, nem regresszió.
7. A P1 (±20%) továbbra is pontbecslés-tűrés, nem CI-döntés.

## Repo-szabályok (változatlan)

- token sosem fájlban; minden push előtt titok-audit (grep); `data/` nem
  .gitignore-ban; a job ID-t a beküldés pillanatában mentjük;
- a döntési szabály a fagyasztott fájlból olvasandó; az elemző és a dryrun
  hash-e a fagyasztott fájlban van; eltérés esetén FAIL-CLOSED;
- fagyasztott fájlt nem írunk felül — új verzió, új hash, külön commit;
- az eredmény "előregisztrált teszt" vagy "felfedező adat"; a szimuláció
  sosem HARDWARE; a NULL-t NULL-ként jelentjük.

---

*Állapot: TERV — QPU-futtatás még nem történt. A v1.3 a Maya-féle NaN-hiba
(agent_feladat_csillag_v13.txt) javítása; készítésekor nincs mérési adat.
Ez a fájl a futtatás előtt készült; tartalma utólag nem módosítható;
módosítás csak verziószámozott kiegészítéssel, „amended" megjelöléssel.*
