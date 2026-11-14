# PLAN_RING v1.2 — AMENDED (felülírja a v1.0-t és v1.1-et)

**EZ A FÁJL AMENDMENT.** A `PLAN_RING_v1.0.md` és `PLAN_RING_v1.1.md` byte-ra változatlanul megmarad
a történet részeként — csendben átírni TILOS. A v1.2 a v1.0-t és v1.1-et FELÜLÍRJA
(superseded): minden döntési küszöb 99% CI + Holm, a csapat szabálya szerint.

**Mi változott és miért (v1.1 → v1.2, Maya auditja alapján):**
1. **Beküldés-napi kalibrációból újraszámolt jóslat (±20% T1/T2 sávval):** A v1.1-ben az ítélet
   kalibrációfüggő volt: FakeKingston-igazsággal NULL 300/300 (a lefagyasztott snapshot zaja döntött,
   nem a fizika). A hardveres futtatás döntési küszöbeit ezért a futtatás napján mért chip-kalibrációból
   kell újraszámolni ±20% T1/T2 bizonytalansági sávval.
2. **QPU k-tartomány korlátozása k ≤ 16-ra:** A k=32 pont routolt költsége 341 CZ (0.565 2Q hibaösszeg),
   ami a W3 szétesési határon túl van. A valódi QPU-futáshoz a rács k ≤ 16 (max 176 CZ @ k=16).
3. **R1-döntés és illesztett kontroll:** Az R1 a csillag-kar dupla kapuszáma miatt tankönyvileg is
   szignifikáns lenne. Az R1 ezért önmagában nem memória-bizonyíték, csak kapuszámban illesztett kontrollal
   együtt értelmezhető.
4. **run_ring.py beküldés-ellenőrző bevezetése:** Szigorú fail-closed ellenőrző szkript (--check-only
   módban: frozen v1.2 integritás, ibm_kingston backend, layout [125, 117, 124, 126], k ≤ 16 kapu,
   mérés-kapu). QPU beküldés kizárólag tulajdonosi döntéssel indulhat.

**Előzmények (v1.0 → v1.1):**
1. Claim-küszöbök: 95% → 99% CI + Holm;
2. ANOMALIA-kapu: determinisztikus kétoldali 99% (z = 2.5758);
3. Deviant kontroll: dryrun hamis ANOMALIA ≤ 1% (≤ 3/300).

A továbbiakban az érvényes szabályokkal karbantartott szöveg következik. Aer/szimulációs eredmény SOHA nem kap
„HARDWARE" címkét. NULL-t NULL-ként jelentünk.

---

**Állapot: terv + 0. fázis (szimuláció) — QPU még nem futott.**
**Dátum:** 2026-11-14 (Máté Róbert, tulajdonos; v1.2 Maya audit szerint)
**Repo:** triangle-anchor-memory — gyűrű-menet v1.2 amendment

## 1. A kiinduló kép és a lefordítása

**Tulajdonos eredeti ötlete:** három sarokpont, amelyek a középpont mellett
EGYMÁSHOZ is kapcsolódnak („gumikkal") — a gerjesztés körbe tud keringeni,
és a keringés iránya maga a tárolt bit. A repó jelenlegi állapota ezt csak
csillagként realizálja; ez a terv a VALÓDI háromszög.

**Kvantitatív fordítás:**
- Három qubit gyűrűben: páronkénti XY-csatolás mindhárom él mentén
  (R1–R2, R2–R3, R3–R1), Peierls-fázistolással (φ_f = π/6 / él; teljes fluxus
  Φ = π/2). Egyetlen gerjesztés alterében a sajátállapotok keringő hullámok:
  **|k₊⟩ ∝ |100⟩ + e^{+i2π/3}|010⟩ + e^{+i4π/3}|001⟩** (óramutató irány),
  **|k₋⟩ ∝ |100⟩ + e^{−i2π/3}|010⟩ + e^{−i4π/3}|001⟩** (ellenirány) —
  ez a két keringési irány a két megkülönböztethető állapot: a **forgásirány-bit**.
- A mérési kérdés: elkészített irányú keringő állapot meddig marad
  irány szerint kiolvasható a veszteségek (T1, T2, kapu- és kiolvasási
  hibák) mellett.
- **Az irány-információ fázisérzékeny.** Mindhárom keringési sajátállapotnak
  azonos a populációja (1/3, 1/3, 1/3) — a populációs mérés önmagában
  SEMMIT nem mond a keringés irányáról. Körültekintés (kötelező): a
  döntési metrikát a plan szerint fázisérzékeny kiolvasásra építjük (lásd 3. §).

## 2. Az előre rögzített állítások (cáfolati feltételekkel)

 claim-család: **R1, R2, PUMP (másodlagos), NC-kontroll** — az elemző saját
 99%-os CI-vel dolgozik, a csapat szabályával egyezően (minden kísérletre
 99% CI + Holm; a v1.0-ás eltérés megszüntetve — v1.1, 2026-11-12).

- **R1 (fő):** a gyűrű irány-bitje TOVÁBB kiolvasható, mint az azonos
  össz-csatolású csillag visszaáramlási jele és az önmagára hagyott qubit —
  kritérium: τ_irány(ring) > τ_vissza(csillag, azonos össz-kapuráfordítás) ÉS
  τ_irány(ring) > τ_tárol(magányos qubit), mindkettő egyoldalú 99% CI-vel.
- **R2 (fő):** a nulla-fluxus referencia (static, φ_f = 0) NEM teljesíti a
  keringést — irány-kontrasztjának el kell maradnia a fluxusos gyűrűétől;
  kritérium: feszes 99% CI-vel gyengébb irány-hűség u.a. kapukosztással.
- **PUMP (másodlagos, NEM memória-claim):** a parametrikusan modulált élű
  gyűrű-kar (g(t) = g0(1 + m·cos(2Ωt + φ_p))) τ_irány-ja m függvényében
  változik; előre rögzített (m, φ_p) párok: (0,0), (0.1,0), (0.2,0), (0.3,0),
  (0.1,π/2), (0.2,π/2), (0.3,π/2) — Ω a zajtalan szimulációból. Cáfolati
  feltétel: **ha EGYETLEN (m, φ_p) pár sem ad a pumpa nélküli gyűrűnél hosszabb
  τ_irány-t 99% CI-vel, a pumpa-ötlet erre a rendszerre megbukott** —
  további paraméter-kombinációt ezután keresni TILOS (paraméter-halászat);
  a kipróbált párok a frozen_ring_params.json "pump" blokkjába kerülnek.
- **NC-kontroll (kikapcsolt élek — a feladat "pozitív kontrollja"):** a
  gyűrű-élek KI kapcsolva (identitás-kitöltők, azonos kaputilus) — az
  elemzőnek az irány-élettartam ELŐNYÉRE NULL-t kell jelentenie. Ha nem NULL,
  az elemző hibás (nem a fizika).

## 3. Mérési protokoll

**Elkészítés (mindkét irány, azonos kapuszerkezet):** a Kerék/Küszöb
Givens-sablonjával — X(R1) + XY(R1,R2; t1,p1) + XY(R2,R3; t2,p2), ahol
(t1,p1,t2,p2) a |k₊⟩ (illetve |k₋⟩) sajátvektora a dekompozíció szerint;
|k₀⟩ = (1,1,1)/√3 is elkészül (kontroll). Kaputilus-egyeztetés minden
karban kötelező (aktív XY = 2 CX; identitás-kitöltő slot = CX·CX = 2 CX).

**Kiolvasás — indoklom a választást:** az **előkészítés inverzével egy
báziskimenetre képezzük** (Loschmidt-típusú visszalépés): fixen a **+ irány
unpreparálja** (`prep_+†`) a betárolt iránytól FÜGGETLENÜL, majd a HÁROM
gyűrű-qubitet Z-ben mérjük. Az echo a **vákuumba (|000⟩)** ad vissza —
NEM a |100⟩-ba (mert prep₊|000⟩ = |k₊⟩, tehát prep₊†|k₊⟩ = |000⟩).
Indoklás: (i) az ideális sajátállapot fejlődése után az amplitúdó a
bemeneti állapotra mutat vissza: P₀₀₀(ideal, bármely k) = 1 a + ágban;
(ii) a |k₋⟩ praparáltonak ugyanaz az áramkör a ZÉRÓvákuum-amplitúdót adja
(a két sajátvektor ortogonális: ⟨k₊|k₋⟩ = 0), tehát a jel teljesen elválik;
(iii) EGYETLEN, direction-switching nélküli protokoll — a mérés előtt
nincs választás (az megszegné a vak elemzést); (iv) az X-bázisú
tomográfia több áramkört kívánna ugyanezért az információért.
A mért mennyiségek (kari definíció):
- **F₊(k) = P(000; m+ ág)** — a + irány echo-visszatérítése;
- **F₋(k) = 1 − P(000; m− ág)** — a − irány echo-visszatérítése (komplementer);
- **C(k) = P(000; m+) − P(000; m−)** — a keringési irány kontrasztja
  (ideal 1; vakon 0; SPAM-robust differenciál, azonos mérési lázzal).
Megjegyzés (a 0. fázis javítása, 2026-11-11): a korábbi (P(R1=1) alapú)
kiolvasás a vákuum-infláció miatt vak mintázatot adott — ezt a szimuláció
eelleplezte; a terv mostantól a fenti metrikával él (v1.0, frozen-előtti
javítás, a v1.0-t NEM növeli, mert nem fagyott le még).

**Tárolási lépés és grid:** minden tárolási kör = 3 XY-él (ORDERS-rotáció,
φ_f = π/6/él); k ellenpontok: {0, 4, 8, …, 32} (9 pont, a csillag-menettel
azonos rács). **Nincs 5 µs kitartás** — a gyűrű-bit mérése közvetlenül a
kaputávon zajlik; a tárolás-index a kör. (5 µs kitartás a csillag-
kontroll armra értendő kontrollként — ugyanaz az időkeret, mint a
csillag-menetnél.)

**Kontrollok (mind a csillag-menet layoutjain, azonos össz-kapuráfordítással):**
- **(a) — csillag visszaáramlási jel, azonos össz-csatolás:** a gyűrű-él-
  kapuk helyett identitás-kitöltők + aktív küllők (a csillag-kar mintája):
  S=|1⟩ → a horgonyokon visszaáramlás; a jel: a horgonyok együttes
  visszaáramlási kontrasztja; mérés: a csillag-menet elemzőjének megfelelő
  U(t) inverz-leképezéssel bázisra. τ_vissza = a visszaáramlási kontraszt
  0.75-ös keresztezése (k-ban, lineáris interpolációval).
- **(b) — magányos qubit állapotbitje:** egyetlen qubit |1⟩-gyel, ugyanannyi
  lépésben; metrikamegdőlése: T1-vonatkozó retenció, τ_tárol a 0.75-ös
  keresztezés. (A q1 96. vonalon, a csillag-menet T1-kalibrációjával.)
- **(c) — horgony nélküli, csak késleltetett qubit:** ugyanaz, mint (b), de
  a lépés végén identitás-kitöltő kétqubitik kapuk UGYANABBAN a számban,
  mint a gyűrű-karban — elkülöníti a puszta kapu-/identitás-költséget a
  csatolás hatásától. (A két leírás értelmezése: (b) a tisztán T1/T2-korlát,
  (c) a tisztán kapukosztás-korlát — nincs közük a horgonyokhoz.)
- **NC (kikapcsolt élek / törött gyűrű):** minden gyűrű-él identitás; a
  prep ugyanaz; a jel: irány-kontraszt ≈ 0 minden k-ra — az elemző NULL-t
  ad az előnyre. (A feladat "pozitív kontroll"-ja ezen a néven szerepel itt;
  a kerék-terminológiában ez negatív kontroll.)

## 4. Kiegészítés — parametrikus pumpa-kar (másodlagos)

A tulajdonos hintaképe (Maya megfogalmazásában): a hintázó gyerek sem tudja,
merre leng, mégis hajtja magát a lenges kétszeres ütemében végzett
paraméter-változtatással — a gyűrűben is lehetne a csatolásokat ritmikusan
modulálni a keringés kétszeres ütemében, kiolvasás és irányismeret nélkül.
A lökés azt erősíti, ami már ott van — ezért „vak lökés", szemben az aktív
korrekcióval.

**Specifikáció:** g(t) = g0 · (1 + m · cos(2Ωt + φ_p)), Ω a keringési
frekvencia (a zajtalan szimulációból, a kör-áramkör spektrális bontásából
meghatározva és a frozen_ring_params_v1.2.json-ben befagyasztva). A pumpa MINDEN
gyűrű-élre egyformán hat; m ∈ {0, 0.1, 0.2, 0.3}, φ_p ∈ {0, π/2}.
**A kar másodlagos:** a fő állítás (R1/R2) a pumpa nélkül is eldönthető;
a pumpa külön kérdés, a fő claims-be nem számít bele.
**Cáfolati feltétel (lásd 2. § PUMP):** nincs (m, φ_p) pár, ami 99% CI-vel
verje a pumpa nélküli gyűrűt ⇒ a pumpa-ötlet megbukott; paraméter-halászat
tilos; a kipróbált párok a frozen fájl "pump" blokkjában.

**A pumpa számított költsége (őszinte korlátok, kötelezően beleírva):**
- A parametrikus pumpa a veszteséget kompenzálja, nem szünteti meg;
- minden lökés saját hibát hoz be: a modellben a pumpálás él-kapu-szöget
  módosít (nincs extra 2Q kapu), DE a lökés-frekvenciájú fluxus-moduláció
  1Q-"kick"-ként kezelve a vak-lökés-költség k×3 impulzus, egyenként
  ~2e-4 hibával (a kerék pumpa-blokkjával azonos mobil); a szimuláció
  mindkét számvitelt kiszámolja és a szigorúbbat jelenti;
- a pumpa a hangzatos hintaképből nem következik — a qubit kétallapotú,
  nem harmonikus oszcillátor; a hatás kizárólag a szimulációból olvasandó ki;
- a 2. fázisos DD pi-impulzusokkal való rokonság csak RÉSZLEGES: a DD
  mágneses fázis-visszafordító vak lökés a défázis ellen, a pumpa viszont
  energiát is visz be — a kettő NEM mosható össze;
- ha a pumpa nyertese kisebb a saját hibájának áránál, az az eredmény —
  így kell kiírni.

## 5. Mérőszámok és döntési szabály (előre rögzítve)

- **F(k)** irányhűség ágonként; **C(k)** irány-kontraszt (fő görbe);
- **τ_irány:** az első k, ahol C(k) < 0.75, lineáris interpolációval
  (1 → 0.5 a teljes elvesztés — 0.75 a felezőpont-fölötti praktikus korlát);
- **τ_pump/τ_0:** a pumpa szorzófaktora m függvényében (csak riport a fő
  claims-hez; a döntés a PUMP-ágban külön);
- Bootstrap: 2000 multinomiális minta (a shot-szintű adatból), seed 20261111;
  **ci_level = 0.99**, correction = "holm" a claim-családon belül
  ([R1, R2, pump, nc]); egyoldalú ahol a feltétel egyirányú.
- **Ítélerek:** TEXTBOOK (a mért retenció az Aer-jóslat 99% CI-sávján belül) /
  ANOMALIA (fölötte — először modell-kalibrációt keresünk, és csak utána
  értelmezés) / NULL (nincs mérhető előny).
- **Az Aer-ablak modellfüggő** — ANOMALIA esetén a modell az első
  gyanúsított, a terv szerint.

## 6. 0. fázis — mit kell lezárnia a fagyasztás előtt

1. Zajtalan szimuláció: irányhűség-görbék, C(k), τ_irány, Ω (a pumpa
   frekvenciája) meghatározása;
2. Zajos (Aer, a csillag snapshot.json T1/T2/ε-jával, 4096 shot): ugyanazok
   a görbék; a kontrollokkal összevetve;
3. Pump-scan: m ∈ {0, 0.1, 0.2, 0.3} × φ_p ∈ {0, π/2} a zajos modellben;
   a nyereség/költség számvetése; a (m, φ_p) párok kipróbálva és FAGYASZTVA;
4. Kaputilus-egyeztetés kimutatva (tábla) + routolt kapuszám-becslés a
   TÉNYLEGES nehéz-hex rácson (a gyűrű-élek NEM natívak — a routing-seb a
   kerék-menetben kimérve; a gyűrűre is jelentjük a számokat);
5. A döntési küszöbök befagyasztva: frozen_ring_params.json (az Aer-várt
   görbék, τ-k, kontrollok, a pumpa-blokk, a döntési szabály változatai),
   SHA-256-nal; a csillag frozen_params.json elrendezését követve;
6. Pozitív kontroll ellenőrzés: a kikapcsolt-élkar az elemzőben NULL-t ad.

## 7. Kockázatok és ismert csapdák (előre kimondva)

- **Fázistolás pontossága:** a φ_f = π/6 és a θ kör-lépések hibaszintje
  közvetlenül a sajátvektorokra hat; a prep-kalibráció (φ-körkapcsolás)
  kötelező kalibrációs kar (a csillag φ_eff mintájára);
- **Élcsatolási eltérések:** a három gyűrű-él nem azonos erősségű a valóságban;
  az Aer a snapshot eps_2q-összegeivel számol — a valódi szórás ismeretlen;
  az elemzésnek a kaputilus-táblát és a φ_eff-t minden futáskor ellenőrznie kell;
- **Keringés vs visszaáramlás összekeverhetősége:** a ring és a csillag-kar
  is mutat "revival"-t — a szétválasztás az IRÁNY (chirális) fázis-kontrasztja;
  populációs mérés mindkettőt azonosan látná → a fázisérzékeny kiolvasás nem
  opcionális;
- **A gyűrű ezen a rácson nem natív:** a nehéz-hex rácsban a (R3,R1) él
  tipikusan SWAP-lánccal routolódik; a routing-költség (a kerék-menetben
  700 CZ-re adódott) RONTJA a megtérülést — a 0. fázis ezt számszerűsíti és
  a fagyasztott fájlba beírja;
- **Várható kimenet:** a szimulációt a Maya-oldal (a forgás a keringést
  nem tartja jobban, mint a sima visszaáramlást — vagy csak marginálisan)
  HD-osan támogatja; a mérés — ha lesz — a mérés dolga. (A tulajdonos
  erős várása a kerék-menetben is a mérhető előny volt.)

## 11. 0. fázis — a számszerű eredmények (Aer/Statevector — NEM hardware)

**Ω (a pumpa frekvenciája), a kör-spektrumából:** a Peierls-élek egy körének
eigenfázisai {−0.390, +0.126, +0.265} rad/kör; a k₊-ág 0.126, a k₋-ág 0.265 —
**Ω = |0.265 − 0.126| = 0.1387 rad/kör** (2Ω = 0.2774 rad/kör). A pumpa
(2Ωt ütem) fagyasztva: `omega_rad_per_round = 0.13868668363497552`.

**Routing-költség (TÉNYLEGES heavy-hex, opt=0, seed 1234):** a k körös
gyűrű-kar (prep + k kör + prep† — a gate-számok a küszöb-jobéval azonosak,
a mérés 3-bites): k=0 → 11 CZ (0.017 várható 2Q-hiba), k=4 → 50 CZ (0.081),
k=8 → 92 CZ (0.126), k=16 → 176 CZ (0.291), **k=32 → 341 CZ (0.565)**.
⇒ A **teljes K=32 grid routolt költsége a 0.5-ös W3-küszöb FÖLÖTT van** —
ezen a négyesen a teljes gyűrű-job sem tervezhető koherensen; k ≤ 16
(0.291) a „beküldhető" tartomány; a döntés a TULAJDONOSé (nem a 0. fázisé);
hát ezt a tényt a fagyasztott fájl és ez a fejezet is könyveli — a gridöt
nem szűkítjük csendben (az paraméter-halászat lenne).

**Zajtalan referencia (exact):** ring_p 1.0→0.77 (stroboszkopikus oszcillációk,
monoton nem-jegyzett); static/lone/delayed = 1.0 minden k-ra (sajátállapotok —
a fluxus NEM látszik az echo-metrikában eseténük; ez a metrika összetevője);
broken oszcillál → 0.18 @32; star oszcillál → 0.02 @32; C(k): 1.0→0.67 @32.

**Native Aer (2048 shot, seed 20261111, A1/A2/A3, párhibák = eps_2q-összeg):**
ring_p 0.97→0.75; C(k): 0.97→0.65; static ≈ 0.97 (lapos); star 0.95→0.16;
broken 0.97→0.17; lone/delayed = 1.0; **τ(kör): ring_p ≈ 17, contrast ≈ 14,
broken ≈ 2.9, star ≈ 0.95** — a keringési bit TÚLÉLI az egységnyi gate-idejű
modellet; a fluxus-mentes referencia (static) PONTOSAN a szimuláció miatt
lapos (lásd 7. fejezet: az echo a fluxust nem látja — a keringési előny
helye itt a kontraszt-garancia és a valós T2-keret).

**Routed Aer (a ahogy-a-chipen-futna szám):** ring_p 0.90→0.32; C(k): 0.90→0.21;
static 0.90→0.40; star 0.95→0.34; broken 0.90→0.12; **τ(kör): ring_p ≈ 3.1,
contrast ≈ 2.7, static ≈ 6.8, broken ≈ 1.8** — a routing-seb miatt a
keringési előny gyakorlatilag elhal; a Maya-oldal (várt: nincs mérhető
keringéselőny) ezen a routingon ASSZISZTÁLT.

**Pump-scan (native, Aer-előrejelzés, seed 20261111):** egyik (m, φ_p) pár
sem ver pumpa nélküli gyűrűt 99% CI-vel — a nyereség ≈ nulla (minden m
intra-shot-zaj ±0.01 tartományban, lásd data/ring_freeze_data.json);
routed-ban a π/2-fázisú pumpa kicsit rosszabb (−0.01..−0.02). Az exact
unitary kis stroboszkopikus különbséget mutat (m=0.3, φ_p=0, +0.04 @k=32),
de ez a hardver-ígérethez elégtelen. Kijelentve, a cáfolati feltétel szerint:
**ha a hardver ugyanezt hozza (nincs nyertes pár 99% CI-vel), a pumpa-ötlet
erre a rendszerre megbukott; további paraméter-keresés TILOS.**
Kipróbált és fagyasztott párok: (0,0), (0.1,0), (0.2,0), (0.3,0), (0.1,π/2),
(0.2,π/2), (0.3,π/2) — a frozen_ring_params_v1.2.json "pump" blokkjában.
A lökés-költség számvetve: 96 impulzus (K=32) × 2e-4 ≈ 0.019 additív hiba —
bőven a nyereség-nulla alá; a saját ára ezt rendben hozza.

**Aer-jóslat (a döntéshez befagyasztva):** native: C(32)=0.65, τ≈14;
routed: C(32)=0.21, τ≈2.7 — ha valaha lesz mérés, a verdikt a routed-számok
szerint dönt; a static-easter-egg (echo-fluxus-vakság) minden interpretation
ELŐTT modell-auditra kötelez.
