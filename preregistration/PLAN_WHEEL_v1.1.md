# A Kerék — forgó gyűrű által tartott középpont — kísérletterv (v1.1, amended)

**„AMENDED" — a v1.0-at NEM módosítja; a fagyasztás (frozen_wheel_params.json)
ezre a verzióra épül. A v1.0 soha nem fagyott le.**
**Állapot:** terv + 0. fázis (szimuláció) — **QPU még nem futott**
**Dátum:** 2026-11-11 (Máté Róbert, tulajdonos; terv szerzője: Control Agent;
az ötlet és az eredeti élmény Máté Róberté)
**Repo:** triangle-anchor-memory — külön menet a csillag- és a gyűrű-menet mellé

v1.1 — a v1.0 fagyasztása ELŐTT (Maya átnézése, 2026-11-11) készült javítások:
1. **ROUTING-TUDATOS TERV** (kritikus) — a heavy-hex rácsban nincs háromszög;
   a gyűrű-éleket SWAP-hálózattal kell végigvinni a tényeleges layouton;
   a W3 a valós kapuszámokkal és kapuhibákkal számol; a széteső tartomány
   előre kimondva; a „virtuális gyűrű" vs routolt összevetés számszerűen.
2. **TEXTBOOK-ALAPVONAL** (kritikus) — az ítélet kétrétegű; az Aer zajos
   szimulációja a TÉNYEGESEN transzpilált áramkörökkel kötelező; a három
   ítélet (TEXTBOOK / ANOMALIA / NULL) előre rögzítve.
3. **HIÁNYZÓ KONTROLLOK** (kritikus) — `alone_DD` (DD-kontroll) és mind
   **karonként kötelező** a kaputilus-egyeztetés (azonos 2Q-darabszám minden karban,
   akár aktív, akár identitás-kitöltő) — kaputilus-táblával.
4. **POZITÍV KONTROLL** (kisebb) — ismert erősségű beépített stabilizáló
   hatás; az elemzőnek ki kell mutatnia, vagy az elemző hibás.
5. **W4 OSZTÁLYOZÁS** (kisebb) — az iránykövető lökés másodlagos, nem memória-
   teszt; a fő W1/W2 állításba nem számít bele.
6. **Maya tankönyvi jellemzése** (várakozás) — szószerint a tervbe; a
   tulajdonos joslata mellette; a mérés dönt.
+ kiegészítés (2026-11-11):
7. **EGYSÉGES, SZIGORÚ KÜSZÖB** — 99% CI + Holm családi korrekció; a
   fagyasztott fájl `ci_level = 0.99`, `correction = "holm"`; az állítás-
   család név szerint: W1, W2, W4-másodlagos, sötétállapot-teszt.
8. **W3-BUKÁS FORGATÓKÖNYV** (előre eldöntve) — ha a W3 széteső: a teljes
   QPU-job NEM megy ki; csak a kis kuszöb-job (gyűrű önmagában, néhány lépés);
   a kerék-állítás a következő, erősebb csatolású qubit-négyesre vár.
9. **SÖTÉTÁLLAPOT-TESZT** — külön kar, név szerint, saját cáfolati feltétellel.

## 1. A kiinduló gondolat és a lefordítása

(Az átirat a v1.0-ból, változatlan szándékkal — lásd `PLAN_WHEEL_v1.0.md` 1. fejezet:
a motivációk (forgó csapágyledorong, szupravezető gyűrű) analógiák, nem állítások;
a terv NEM állít mechanikus lebegtetést, g-eltérítést vagy új fizikát; a kérdés a
geometriai erősítés mérhető léte tankönyvi unitér dinamika keretében.)

A lefordítás kvantitatív váza:
- Gyűrű: 3 qubit (R1, R2, R3), páronkénti XY-csatolás, Peierls-fázisokkal
  (φ_f = π/6 / él; teljes fluxus Φ = π/2);
- Középpont: S qubit, három küllőn csatolva (0°, 120°, 240°);
- Keringési állapotok (a terv definíciói, fluxustól független hurokáram-
  sajátállapotok): |m=+1⟩ = (1, ω, ω²)/√3 forgó, |m=−1⟩ = (1, ω², ω)/√3
  ellenforgó, |m=0⟩ = (1, 1, 1)/√3 nem forgó (ω = e^{2πi/3}); minden élen
  |I| = 1/√3 (m=0-nál 0) — a sötétállapot-teszt ezért tisztán a keringés
  hatását méri;
- S kezdőállapot: pop-ágban |1⟩ (és |0⟩ a kompenzációs ágon); a megtartás-
  görbe R(k) = P(S = 1; k).

## 2. Az előre rögzített állítások (a fagyasztott fájl szerint)

Claim-család (Holm-korrekció, 99% CI): **W1, W2, W4-másodlagos, sötétállapot-teszt**.

- **W1 (fő):** AUC(wheel) legalább 25%-kal hosszabb megtartást ad, mint a
  static ÉS a ring_only — kritérium: AUC(wheel) − 1.25·AUC(static) > 0 és
  AUC(wheel) − 1.25·AUC(ring_only) > 0; egyoldalú bootstrap 99% CI alsó
  határai > 0, Holm után (claim-en belül Bonferroni).
- **W2 (fő):** a fordított irány (wheel_rev, m = −1) mérhetően eltérő
  megtartást ad — AUC(wheel) − AUC(wheel_rev) két oldalú 99% CI kizárja a
  0-t, Holm után.
- **W3 (kapuőr, mini-teszt):** flux-locking — lásd 8. fejezet: **SZÉTESŐ**
  tartomány; a teljes QPU-job NEM tervezhető; a kuszöb-job (gyűrű, pár lépés)
  az egyetlen szóba jövő futtatás; a kerék-állítás vár.
- **W4 (másodlagos, NEM memória-teszt):** AUC(pump_dir) > AUC(wheel)
  egyoldalú 99% CI + Holm; a W1/W2-be nem számít bele; az iránykövető lökés
  előre beállított iránya önmagában hajtja a forgást.
- **Sötétállapot-teszt (külön, név szerinti):** d1 = AUC(dark_m1) − AUC(dark_m0);
  d2 = AUC(dark_mm1) − AUC(dark_m0); p = max(p1, p2); 99% CI + Holm.
  Cáfolati feltétel (a Maya/tulajdonos vita közvetlen döntőbírája): ha egyik
  chirális ág sem válik el a m=0-tól a szigorú küszöb után, a "forgás tartja
  S-t" hipotézis ezen a berendezésen **cáfolva**; ha MINDKÉT chirális ág
  mérhetően tovább tartja S-t, a tulajdonos-ág kap támogatást.

## 3. Mérési protokoll

### 3.1 Qubit-választás és a TÉNYLEGES layout — ROUTING (javítás #1)
A csillag-menet layoutja (a kiindulás): **S = 125, R1 = 117, R2 = 124,
R3 = 126 (ibm_kingston, heavy-hex)**. A snapshot: `data/snapshot.json`
(2026-11-11T20:51:59Z; VALÓS backend-pillanatkép a csillag-menet beküldesekor;
NEM hardver-eredmény).

**A chipen nincs háromszög:** a 352 él között **0 db 3-klik**; 48 vertex
fokszáma ≥ 3. A 125 szomszédai pontosan {117, 124, 126} — vagyis a
horgonyok közvetlenül csak a középponton keresztül érhetők el; a 125-től
független legrövidebb gyűrű-él ~98–102 hop (használhatatlan).

A routing a **transzpilált áramkörökből** számolandó, nem idealizált gráfból.
A fagyasztott beállítás (a kaputilus-illesztés miatt szakmai kényszerűség):
**optimization_level = 0, seed_transpiler = 1234, basis cz/rz/sx/x/delay/id,
initial_layout [125, 117, 124, 126]** — ezen a szinten az identitás-kitöltők
ténylegesen lefutnak, tehát a static/ring_only/alone karok ugyanannyi 2Q
kaput fizetnek, mint a wheel (a szigorúbb opt=3-nál a 2Q-kitöltők elnyelődnek
— a kaputilus-illesztés megszűnne; az opt=3-as számok mellékadat).

**Mért routing-költség (K = 32 lépés, fagyasztva):**

| változat | 2Q (CZ) | megjegyzés |
|---|---|---|
| ideális (logikai, elmélet) | 388 CX-e | XY = 2 CZ; SZÜKSÉGES, de a chipen unobtaining |
| routolt, opt=3 | 606 | a kitöltők elnyelődtek — kaputilus-illesztés SÉRÜL |
| **routolt, opt=0 (FAGYASZTOTT)** | **700** | **minden karra azonos** (lásd 3.2) |
| virtuális gyűrű (S-mediált soros részleges SWAP-ok, 3 XY/él) | 772 CX-e | NEM egységkép-ekvivalens (K=6-nál ‖·‖≈0.94) — mediátor-analóg |

A routed verzió az IDEÁLIS áramkör lefordítása (unitarily azonos), a
virtuális gyűrű ezzel szemben KÜLÖNBÖZŐ effektív kölcsönhatás — ezért a
választás: **routed_transpiled** (a virtuális költsége nagyobb is).

**A routing kapuhiba-költsége (számszerűen, a snapshottal):**
- opt=0 CZ-eloszlás (wheel, K=32): (117,125): 236; (124,125): 232; (125,126): 232
- várható 2Q-hibaszám a teljes áramkörben: **1.05** (opt=3-nál 0.90; a
  idealizált, chipen elérhetetlen XY-számvitel 0.43; ideal-native ≈ 0.87);
- a routing a középponton (125) keresztül zajlik: S logikai qubitja a
  futás alatt 126/117/124 pozíciókon is megfordul — az Aer ezt PONTOSAN
  szimulálja (q3.2-q3.4, lásd 8. fejezet);
- **tárolási padló** (173 µs): S: 0.62; A1: 0.57; A2: 0.55; A3: 0.51 (T1);
- **flux-lock:** J/2π ≈ 460 kHz ≫ Ramsey-kötött szórás (≤ 2.2 kHz; a
  frequency_hz a snapshotban NULL — a valódi szórás lehet kisebb) —
  (a) TELJESÜL.

**W3 verdikt: SZÉTESŐ** — a (b) kapuhiba-kötelezettség (≤ 0.5 várt 2Q-hiba /
áramkör) bukik (1.05 > 0.5); a tárolási (c) teljesül; a flux-lock (a) teljesül.
A teljes QPU-job **NEM tervezhető**; a kuszöb-job (gyűrű önmagában, pár lépés,
a szétesés közvetlen kimutatására) az egyetlen szóba jövő futtatás, és az is
csak a tulajdonos/Control Agent beküldésével (az agent soha). A kerék-állítás
a következő, erősebb csatolású qubit-négyesre, vagy javított routingra vár.

### 3.2 Áramkör-család és KAPUTILUS-TÁBLA (javítás #3)
Minden kar: azonos össz-időtartam (173.056 µs ≈ K·(5 µs + 6·68 ns)), azonos
**logikai slot-szám (194)**, azonos **2Q-CX-ekvivalens (388)**, és
opt=0 routing után **azonos 700 CZ** — pontosan, routing mellett is:

| kar | prep m | fluxus | küllők | extra | CZ (opt=0) | AUC (Aer, előrejelzés) |
|---|---|---|---|---|---|---|
| wheel | +1 | π/6 | 0/120/240° | — | 700 | 0.471 |
| wheel_rev | −1 | π/6 | 0/120/240° | — | 700 | 0.482 |
| static | +1 | **OFF** | 0/120/240° | — | 700 | 0.476 |
| ring_only | +1 | π/6 | — | spoke-kitöltők | 700 | 0.730 |
| alone | +1 | π/6 | — | mind kitöltő | 700 | 0.732 |
| alone_DD | +1 | π/6 | — | X-echo/lépés | 700 | 0.815 |
| pump_blind | +1 | π/6 | 0/120/240° | vak pumpa | 700 | 0.472 |
| pump_dir | +1 | π/6 | 0/120/240° | iránykövető | 700 | 0.480 |
| pump_wrong | +1 | π/6 | 0/120/240° | fordított sorrend | 700 | 0.479 |
| cut | +1 | π/6 | 0/120/240°, él 3–1 kiv | — | 700 | 0.445 |
| dark_m1 | +1 | π/6 | 0/120/240° | S=\|1⟩ | 700 | 0.471 |
| dark_m0 | 0 | π/6 | 0/120/240° | S=\|1⟩ | 700 | 0.492 |
| dark_mm1 | −1 | π/6 | 0/120/240° | S=\|1⟩ | 700 | 0.482 |

A kitöltők: páronként 2 CZ (vagy a logikai szinten CX–CX / XY-slot), úgy
választva, hogy a transpiler NE tudja kineutralizálni őket (opt=0). A
**gate-count matching teljesül minden karra** — nincs olyan kar, amely a
túlkapuzás miatt veszít. Megjegyzés (őszinteség): a populációs metrikában a
ring_only és az alone **azonos kísérlet** (S-t csak a küllők érintik) — a két
karkölcsönös konzisztencia-ellenőrzés; a tervből való kivételéük TILOS
(a v1.1 kötelezővé teszi a ring_only-nak épp ezt, az alone mellé).

Alone_DD (a DD-kontroll): az alone-kar DD-megerősítése — a lépés végén
X-echo; a "forgás tartja vs sima DD-védelem" szétválasztására kötelező.

Pumpa-ágak (másodlagos): egy előre rögzített beállítás (m = 0.2, fi_p = 0,
f = 2Ω ≈ 1.396 rad/kör); a kick-költség 1Q (≈ 2e-4 hiba/impulzus) — a 2Q-
költség NEM nő; nulla nyereség várva (lásd v1.1 #5 és a frozen fájl
pump_block).

### 3.3 Kalibráció ugyanabban a jobban
S + a három gyűrű-qubit T1/Hahn-T2; kiolvasási hibák; az S–Ai él-csere-
oszcillációból a φ_eff kalibráció (ha > 15% eltérés a három pár között, a
preregisztrált elemzés figyelembe veszi — utólagos "szimmetrizálás" TILOS);
a gyűrű-qubitek frekvenciaszórása (a W3-hoz; a snapshotban frequency_hz =
null — a W3 küszöbe ezért a Ramsey-kötött becsléssel, illetve a valós
kapuhiba-kötelezettséggel dől el).

## 4. Mérőszámok és döntési szabály (előre rögzítve)

**Metrikák (fagyasztva):**
- R(arm, k) = P(S = 1; k), pop_branch = 1;
- AUC(arm) = a 9 ellenpont (k = 0..32, lépésköz 4) R-értékeinek átlaga;
- a "fél-megtartási idő" az oszcilláció miatt ILL-POSED (többszörös
  átlépés) — csak leíró statisztika, a döntésbe nem számit;
- D_S = |P1(1) − P1(0)| — másodlagos, a fő ítéletbe nem számít;
- koherencia-ág (S = |+⟩, X-mérés) — másodlagos; a CZ-kitöltők miatt csak
  azonos kitöltő-szerkezetű karok között értelmes.

**Bootstrap:** 2000 multinomiális minta a shot-okból; seed 20261111;
ci_level = 0.99; correction = "holm"; a claim-család név szerint
[W1, W2, W4_secondary, sotetallapot].

**Ítéletek (a fagyasztott fájl verdicts blokkja):**
- **TEXTBOOK:** a mért megtartás az Aer-jóslat 99% CI-sávján belül — az
  "effektus" (ha van) tankönyvi (a forgó minta zaj-kiatlagolása is ide
  számolandó);
- **ANOMALIA:** a mért megtartás meghaladja az Aer-jóslat felső 99% CI-jét
  — ELŐSZÖR kalibrációs/modellhibát kell keresni (T1/T2 drift, readout,
  csatolás-kalibráció), és csak utána jöhet bármilyen értelmezés; a claim
  az anomália feloldása előtt NEM kerül kikiáltásra;
- **NULL:** nincs mérhető előny a kontrollokkal szemben (W1 nem teljesül) —
  NULL-t NULL-ként közöljük.

**Pozitív kontroll (javítás #4):** a wheel-áramkörbe minden lépésben
Ry(2·0.15) a |1⟩ felé (ismert erősségű beépített stabilizáló hatás; SOSEM
QPU-kar) — az Aer futtatásban az elemzőnek a 99% CI-vel ki kell mutatnia a
bevitt hatást; ha nem mutatja ki, **az elemző hibás, nem a fizika**.
**Negatív kontroll:** a `cut` kar — a "kitört gyűrű" állapotban az elemzőnek
NULL-t kell jelentenie a wheel-hoz képest.

**Kapuőrség W3:** ha a számontartás szeteső — JELENLEG EZ ÁLL FENN —, a teljes
job NEM fut; a kuszöb-job csak a tulajdonos/Control Agent beküldésével.

## 5. Fázisok
- **0. fázis (megtörtént, ez a v1.1):** zajtalan + Aer-zajos szimuláció a
  TÉNYEGES transzpilált áramkörökön; a W3 kiszámítva (**SZÉTESŐ**); a
  kaputilus-tábla; a pozitív/negatív kontroll; a fagyasztás.
- **1. fázis:** QPU-job — **NEM tervezhető a jelenlegi W3-verdikt szerint.**
  A kuszöb-job (gyűrű önmagában, néhány lépés) az egyetlen szóba jövő
  futtatás; a teljes kerék-job ugyanilyen routing mellett nem értelmes.
- **2. fázis:** elemzés a fagyasztott szabály szerint; **record-first** —
  a beadott-állapot commitja megelőzi az eredményeket; NULL is record-first.

## 6. Kockázatok és ismert csapdák (előre kimondva)
- **Routing-seb (KRITIKUS):** a gyűrű S 125-ön keresztül routolódik — S
  logikai szerepe a futás alatt a fizikai 124/126 qubitekre is szivárog;
  az Aer pontosan szimulálja ezt (q3.2–q3.4). Ez maga is eredmény:
  a v1.0 gyűrűe nem realizálható a csillag-layouton ipari méretekben.
- **Kaputilus-eltérés kerülve** (opt=0 fagyasztás — lásd 3.1/3.2).
- **Cirkuláció vs populáció:** fázisérzékeny; a sötétállapot-teszt a saját
  ágán dönt.
- **Egyirányú szimuláció:** a zajmodell a snapshot MINTÁRA épül; a valódi
  berendezés szórását nem ismeri — az Aer-sáv modellfüggő, ezért ANOMALIA
  eseten először a modell az ellenőrzendő.
- **Várható kimenet:** NULL (Maya-előrejelzés) — lásd 7. fejezet; és a
  W3-kapuőrség miatt valószínűleg SOHA nem lesz mérés ezen a negyesen.
- **Kitöltők csapdája:** ha valaha más szintre váltjuk a transpile-t, a
  kaputilus-illesztés csendben megszűnik — az elemzőnek ezt minden
  futtatáskor ellenőriznie kell (az analysis.py fagyasztott ellenőrzései).

## 7. Várható eredmények — két várakozás egymás mellett (a mérés előtt, rögzítve)

- **Maya tankönyvi joslata (szószerint):** *"a három küllő hatása 0°, 120°,
  240° fásisal érkezve a középpontban kioltja egymást; a tankönyv szerint a
  forgás a középpontot nem tartja, csak nem zavarja — ezért a W1 és W2
  várhatóan NULL."* (Maya átnézése, 2026-11-11)
- **A tulajdonos joslata (Máté Róbert, 7. fejezet, 2026-11-11):** a Kerék
  mérhetően, erősen jobban tartja a középpontot — erős hatás.
- **A 0. fázis szimulációja a Maya-oldalra hajlik:** wheel AUC ≈ static
  (0.471 vs 0.476); a zajtalan wheel is oszcillál (0.75); a ring_only/alone
  jobb (0.73); a sötétállapot chirális és m=0 ágai az Aer-előrejelzésben
  szétnyílnak alig (0.471/0.492/0.482). A mérés dönt — ha mérés lesz.

## 8. 0. fázis — a számszerű eredmények (Aer/NEM hardware)

**Gate-count tábla (opt=0, K=32):** minden kar 700 CZ; logikai slot 194;
CX-ekvivalens 388; a routolt az ideálishoz képest +312 CZ (+80%).
**Virtális vs routolt:** 772 CX-e (nem ekvivalens, 0.94-es illeszkedés K=6-nál)
vs 700 CZ (unitarily azonos) → a fagyasztott választás: **routed_transpiled**.
**Kapuhiba-költség:** várható 2Q-hiba 1.05/áramkör (opt=0) / 0.90 (opt=3);
flux-lock arány 214 (teljesül); tárolási padló 0.51–0.62 (teljesül);
**W3 = SZÉTESŐ → a teljes QPU-job NEM tervezhető; a kuszöb-job az egyetlen
szóba jövő; a kerék-állitas vár.**
**Aer-előrejelzések (AUC, 99% sávval):** wheel 0.471; wheel_rev 0.482;
static 0.476; ring_only 0.730; alone 0.732; alone_DD 0.815; pump_blind 0.472;
pump_dir 0.480; pump_wrong 0.479; cut 0.445; dark_m1 0.471; dark_m0 0.492;
dark_mm1 0.482.
**Pozitív kontroll:** a beépített Ry(2·0.15) hatását az Aer futás mutatja
(AUC 0.52 vs 0.46 — a dryrunban az elemzőnek ki KELL mutatnia).
**Sötétállapot-teszt ára:** 27 áramkör (3 kar × 9 ellenpont), 4096 shot/áramkör,
S=|1⟩ indulás; a fő W1/W2-től függetlenül értelmezhető; saját cáfolati
feltétellel (lásd 2. fejezet).

## 9. A fagyasztott fájl (frozen_wheel_params.json) tartalma
`ci_level = 0.99`; `correction = "holm"`; `claim_family = ["W1", "W2",
"W4_secondary", "sotetallapot"]`; a routing-választás és -költség; a W3-verdikt
és az aktív ág (SZÉTESŐ → nincs teljes job); a kaputilus-tábla; az Aer-sávok;
a metrikák (AUC; a fél-megtartás ill-posed, kizárva); a bootstrap
(2000×, seed 20261111); a verdicts blocok; a pozitív kontroll; a
sötétállapot-teszt 27 áramköre; a prep-szögek (1e-12 verifikálva); az
expectations (Maya vs tulajdonos) — minden 2026-11-11-én fagyasztva, SHA-256-nal.

## 10. Szabályok és tilalmak (változatlanok)
No QPU az agenttől (tokent nem kap); csillag-anyagok olvasás-csak; secret-grep
commit előtt; `data/` nincs gitignorálva; szimuláció soha „HARDWARE" címkével;
NULL is record-first; a döntési szabály változtatása csak verziózott
"amended" verzióban; no post-hoc paraméter-halászat; minden commit után
hash jelentendő; a beküldés a tulajdonos/Control Agent feladata.
