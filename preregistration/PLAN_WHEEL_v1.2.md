# PLAN_WHEEL v1.2 — AMENDED (felülírja a v1.1-et; a v1.0 és a v1.1 byte-ra változatlan)

**EZ A FÁJL AMENDMENT.** A `preregistration/PLAN_WHEEL_v1.0.md`,
a `preregistration/PLAN_WHEEL_v1.1.md`, a `preregistration/frozen_wheel_params.json`
(v1.1) és a hozzá tartozó `.sha256` — a v1.1 `.sha256`-ben rögzített hashekkel
(`8920be6b…` PLAN_WHEEL_v1.0.md, `533b3a7b…` PLAN_WHEEL_v1.1.md,
`52f84bc6…` frozen_wheel_params.json) — **byte-ra változatlanul megmaradnak
a történet részeként** —
csendben átírni TILOS. A v1.2 a v1.1-et FELÜLÍRJA (superseded) az alábbi
pontokban; minden más (a kísérletterv felépítése, a kaputilus-tábla, az
Aer/zajtalan 0. fázis, a routing-fagyasztás `routed_transpiled`, a claim
claim-család név szerint: W1, W2, W4_secondary, sotetallapot, 99% CI +
Holm) a v1.1-ből ÖRÖKLŐDIK.
**Dátum:** 2026-11-12 · **Előzmény:** Maya beküldés előtti átnézése
(2026-11-12 09:05 UTC) + Maya javítása (2026-11-12 20:01 UTC) · **Repo:**
triangle-anchor-memory, `arena/71dcbdba-triangle-anchor-memory` ág ·
**Státusz:** terv + amendment — **QPU MÉG NEM FUTHAT; beküldés TILOS**
(lásd a W3-kapu fejezetet és a 4. pontot).

## Miért készült (Maya megállapításai, 2026-11-12 09:05 UTC — rögzítve)

1. **A W2 a nulla ellen mért, de tankönyvi fizikán is 66%-ban szignifikáns**
   (a fagyasztott Aer-igazsággal 199/300), mert a `wheel` és a `wheel_rev`
   áramkörök között **kapusorrendi tankönyvi különbség** van — a kapusorrend
   a routolt áramkörökben NEM azonos a két irányban, így az Aer-modell eleve
   nem-nulla iránykülönbséget jelez (−0.0114). A nulla mint referencia ezért
   ALKALMATLAN: a "szignifikáns" kimenetel nem hordoz információt.
2. **Az ítélet a kódban és a docstringben nem volt összhangban** (a korábbi
   `src/wheel/analysis.py` 172–195. sora abszolút `AUC(wheel)`-t vetett
   össze a lefagyasztott Aer-AUC-val, miközben a docstring (26. sor) "wheel
   vs static kontraszt"-ot írt). Kalibráció-eltérésnél az abszolút összevetés
   NULL-ba csúszik, pedig a **kontraszt** (közös skálaeltolódások
   kiejtődnek) összhangban marad az Aer-jóslattal.
3. **Maya tankönyvi jóslata a szimulációban máris teljesül** (SZIMULÁCIÓ,
   NEM mérés): W1 a `ring_only` ellen **NULL** (0.471 vs 0.730); a
   sötétállapot-teszt **nem válik el** (`dark_m1` = 0.4706 < `dark_m0` =
   0.4917; `dark_mm1` = 0.4820 < `dark_m0`). Ez tényként rögzítve kerül a
   terv várakozásai közé (l. `frozen_wheel_params_v1.2.json` expectations) —
   **a mérés (ha lesz) ettől függetlenül dönt**.

## Mi változott és miért (v1.1 → v1.2)

1. **A W2, W4 és a sötétállapot-teszt nullhipotézise az Aer-jósolt
   különbség, NEM a nulla** (a lefagyasztott görbék különbségei,
   pontosan):
   - **W2:** `AUC(wheel) − AUC(wheel_rev)` nullhipotézise =
     **−0.011366102431** (Aer: 0.470649 − 0.482015; a tervben: **−0.0114**);
   - **W4_secondary:** `AUC(pump_dir) − AUC(wheel)` nullhipotézise =
     **+0.009738498264** (Aer: 0.480387 − 0.470649; a tervben: **+0.0098**);
   - **Sötétállapot:** `d1 = AUC(dark_m1) − AUC(dark_m0)` nullhipotézise =
     **−0.021023220486** (Aer: 0.470649 − 0.491672; a tervben: **−0.0210**);
     `d2 = AUC(dark_mm1) − AUC(dark_m0)` nullhipotézise =
     **−0.009657118056** (Aer: 0.482015 − 0.491672; a tervben: **−0.0097**).
   - **W1 változatlan** (nulla a nullhipotézis, 1.25-ös előny-küszöb) — a
     W1 az "előny a kontrollokkal szemben" kérdés, nem modell-ellenőrzés.
   - A riportban **külön sor**, a Holm-korrekcióstól függetlenül:
     `tankonyvi varakozas: teljesul / nem teljesul` — „teljesül”, ha az
     adott kontraszt 99% CI-je tartalmazza az Aer-jósolt értéket; különben
     „nem teljesül” (W2-re és W4-re külön; sötétállapotnál d1 és d2 külön,
     claim-szinten a kettő **AND**-je). A kimenetel a riportban név szerint,
     egymás mellett szerepel a Holm-döntéssel.
   - A claim-család p-értékei (bootstrap): W2 és W4 két oldalú p az
     Aer-nullhoz; sötétállapotnál d1/d2 két oldalú p, claim-p =
     max(p1, p2) (Bonferroni a claim-en belül). Holm a családban
     (ci_level = 0.99, correction = holm) változatlan.
2. **Ítéletlogika — kontraszt-alapú (kód és docstring összhangban):**
   - `d_static = AUC(wheel) − AUC(static)`, `d_ring = AUC(wheel) − AUC(ring_only)`;
     az **Aer-jósolt kontrasztokhoz** mérve (`d_static,Aer = −0.0050`;
     `d_ring,Aer = −0.2598`; a lefagyasztott görbék különbségei).
   - **TEXTBOOK:** mindkét |d_obs − d_Aer| a hibrid 99% CI-sávon belül
     (sáv = 3.2905·sqrt(σ²_Aer,kontraszt + σ²_obs,kontraszt);
     σ²_Aer,kontraszt = σ²_arm1 + σ²_arm2 — a lefagyasztott Aer-std-k
     kovarianciája nincs rögzítve → függetlenséget feltételezünk).
   - **ANOMALIA:** bármelyik d_obs > d_Aer + sáv (az Aer ALÁBECSÜLI a
     megtartást) — ELŐSZÖR kalibrációs/modellhibát kell keresni (T1/T2
     drift, readout, csatolás-kalibráció); claim az anomália feloldása
     előtt NEM kerül kikiáltásra.
   - **NULL:** különben (beleértve az Aer-sáv ALATTi eltérést és a nem
     teljesülő W1-et) — NULL-t NULL-ként közöljük.
   - **A beküldés napi kalibrációjából újraszámolt Aer-jóslat az
     alkalmazandó referencia** — a `frozen aer_prediction` a preregisztrált
     alap; ha a beküldéskori kalibráció eltér (pl. T1/T2 drift), az
     Aer-jóslatot a beküldés részeként ÚJRA KELL SZÁMOLNI, és az ÍTÉLET
     összevetése az újraszámolt referenciához történik. A v1.1-féle abszolút
     összevetés (amely kalibráció-eltérésnél NULL-ba csúszik) megszűnt.
3. **Az elemző és a dryrun sha256-ja a frozen JSON-ba kerül** (`file_hashes`:
   `preregistration/PLAN_WHEEL_v1.2.md`, `src/wheel/analysis.py`,
   `dryrun_wheel.py`), és a fagyasztott elemző futás közben
   ELLENŐRZI őket — eltérés/hiány esetén MEGTAGADJA a futtatást
   (a v1.2 fagyasztott integritás részeként).
4. **A W3-kapu MARAD.** A Kerék QPU-job CSAK akkor tervezhető, ha
   **(a) a Küszöb-ítélet ROGZUL** — ez **2026-11-12-én teljesült** (job
   `dbr1fl6jjaos73ai51pg`, DONE 19:51 UTC; a rekord:
   `submission/kuszob/results/`; kötelező jelölés: „gep-alkalmassagi kapu,
   tankonyvi varakozas”) — **ÉS (b) egy ÚJ, a beküldés napi kalibrációjával
   elvégzett W3-számítás nem SZÉTESŐ**. A 2026-11-11-i snapshoton a W3
   verdiktje **SZÉTESŐ** (1.05 várt 2Q-hiba > 0.5; a tárolási és a
   flux-lock feltételek teljesülnek) — az amendment ezt NEM számolja újra
   (ugyanaz a bemenet → ugyanaz az eredmény), és nem is teheti: **a friss
   W3 új (beküldéskori) snapshot/kalibráció nélkül nem adható ki**.
   **(b) ezért JELENLEG NEM TELJESÜL, és a Kerék QPU-job NEM tervezhető.**
   **Beküldő szkript NEM készül** — csak akkor, ha mindkét feltétel
   teljesül, és külön tulajdonosi döntés + audit után; a követelmények
   (submission-day kalibrációból újraszámolt Aer-referencia; a beküldés
   útján kötelező kapu a payload mérés-bekötésénél (a küszöb-menet v1.3 G8
   mérés-kapujának megfelelően); record-first; env-név token) a Gyűrű v1.2
   amendment 2. és 4. pontjával összhangban — a Gyűrű v1.2 dokumentum nem
   része ennek a repónak; az ott hivatkozott követelményeket szándék
   szerint követjük: beküldő csak a kapuk nyitása után, env-nevű tokennel,
   record-first folyamattal készülhet.
5. **A várakozások közé tényként bekerülnek a szimulációs eredmények**
   (SZIMULÁCIÓ, NEM mérés): W1 a ring_only ellen NULL (0.471 vs 0.730);
   a sötétállapot nem válik el (`dark_m1` < `dark_m0`); a W2 nulla-elleni
   szignifikancia tankönyvi (199/300). **A tulajdonos és Maya várakozásai
   változatlanul egymás mellett állnak** — a mérés dönt (ha lesz).

## Amit a v1.2 NEM változtat

- A claim-család név szerint: `W1, W2, W4_secondary, sotetallapot`;
  `ci_level = 0.99`; `correction = holm`; Holm a családon.
- A routing: `routed_transpiled` (opt=0, seed_transpiler=1234,
  initial_layout [125,117,124,126] → transzpilált elrendezés; a gyűrű-élek
  S 125-ön keresztül routolódnak); a kaputilus-tábla (minden kar 700 CZ);
  a 0. fázis (zajtalan + Aer); a pozitív/negatív kontroll; a sötétállapot
  27 áramköre; a `bootstrap_seed = 20261111`; a `bootstrap_n = 2000`.
- A v1.0/v1.1 tervek és a v1.1 `frozen_wheel_params.json` + `.sha256`
  **byte-ra változatlanok**; a v1.2 az `frozen_wheel_params_v1.2.json`-nal
  lép érvénybe (saját `.sha256`-jével).
- **NULL-t NULL-ként jelentjük.** A szimuláció soha nem „HARDWARE”. A
  token kizárólag `IBM_QUANTUM_TOKEN` env-névként szerepelhet; token SEHOL
  máshol. A `data/` nincs gitignore-olva. A döntési szabály csak verziózott
  amendmenttel módosítható.

## A kimondott tilalmak (a v1.2 idején)

1. **QPU-beküldés TILOS — kétszeresen.** (i) A Kerék saját W3-kapuja
   SZÉTESŐ (a 2026-11-11-i snapshoton; (b) friss W3 nem történt és nem
   történhet a beküldés napi kalibrációja nélkül); (ii) a Kerék QPU-jobhoz
   külön tulajdonosi döntés és formális audit kell — egyik sem történt meg.
   **A Küszöb-ítélet ROGZUL-léte NEM jogosít fel semmilyen Kerék-beküldésre.**
2. Az agent tokent nem kap, nem kér és nem kezel; a QPU indítása minden
   esetben a tulajdonos/Control Agent feladata.
3. A fagyasztott fájlokhoz (v1.0/v1.1 és minden korábbi rekord) hozzányúlni
   TILOS; `data/` nem kerülhet ki a repóból; a hash-láncot minden commit
   előtt ellenőrizzük (titok-grep).

## Dryrun és ellenőrzés

A `dryrun_wheel.py` a fagyasztott v1.2 integritását ellenőrzi, majd Aer
(routingolt) "mérést" végez 512 shot/áramkörrel (seed 20261111), futtatja
az elemzőt, a pozitív/negatív kontrollt és a W3-kaput; a jelentést a
`data/wheel_dryrun_report_v1_2.json`-ba írja (a v1.1 jelentés
megőrződik). A dryrun szimuláció — **NEM hardware-eredmény.**

## Szabályok és tilalmak (örökölt, változatlan)

No QPU az agenttől; titok-grep commit előtt; `data/` nincs gitignorálva;
a szimuláció soha „HARDWARE” címkével; NULL is record-first; a döntési
szabály változása csak verziózott „amended” verzióban; no post-hoc
paraméter-halászat; minden commit után hash jelentendő; a beküldés a
tulajdonos/Control Agent feladata — a Küszöb-eredmény (ROGZUL) sem jogosít
fel Kerék-beküldésre.
