# A Kerék — forgó gyűrű által tartott középpont — kísérletterv (v1.0, transport)

**Állapot:** terv + 0. fázis (szimuláció) — **QPU még nem futott**
**Dátum:** 2026-11-11 (Máté Róbert, tulajdonos; terv szerzője: Control Agent;
az ötlet és az eredeti élmény Máté Róberté)
**Repo:** triangle-anchor-memory — külön menet a csillag- és a gyűrű (PLAN_RING) anyag mellé
**Elsőbbség:** ez a fájl preregisztációs dokumentum; fagyasztás csak a v1.1 (amended) után, első verzióként — lásd `preregistration/PLAN_WHEEL_v1.1.md` és `preregistration/frozen_wheel_params.json`.

## 1. A kiinduló gondolat és a lefordítása

A tulajdonos ötlete (az eredeti élmény szintjén, motivációként): mint a forgó
csapágyledorong vagy a szupravezető gyűrű, amelyben a keringő áram "megtartja" a
középpontot — a **Kerék** három sarkot (gyűrű) köt össze egy középponttal, és a
keringés (forgatás) elvileg "lebeg-teti" a középpontot.

A kísérleti lefordítás: 3 gyűrű-qubit (R1, R2, R3) páronkénti XY-csatolással
(szintetikus fluxussal, φ_f = π/6 élenként, a gyűrű teljes fluxusa Φ = π/2),
hozzájuk kapcsolva a középpont S qubit a három küllőn (0°, 120°, 240° fázissal).
A keringés iránya (m = +1 forgó / m = −1 ellenforgó / m = 0 nem forgó) maga a
felvetett "tartóerő" iránya.

**A motivációk (forgó csapágyledorong, szupravezető gyűrű) ANALÓGIÁK, nem
állítások.** A terv NEM állítja, hogy:
- mechanikus lebegtetés vagy g-eltérítés mérhető (ez kvantum-áramkör, nem mechanika);
- az ekvivalencia-elv értelmében vett hatásról van szó;
- a hatás új fizika — csak a geometriai erősítés MÉRHETŐ lété a kérdés,
  tankönyvi unitér dinamika keretében.

A csillag-menet (PLAN_v1.0 / PLAN_v1.1 amended, frozen_params.json, 4 jobs QPU-ra
beadva — QUEUED) külső kontrollként és alapvonalként szolgál; a csillag-anyaghoz
**tilos hozzányúlni**. A gyűrű-menet (PLAN_RING_v1.0, v1.1) ELŐZŐ tervfázis —
a Kerék-menet ebből építkezik (a gyűrű keringetési állapotok megtartása), de a
kutatási kérdés új: nem a gyűrű tulajdonsága, hanem a **középpont megtartása**
a forgó gyűrű mellett.

## 2. Az előre rögzített fizikai állítások

A állítások A PRIORI, mérés előtt rögzítve; a várakozások a 7. fejezetben.

- **W1 (fő):** S fél-megtartás (AUC-metrika, lásd 4. fejezet) a wheel karban
  legalább **25%-kal hosszabb**, mint a static ÉS a ring_only karban.
- **W2 (fő):** a fordított keringési irány (wheel_rev, m = −1) mérhetően
  eltérő középpont-megtartást ad, mint a wheel (m = +1).
- **W3 (mini-teszt, kapuő):** flux-locking küszöb — a csatolás (mozgás
  frekvenciája) nagyobb-e mint a qubitek frekvencia-szórása + zaj; a
  küszöbszámítás a TÉNYLEGES layouton, valós kapuszámokkal és kapuhibákkal
  dönt a QPU-jogosultságról. Ha nem teljesül: **nincs teljes QPU-job** —
  csak a kis kuszöb-job (gyűrű önmagában, néhány lépés) tervezhető.
- **W4 (másodlagos, v1.1 javítás #5):** az iránykövető (direction-tracking)
  paraméteres pumpa — **másodlagos** a fő állításokhoz képest, mert az
  előre beállított iránynak önmagában is van hajtó hatása, így nem memória-
  teszt; csak a középpont-megtartásról szól, és a W1/W2-be nem számít bele.

## 3. Mérési protokoll

### 3.1 Qubit-választás és layout
A csillag-menet layoutja a kiindulás (S = 125, horgonyok 117/124/126,
ibm_kingston, heavy-hex). A gyűrű-élek fizikailag NEM léteznek: a heavy-hex
rácsban NINCS háromszög (0 db 3-klik a 352 él között; 48 vertex fokszáma ≥ 3).
A gyűrű-éleket SWAP-hálózattal kell végigvinni a `125`-ön (és minden más út
≥ ~100 hop — használhatatlan). A 0. fázis a TÉNYLEGES transzpilált áramkörökből
dolgozzon (a routing nem idealizált gráf), lásd v1.1 javítás #1.

### 3.2 Áramkör-család (minden kar azonos össz-időtartam és azonos 2Q-kapuszám)

| kar | prep (m) | gyűrű fluxus | küllők | extras | szerepe |
|---|---|---|---|---|---|
| `wheel` | +1 | π/6/él | 0/120/240° | — | a teljes szerkezet (fő kar) |
| `wheel_rev` | −1 | π/6/él | 0/120/240° | — | ellenforgó (W2) |
| `static` | +1 | **OFF** (φ_f = 0) | 0/120/240° | — | álló fázisoscilláció kontroll |
| `ring_only` | +1 | π/6/él | — | spoke-kitöltők | keringő gyűrű, S küllők nélkül |
| `alone` | +1 | π/6/él | — | minden slot kitöltő | S magában (idő-kitöltve) |
| `alone_DD` | +1 | π/6/él | — | X-echo / lépés | DD-kontroll (v1.1 #3) |
| `pump_blind` | +1 | π/6/él | 0/120/240° | vak pumpa | másodlagos (W4) |
| `pump_dir` | +1 | π/6/él | 0/120/240° | iránykövető lökés | másodlagos (W4) |
| `pump_wrong` | +1 | π/6/él | 0/120/240° | fordított sorrendű lökések | W4 kontrollja |
| `cut` | +1 | π/6/él (él 3–1 kivéve) | 0/120/240° | — | megszakított gyűrű — negatív kontroll |
| `dark_m1` | +1 | π/6/él | 0/120/240° | S=\|1⟩ indul | sötétállapot-teszt, forgó |
| `dark_m0` | 0 | π/6/él | 0/120/240° | S=\|1⟩ indul | sötétállapot-teszt, nem forgó |
| `dark_mm1` | −1 | π/6/él | 0/120/240° | S=\|1⟩ indul | sötétállapot-teszt, ellenforgó |

A keringési sajátállapotok a terv saját definíciói (fluxustól független
hurokáram-sajátállapotok): |m=+1⟩ = (1, ω, ω²)/√3, |m=−1⟩ = (1, ω², ω)/√3,
|m=0⟩ = (1, 1, 1)/√3 (ω = e^{2πi/3}); minden élen |I| = 1/√3 (m=0: 0) — a
"sötétállapot-teszt" ezért tisztán a fázisok (keringés) hatását méri.

Szimmetria-szabály: az egy körben alkalmazott páronkénti csatolások sorrendje
körönként forog (ORDERS: [01,12,13] → [12,13,01] → [13,01,12]), hogy a sorrendi
aszimmetria ne hamisítsa meg az eredményt.

Két mérési ág:
- **populációs ág (fő):** S kezdőállapota |1⟩ (és |0⟩ a kompenzációs futásokhoz),
  Z-mérés; a megtartás-görbe R(k) = P(S=1; k);
- **koherencia-ág (másodlagos):** S kezdőállapota |+⟩, X-mérés (a 0/120/240
  küllők elvileg fázis-érzékenyek) — a populációs ágtól függetlenül jelölve,
  a fő ítéletbe nem számít bele.

### 3.3 Kalibráció ugyanabban a jobban
- S és mindhárom gyűrű-qubit T1, Hahn-T2 karjai;
- kiolvasási hibák;
- csatolás-erősség kalibráció a legkisebb hatásos él-párra;
- a ring-qubitek frekvenciaszórása (a W3-hoz);
- ha a csatolás-φ_eff eltérése > 15% a három pár között, azt a preregisztrált
  elemzésnek figyelembe kell vennie — utólagos "szimmetrizálás" TILOS.

## 4. Mérőszámok és döntési szabály (előre rögzítve)

Fő mérőszámok (a k = 0..32, lépésköz 4 ellenpontokon, bootstrap 2000×,
multinomiális, seed 20261111):
- `AUC(arm)` = a 9 ellenpont R(k) értékeinek átlaga — a "megtartás"
  skaláris mérőszáma;
- W1: AUC(wheel) − 1.25·AUC(static) > 0 és AUC(wheel) − 1.25·AUC(ring_only) > 0
  (egyoldalú bootstrap 99% CI alsó határa > 0, Holm után);
- W2: AUC(wheel) − AUC(wheel_rev) két oldalú 99% CI kizárja a 0-t (Holm után);
- W4 másodlagos: AUC(pump_dir) − AUC(wheel) egyoldalú 99% CI > 0 (Holm után);
- sötétállapot-teszt: d1 = AUC(dark_m1) − AUC(dark_m0) és d2 = AUC(dark_mm1) −
  AUC(dark_m0); p = max(p1, p2) (Bonferroni a claim-en belül); 99% CI + Holm.

A "fél-megtartási idő" az oszcilláció miatt **ill-posed** (többszörös
átlépés); csak leíró statisztika, a döntésbe nem számít.

Ítéletek (a fagyasztott fájlban, ld. v1.1 javítás #2):
- **TEXTBOOK:** a mért megtartás a fagyasztott Aer-jóslat 99% CI-sávján belül
  van (az "effektus" tankönyvi hatásokkal magyarázható);
- **ANOMALIA:** a mért megtartás meghaladja az Aer 99% CI felső határát
  (először kalibrációs/modellhiba keresendő, csak utána következik bármi);
- **NULL:** nincs mérhető előny a kontrollokkal szemben (W1 nem teljesül).

## 5. Fázisok
- **0. fázis (ez a dokumentum + szimuláció):** zajtalan és Aer-zajos
  szimuláció a TÉNYLEGES transzpilált áramkörökön; a W3-küszöb kiszámolása;
  a fagyasztás (frozen_wheel_params.json + .sha256) — EZZEL a v1.1 verzióval.
- **1. fázis (NEM agent):** QPU-job, ha W3 ROGZUL — a jelenlegi W3-verdikt
  szerint **NEM tervezhető**; csak a kis kuszöb-job jöhet szóba. A beküldés a
  tulajdonos/Control Agent feladata; az agent QPU-t nem indít, tokent nem kap.
- **2. fázis:** elemzés a fagyasztott szabály szerint, **record-first**:
  a beadott-állapot commitja megelőzi az eredményeket; NULL is record-first.

## 6. Kockázatok és ismert csapdák (előre kimondva)
- **Routing-költség (KRITIKUS):** a gyűrű-élek csak SWAP-hálózattal
  vihetők végig; a 0. fázis kapuszámait a transzpilált áramkörből számoljuk
  (lásd v1.1 javítás #1 és a frozen fájl routing blokkját).
- **Rejtett kaputilus-eltérés:** a static és ring_only karok kaputilus-
  illesztettek kell legyenek, különben a több kapu dönti el a versenyt
  (lásd v1.1 javítás #3 és a terv kaputilus-tábláját).
- **A forgatás és a DD összekeverése:** a "forgás tartja" nem lehet
  ökove a puszta DD-védelemnek — ezért kötelező az alone_DD kontroll.
- **Cirkuláció vs populáció-visszaáramlás:** a keringési információ
  fázisérzékeny; populációs mérés önmagában nem elég — a sötétállapot-teszt
  a saját ágán, név szerint utal rá.
- **Oszcilláló megtartás:** a "half-survival" mérőszám ill-posed — a tervből
  kiváltva (leíró statisztika), a döntés AUC-n történik.
- **Modell-túlhatás:** ha a mért eredmény az Aer-jóslat 99% CI-t túllépi,
  először a zajos modellt és a kalibrációt kell vizsgálni (nem az új fizikát).
- **Pozitív kontroll hiánya:** a "kitört gyűrű → NULL" negatív kontroll mellé
  kötelező pozitív kontroll (v1.1 #5) — az elemző vaksága az elemző hibája,
  nem a fizikáé.
- **Várható kimenet (őszinteség):** a 2. fázis valószínű kimenete NULL
  (Maya-előrejelzés, lásd 7. fejezet és a frozen fájl expectations blokkja).

## 7. Várható eredmények — két várakozás, egymás mellett (a mérés előtt, rögzítve)

- **Maya tankönyvi joslata (szószerint a tervbe):** *"a három küllő hatása
  0°, 120°, 240° fázissal érkezve a középpontban kioltja egymást; a tankönyv
  szerint a forgás a középpontot nem tartja, csak nem zavarja — ezért a W1
  és W2 várhatóan NULL."* (Maya átnézése, 2026-11-11)
- **A tulajdonos joslata:** a Kerék mérhetően, erősen jobban tartja a
  középpontot, mint a kontrollok (a terv 7. fejezetének eredeti
  fényében, 2026-11-11).
- **A 0. fázis szimulációja a Maya-oldalra hajlik** (wheel ≈ static AUC;
  ring_only/alone megtartása jobb; a zajtalan wheel is oszcillál) — de a
  mérés dönt, ha mérés lesz; a szimuláció nem bizonyíték, csak jelzés.

## 8. Repo-felépítés az agentnek (token nélkül végezhető)
- `preregistration/PLAN_WHEEL_v1.0.md` — ez a dokumentum;
- `preregistration/PLAN_WHEEL_v1.1.md` — amended (a fagyasztás alapja);
- `preregistration/frozen_wheel_params.json` + `frozen_wheel_params.sha256`;
- `src/wheel/` — áramkörök, zaj, szimuláció, elemző, W3-számítás;
- `dryrun_wheel.py` — QPU nélkül végigfut (zajtalan→TEXTBOOK-sáv,
  pozitív kontroll→kimutatva, cut→NULL);
- `README.md` — „A Kerék-menet" szakasz.

A token-változót (`IBM_QUANTUM_TOKEN`) az agent nem használja; a commitok előtt
titok-grep; minden commit után hash jelentendő; a csillag anyagok (PLAN_v1.0/
v1.1, frozen_params.json, src/) olvasás-csak; a `data/` nincs gitignorálva.
