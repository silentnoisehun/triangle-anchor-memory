# A Küszöb-job — Ring-Ramsey fáziszár-teszt (v1.0)

**Státusz: ELŐKÉSZÍTVE — NEM BEKÜLDVE.** A Kerék-menet W3-ágon előre
rögzített következménye (PLAN_WHEEL_v1.1, javítás #8: SZÉTESŐ → a teljes
QPU-job NEM megy ki; csak a küszöb-job jöhet szóba, és az is kizárólag a
tulajdonos/Control Agent beküldésével). Az agent QPU-t SOSEM indít; tokent
nem kap, tokent nem tárol.
**Dátum:** 2026-11-11 · **Repo:** triangle-anchor-memory · **Előzmény:** PLAN_WHEEL_v1.1, data/wheel_w3_report.json

## 1. Miért létezik ez a job

A W3-számvetés azt mondta ki: a 0. fázis szerint ezen a négyesen (S=125 hub,
R1=117, R2=124, R3=126) a routolt teljes Kerék-áramkör várható 2Q-hibája
≈ 1.05 — a 0.5-ös küszöb felett —, ezért a Kerék-job NEM tervezhető.
A küszöb-job az egyetlen szóba jövő következő lépés, és a legolcsóbb kérdés,
amire válaszolni tud: **képes-e ezen a négyesen egyáltalán koherens
Peierls-ring működni?** Ez NEM a Kerék-állítás tesztje; a teljes
Kerék-QPU-job továbbra is TILOS ezen a quadon.

## 2. Mit mér

    prep(m) [Givens, a Kerékkel azonos sablon] → k kör gyűrű-él (Peierls φ_f = π/6; teljes fluxus Φ = π/2; EDGE_ORDER rotáció) → prep† → mérés
    P_return = P(R1R2R3 = 000)     — az echo a VAKUUMBA ad vissza (prep∘prep† = I)

A prep a keringésmokd sajátállapotát állítja elő (m ∈ {+1, −1, 0}); ezek az
abszolút fázisukat tekintve sajátállapotok, de a STROBOSZKOPIKUS (3-kapús
körön) fejlődés miatt a zajtalan referenciájuk NEM 1 — ezért a zajtalan
értékeket a csomag exact (Statevector) szinten befagyasztja (lásd
circuits_manifest.json → p000_exact):

| kar   | k=0   | k=2    | k=4    | k=8    |
|-------|-------|--------|--------|--------|
| m+1   | 1.000 | 0.9509 | 0.8628 | 0.8384 |
| m−1   | 1.000 | 0.9475 | 0.8702 | 0.9208 |
| m0    | 1.000 | 0.8999 | 0.7539 | 0.8693 |
| pc    | 0.7778 (=7/9, analitikus) | — | 0.8501 | — |
| cut   | —     | 0.9029 | 0.6935 | 0.2460 |

A fáziskoherencia **fázisérzékeny** mennyiség — a populáció-only mérés NEM
erre a kérdésre ad választ; ezért echo (Loschmidt-típusú) protokoll.
A '000' kulcs mindaddig megtévesztő, amíg ki nem mondjuk: az NEM „semmi sem
történt", hanem „a jel coherent módon visszaért".

## 3. Karok és kontrollok (17 áramkör, 4096 shot/áramkör, 1 job-darab)

- **Fizikai karok:** m+1, m−1, m0 × k ∈ {0, 2, 4, 8} — a fáziszár-jel.
- **Pozitív kontroll (pc):** a prep után ismert RZ(π/3) a R2-n — a zajtalan
  referenciája **7/9** (analitikusan levezetett; a manifestben exact 0.7778);
  az elemzőnek KIMUTATNIA KELL ezt a dip-et, különben az elemző vak.
- **Negatív kontroll (cut):** a (R3,R1) gyűrű-él helyén identitás (CX·CX) —
  nyílt gyűrű; k ≥ 4-nél mérhetően el kell maradnia a zárt gyűrűtől
  (exact: 0.694 / 0.246 a k=4/8-nál vs 0.863 / 0.838).
- **k=0 ágak:** gép-egészség (prep+mérés+routing floor) — az aer-referencia
  szerint ≈ 0.91.

## 4. Fagyasztott beállítások

- Layout: S=125 (csak kötőelem, NEM mérjük), R1=117, R2=124, R3=126;
  routing a valós `data/snapshot.json` coupling-mapjén, **opt_level = 0**,
  seed_transpiler = 1234 (a Kerék-menettel azonos választás);
  basis: cz/rz/sx/x/delay/id.
- Shots: **4096** (a csillag-menet shot-politikájával azonos); összesen
  17 × 4096 = 69 632 shot; max_experiments = 300 → **egyetlen job-darabola**.
- A gyűrű-állapot retenció: **nincs 5 µs kitartás** (a Kerék-menet
  dwell-time-ját NEM másoljuk — a küszöb-job a kapu/routing koherenciát
  méri a vizsgált időskálán; eltérés a Kerék-montokollhoz képest tudatos és
  itt kimondva).
- **Nincs identitás-kitöltő kaputilus-illesztés** (ezen az újísérleten nincs
  összehasonlító kaputilus-kényszer); a `cut` CX·CX-e itt is I.
- A fagyasztott Kerék-fájl (`frozen_wheel_params.json`) **nem változik és
  nem is csökkenértékű**; a küszöb-job kimenete semmilyen Kerék-verdiktet
  nem ír át utólag.

## 5. Döntési szabály (előre rögzítve; EGY elsődleges végpont, 99% CI, nincs többszörös korrekció)

Binomiális/Wilson CI-k; egyoldalú, ahol azt mondjuk.

**(a) Gép-egészség — ELŐKAPU:** P(m+1, k=0) ≥ **0.70** ÉS a három kar
k=0-értéke egymástól legfeljebb 0.10-nel térhet el.
Bukás esetén ⇒ **AUTOMATIKUS HARASZTÁS** (lásd 7. §), nincs elsődleges
döntés.

**(b) ELSŐDLEGES (jog: „ROGZUL-ág" — a fáziszár ezen a négyesen elérhető):**
P(m+1, k=8) egyoldalú 99% CI alsó határa **≥ 0.5** ÉS
P(m+1, k=8) − P(cut, k=8) egyoldalú 99% CI **alsó határa > 0**
(SPAM-robust differenciál — a két kar ugyanazzal a mérési lázzal mérhető).

**(c) NULL:** (b) nem teljesül — a fáziszár nem mutatható ki ezen a
négyesen/routingon; a Kerék-állítás a következő, erősebb csatolású
négyesre vár. NULL-t NULL-ként közöljük.

**(d) SZÉTESŐ:** a PC-dip nem mutatható ki (P(pc, k=0) nem marad 99%-osan
m+1 k=0 alatt) VAGY P(cut, k=8) ≥ P(m+1, k=8) VAGY kalibráció/elemző
használhatatlan ⇒ a csomag **HARASZTOTT** + modell-audit; semmilyen fizikai
állítás nem készül.

**(e) Másodlagos, NEM a döntésbe:** ε̂ per round illesztés a k = 2,4,8
pontokra (a SPAM-tényező k=0-ból becsülve); csak riport.
**(f) Tárolási padló:** a leghosszabb áramkör t_est ≈ 16.7 µs, a legrosszabb
T1 (A3, 256.9 µs) → megtartás ≥ 0.937 — bőven a W3-padló felett.
**(g) Kapuhiba-költséglet:** max 92 CZ/áramkör; várható 2Q-hiba **≤ 0.126 ≤ 0.5**
(a W3 (b) küszöb 4× tartalékkal). Az Aer-előrejelzés szerint (teljes Aer
zaj-próba, lásd verification_last.json) P(m+1, k=8) ≈ **0.61 raw** — a
büntető döntés reális esélye megvan, a küszöb nem „kozmetikai".

## 6. Cáfolatképes pontok

Az elsődleges döntés CSAK (b)–(d); az Aer-zaj előrejelzés a csomagrészében
szerepel, de a döntés soha nem „mert az Aer ezt mondta" alapú — a mért
számok döntenek (ha mérés lesz).

## 7. Automatikus HALASZTÁS triggerel (a csomag státuszát automatikusan váltják)

1. Az agent-oldali ellenőrzés bármely kapuja bukik (verify_kuszob.py ≠ PASS);
2. a gép-egészség (a) bukna egy valódi futáson;
3. a transpile/routing befagyasztott beállításai nem tarthatók (pl. backend-változás);
4. a snapshot (`data/snapshot.json`) SHA-256-ja nem egyezik a csillag job_meta.json
   rögzített `snapshot_sha256`-jával (2acfda2e…);
5. a fagyasztott Kerék-fájl integritása sérülne (frozen_wheel_params.sha256≠tényleges).

HALASZTÁS esetén: a csomag státusza `HALASZTOTT — a kerek ezen a négyesen vár`;
semmilyen eredmény nem születik; a csomagot nem javítjuk titokban — minden
változtatás új verzió+revízió.

## 8. Sorrend (előírva)

1. A csomag elkészül (ez a dokumentum + `submission/kuszob/`);
2. **agent-oldali** ellenőrzés: `submission/kuszob/verify_kuszob.py --aer`
   (NEM független — előszűrés; az eredmény verification_last.json);
3. **TULAJDONOS / Control Agent felülvizsgálat — KÖTELEZŐ**, mielőtt bármilyen
   beküldésről szó lehet;
4. külön, explicit tulajdonosi döntés: beküldés VAGY halasztás. Az agent a
   beküldést SOSEM végzi el.

## 9. Mit NEM állít egy ilyen mérés

Nem bizonyítja a Kerék-állítást vagy a W1/W2-t; nem a sötétállapot-teszt;
nem „fáziszár az univerzumban" — csak: ezen a négyesen, ilyen routinggal,
ilyen időskálán, mérhető-e a rövidtávú Peierls-fáziskoherencia.

## 10. Kapcsolat a Kerékkel és a csillaggal

A Kerék-menet zárolva marad (teljes QPU-job NEM tervezhető); a csillag-menet
futó eredményeire a küszöb-job semmilyen hatással nincs. Ez a dokumentum és a
csomag a v1.1-es forgatókönyv végrehajtása, semmi több.
