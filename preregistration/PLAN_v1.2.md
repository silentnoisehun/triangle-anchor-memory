# PLAN v1.2 — AMENDED (felülírja a v1.0-t és a v1.1-et)

**EZ A FÁJL AMENDMENT.** A `PLAN_v1.0.md` és a `PLAN_v1.1.md` byte-ra
változatlanul marad — csendben átírni TILOS. A v1.2 a v1.1-et FELÜLÍRJA
(superseded): a P2/P3/anomália döntési küszöbök **95% CI → 99% CI + Holm**,
a csapat szabálya szerint, amely MINDEN kísérletre kötelező: **ANOMALIA
csak akkor adható ki, ha a mérés a tankönyvi jóslatot 99% CI-val,
Holm-korrekció után is túllépi.**

**Háttér (tények):** a négy csillag-job (dbqdaupabdes73fo2jrg,
dbqdav7v5hds73dfs6mg, dbqdavhabdes73fo2jug, dbqdavgk09pc73at2da0; beküldve
2026-11-11 20:52 UTC, ibm_kingston, S=125) **2026-11-12 reggel tulajdonosi
döntéssel VISSZAVONVA lett — mind a négy CANCELLED. MÉRÉSI ADAT NEM
KELETKEZETT.** Az állítás eldöntetlen. Az újraküldés csak külön tulajdonosi
döntéssel, kedvezőbb időpontban, lehetőleg időben tagolva (fair-share).
**Ez az amendment mérés ELŐTTI** — az adat nem teszi utólagossá a változtatást.

**Mi változott és miért (v1.1 → v1.2):**
1. **Claim-család előre rögzítve** a fagyasztott `frozen_params_v1.2.json`-ben:
   `["P2", "P3", "anomaly"]`, `correction = "holm"`, `ci_level = 0.99`,
   family-wise α = 0.01. A P1 (±20% arány-tűrés, pontbecslésre) NEM CI-döntés —
   változatlan.
2. **P2:** A_vissza(n3) ≥ A_vissza(n1) — a döntés mostantól 99% bootstrap-CI,
   ill. bootstrap-p (P_boot(A₃−A₁ ≤ 0)), Holm az anomáliával és a P3-mal.
3. **P3:** a `cut` kar feltétele (≥ 2 lépés eltolás VAGY ≥ 20% alacsonyabb
   csúcs) — 99% bootstrap-CI mindkét ágra; a claim p-értéke a két ág
   Bonferroni-maxa (min p × 2, ≤ 1). Holm a családban.
4. **ANOMALIA:** csak akkor mondható ki, ha bármely kar A_vissza-jének 99%
   bootstrap-CI alsó határa túllépi a fagyasztott zajtalan unitér maximumot,
   ÉS az anomaly-claim Holm után szignifikáns (p = max kar-Bonferroni a
   családon). Először modell-audit/kalibráció — claim SOHA nem születhet
   ANOMALIA-ból.
5. **A 0. fázis Aer/szimulációs adatai VÁLTOZATLANOK** — csak a döntési
   magasság nő; az előrejelzések nem mozdulnak.
6. **Semmi más nem változik:** φ = π/16, K = 32, ablakok, P1, kontrollok,
   koherencia-ág (MÁSODLAGOS), repo-szabályok.
7. **Beküldési tilalom:** újraküldés CSAK külön tulajdonosi döntéssel,
   kedvezőbb időpontban, lehetőleg időben tagolva (fair-share). Az agent QPU-ra
   NEM küld. A v1.2 merge-elése sem jogosít beküldésre.

A továbbiakban a v1.1 szövege következik érvényes szabályokkal. Szimulációs
eredmény SOHA nem kap „HARDWARE" címkét. NULL-t NULL-ként jelentünk.

---

> **Amended — miben és miért tér el a v1.1 a v1.0-tól**
>
> Kizárólag EGYETLEN szó javult: a v1.0 **195. sorában** a másolatban
> „countsból" szerepelt, az eredeti kísérletterv-szövegben **„countsokból"**
> áll (Control Agent auditja, 2026-11-11; a pontos eredeti szóalakot a
> tulajdonos / a Control Agent közölte). A különbség kizárólag szöveges —
> a beküldési folyamatot leíró mondat utolsó szava —, és NEM érinti a
> döntési szabályt, a tűréseket, az áramkör-családot, a fázisokat, a
> pontozást, a befagyasztott `preregistration/frozen_params_v1.2.json`-t
> (SHA-256: `e1d7a78888c531ba8ae7e5f84ed090649f5156774eabd763c8772d5d02d09429`),
> sem a döntési logika olvasási útját (a döntési szabály forrását). Minden egyéb sor betű szerint
> megegyezik a v1.0-val; a v1.0 (SHA-256:
> `12b22f18c468f05ab5ca10ed0bbb0819ed85e21564f3a3780b51c25508e38775`)
> változatlan maradt, és az is marad. Részletek: `preregistration/ERRATA.md`.
>
> Ez az „amended" megjelölésű változat a helyesírás formális helyreállítása;
> semmilyen tartalmi döntést nem módosít, és új preregisztrált tartalmat
> NEM vezet be.
>
> ---

*Ötlet: Máté Róbert (2026-11-11) — „három sarokpontról gumikkal a középpontra
kipöckölve; indítás után magát húzza". Terv és szigorítás: Control Agent.
Állapot: TERV — QPU-futtatás még nem történt. Ez a fájl a futtatás előtt
készült, és a benne rögzített döntési szabályok utólag nem módosíthatók;
módosítás csak verziószámozott kiegészítéssel, „amended" megjelöléssel.*

---

## 1. A kiinduló gondolat és a lefordítása

A rezonátor-projekt 1. fázisa kimérte: az olvashatósági idő az energiával
csak logaritmikusan nő (energiaduplázás: +0,347τ). Ebből Máté következtetése:
**nem több energia kell, hanem kevesebb veszteség és jobb szerkezet.**

A háromszög-kép: egy középponti bitet három sarokponthoz rugalmas csatolás
(„gumi") köt. Kitérítés után a szerkezet külső beavatkozás és további
energia nélkül húzza vissza a bitet középre.

Chipre fordítva:
- **középpont** = egy qubit (S), amelynek az állapotát őrizzük;
- **három sarokpont** = S három, fizikailag csatolt szomszédja (horgonyok,
  A1, A2, A3), rögzített kezdőállapotban (|0⟩);
- **„gumi"** = részleges csere-csatolás (XY-exchange / részleges SWAP)
  S és minden horgony között, azonos erősséggel (szimmetrikusan);
- **kitérítés** = S kezdőállapota (|1⟩, ill. a koherencia-ágban |+⟩);
- **„magát húzza"** = a csatolások unitér fejlődése során az S-be írt
  gerjesztés szétoszlik a horgonyokra, majd mérhetően **visszaáramlik
  S-be** — pontosan az a visszaáramlási jelenség, amelyet a rezonátor
  3. fázisa egyetlen szomszéddal már kimutatott (BLP = 0,4190,
  kontroll 0,0000). Az új kérdés: **a háromszög-szimmetria erősíti-e,
  gyorsítja-e és szabályosabbá teszi-e ezt a visszahúzást.**

## 2. Az előre rögzített fizikai állítások

Egyetlen gerjesztés alterében a csillag alakú (K1,N) csatolási gráf
unitér fejlődése analitikusan ismert. Ebből a következő, számszerű
jóslatok rögzíthetők a futtatás előtt:

- **P1 (sebesség):** a visszahúzás első visszatérési csúcsának ideje
  N horgony esetén a csatolási erősség √N-szeresével skálázódik:
  **t_vissza(N) ∝ 1/√N**. Tehát a 3 horgonyos visszatérés az
  1 horgonyoshoz képest kb. **1/√3 ≈ 0,58-szoros idő alatt** érkezik.
- **P2 (teljesség):** ideális, veszteségmentes esetben a visszatérés
  teljes (D(k) visszaér a kiinduló értékre). A valós chipen a visszatérési
  csúcs magassága a koherencia-veszteséggel csökken; az állítás az, hogy
  azonos össz-idő mellett a 3 horgonyos csúcs **nem alacsonyabb**, mint
  az 1 horgonyos rendszer második csúcsa ugyanazon időpontban — a
  gyorsabb visszatérés kevesebb veszteségi időt jelent.
- **P3 (szimmetria):** ha az egyik „gumit elvágjuk" (egy horgony csatolását
  kihagyjuk, miközben az áramkör teljes ideje változatlan), a visszahúzási
  kép mérhetően eltorzul (a csúcs eltolódik és/vagy lecsökken) a
  szimmetrikus 3 horgonyos esethez képest. A geometria tehát okozati,
  nem csak a horgonyok száma számít.

**Cáfolat:** ha a visszatérési idők nem követik az 1/√N skálát (±20%-on
túl), vagy a 3 horgonyos visszahúzás nem különbözik szignifikánsan az
1 horgonyostól, vagy az „elvágott gumi" kontroll ugyanazt adja, mint a
szimmetrikus — az állítás megbukott, és ezt így kell kimondani.

**Kifejezetten NEM állítjuk:** nem állítjuk, hogy a rendszer csillapodva
„leül középre" (a chipen nincs súrlódás; a visszahúzás oszcillál, csúcsok
sorozatában tér vissza). Nem állítjuk, hogy ez új fizika; a geometriai
erősítés mérhető volta a kérdés, szövegkönyvi unitér dinamika keretében.

## 3. Mérési protokoll

### 3.1 Qubit-választás
Olyan S qubit kell, amelynek **három fizikai szomszédja** van a csatolási
térképen (Heron rácsban ilyen létezik). Pontozás az auditált szabály szerint:
`min(T1,T2)/(1+20ε)` az S-re, szorozva a három horgony ugyanezen
pontszámainak minimumával — a láncot a leggyengébb horgony határozza meg.
A választás a futtatás előtti pillanatképből, a terv lezárása (hash) előtt
történik, és utána nem változtatható.

### 3.2 Áramkör-család
Minden kar azonos össz-időtartamú; a „gumik" részleges SWAP-lépések
φ szöggel, k = 0…K lépésben (φ és K a 0. fázis szimulációjából, futtatás
előtt rögzítve — várhatóan φ = π/16, K = 32).

| kar | leírás | szerepe |
|---|---|---|
| `n0` | S egyedül, csatolás nélkül, ugyanannyi üres idő | alapvonal (saját T1/T2 romlás) |
| `n1` | S–A1 csatolva | egy gumi (a rezonátor 3. fázis megfelelője) |
| `n2` | S–A1, S–A2 | két gumi |
| `n3` | S–A1, S–A2, S–A3 szimmetrikusan | **a háromszög** |
| `cut` | 3 horgony jelen, de az A3 csatolása kihagyva, idő kitöltve | „elvágott gumi" kontroll (P3) |
| `noisy` | 3 horgony, de a horgonyok \|+⟩ állapotból indulnak | zajos környezet kontroll |

Szimmetria-szabály: az egy körben alkalmazott páronkénti csatolások
sorrendjét körönként forgatjuk (A1A2A3 → A2A3A1 → …), hogy a sorrendi
aszimmetria ne hamisítsa meg a szimmetria-állítást.

Két mérési ág minden karon:
- **populációs ág:** S kezdőállapota |0⟩ és |1⟩, mérés Z-bázisban;
  a távolsági görbe D(k) = |P₁⁽¹⁾(k) − P₁⁽⁰⁾(k)| (mint a 3. fázisban);
- **koherencia-ág (másodlagos):** S kezdőállapota |+⟩, mérés X-bázisban;
  azt mutatja, hogy a visszahúzás a fázist is visszahozza-e, vagy csak
  a populációt. Külön kell jelölni, nem keverhető a fő állításba.

### 3.3 Kalibráció ugyanabban a jobban
- S és mindhárom horgony T1, Hahn-T2 karjai;
- kiolvasási hibák (készülék-kalibrációs áramkörök);
- csatolás-erősség kalibráció az `n1` karból (a csere-oszcilláció
  periódusából tényleges φ_eff minden S–Ai párra); ha a három pár
  φ_eff értéke 15%-nál jobban eltér, azt a preregisztrált elemzésnek
  a szimmetria-állításnál figyelembe kell vennie — utólagos
  „szimmetrizálás" tilos.

## 4. Mérőszámok és döntési szabály (előre rögzítve)

Fő mérőszámok karonként, bootstrap (2000×, multinomiális) CI-val:
- `t_vissza`: az első visszatérési csúcs lépésindexe (a szimuláció által
  előre kijelölt keresési ablakban);
- `A_vissza`: az első visszatérési csúcs D-magassága, az induló D-re
  normálva;
- `BLP`: a pozitív D-növekmények összege (a 3. fázissal azonos módon).

Ítélet:
- **TEXTBOOK–MEGERŐSÍTVE (geometriai visszahúzás):** teljesül P1
  (t_vissza arányok 1 : 0,71 : 0,58, ±20% tűréssel N=1,2,3-ra),
  P2 (A_vissza(n3) ≥ A_vissza(n1) az n3 első csúcsának idején, 99% CI
  alapján nem alacsonyabb — bootstrap-p ≤ a Holm-küszöb), és P3 (a `cut`
  kar első csúcsa legalább 20%-kal alacsonyabb vagy legalább 2 lépéssel eltolódik a `n3`-hoz
  képest, 99% CI-val alátámasztva). Az P2 és P3 a három tagú
  claim-családba ([P2, P3, anomália]) tartozik; a családon belül Holm,
  α = 0.01.
- **NULL (geometria nem segít):** ha a fenti feltételek bármelyike nem
  teljesül, a címke NULL, és a három kar görbéit egymásra rajzolva kell
  közölni. Nem használható a „beállítottság/optimalizálás" utólagos
  újraértelmezése.
- **ANOMÁLIA:** csak akkor mondható ki, ha a mért visszatérés bármely
  karon a teljesen unitér, zajtalan szimuláció által megengedett maximumot
  99% CI-val túllépi ÉS az anomaly claim Holm után szignifikáns. (Ez zárt
  rendszerben lehetetlen; ha megjelenik, az mérési vagy kalibrációs hibát
  jelez — először azt kell keresni.)

A φ, K, a csúcs-keresési ablakok és a tűrések számszerű értékeit a
0. fázis (szimuláció) futása után, de minden QPU-beküldés előtt, az
`preregistration/` mappában hash-elt fájlban kell rögzíteni.

## 5. Fázisok

- **0. fázis — szimuláció (ingyen, QPU nélkül):** zajtalan és zajos
  (a pillanatkép T1/T2/ε értékeivel épített) szimuláció minden karra;
  ebből φ, K, ablakok, várt görbék. Pozitív kontroll: szándékosan rontott
  szimulációnak (pl. csatolások kikapcsolva) NULL-t kell adnia az
  elemzőnek.
- **1. fázis — QPU (1 job):** az összes kar + kalibráció egyetlen jobban,
  sorsolt sorrendben (shuffle), a sorrend a job_meta-ban rögzítve;
  nyers counts azonnal mentve és hash-elve.
- **2. fázis — elemzés:** offline, token nélkül újraszámolható;
  független újraellenőrzés a nyers countsból a korábban bevált módon.

## 6. Kockázatok és ismert csapdák (előre kimondva)

1. **A horgonyok zajforrások is.** Három gumi = három további romló
   qubit. Ha az A_vissza(n3) alacsonyabb, az valószínűleg ez — ezért
   a `noisy` kar és a horgony-kalibráció kötelező, nem dísz.
2. **Áthallás (crosstalk) és sorrendi hatások** a páronkénti csatolásoknál;
   a forgatott sorrend és az azonos össz-idő ezt hivatott felfedni.
3. **A „visszahúzás" nem egyensúlyba ülés.** Aki „leül középre" jellegű
   görbét vár, csalódni fog; a jóslat csúcsok sorozata, csökkenő
   amplitúdóval. A kommunikációban is így kell leírni.
4. **Egyetlen jobban = egyetlen napi kalibráció.** Az eredmény ahhoz a
   chipállapothoz kötött; erősebb állításhoz ismétlés kell — ezt a
   következtetésekbe bele kell írni, nem elhallgatni.
5. **A koherencia-ág várhatóan gyengébb** a populációsnál; ha csak a
   populáció tér vissza, az az eredmény, így kell közölni.

## 7. Repo-felépítés az agentnek (token nélkül végezhető)

Új repo: `triangle-anchor-memory`

```
preregistration/   a terv hash-elt, időbélyeges változata (futtatás előtt)
src/config.py      φ, K, karok, döntési küszöbök (a 0. fázis után fagyasztva)
src/circuits.py    kar-építők + kalibrációs áramkörök
src/sim.py         zajtalan + zajos szimuláció, várt görbék, pozitív kontroll
src/run.py         beküldő — tokent CSAK környezeti változóból olvas
src/analysis.py    D(k), BLP, csúcskeresés, bootstrap, ítélet
dryrun.py          QPU nélkül mindent végigfuttat; TEXTBOOK/NULL ágak + kontroll
data/              job_meta.json, raw_counts.json (NEM gitignore-olt!)
```

Kötelező szabályok az agentnek (a rezonátor-kör hibáiból tanulva):
- token sosem fájlban; minden push előtt grep-ellenőrzés titokra;
- `data/` nem kerülhet .gitignore-ba; a job ID-t a beküldés pillanatában
  menteni, külön a lekérdezéstől; commit-üzenetbe csak job_meta szerinti
  azonosító kerülhet;
- a döntési szabály a preregisztrált fájlból olvasandó, nem a kódba
  „beleégetett" szövegként utólag módosítható.

A QPU-beküldést nem az agent végzi: a kód auditja után a futtatást a
Control Agent indítja a tulajdonos által adott, rövid életű tokennel;
a jobok állapotát a tulajdonos jelzi; a független újraszámolás a nyers
countsokból történik.

---

*Aláírás nélküli munkapéldány — a preregisztrált változat a repóban,
hash-szel és dátummal lesz hatályos.*
