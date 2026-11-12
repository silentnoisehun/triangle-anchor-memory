# PLAN_KUSZOB v1.3 — AMENDED (mérés-hiány javítás; felülírja a v1.2-t KIZÁRÓLAG a beküldési payload mérés-huzalozását és a G8 kaput illetően; a v1.0, a v1.1 és a v1.2 byte-ra változatlan)

**EZ A FÁJL AMENDMENT.** A `preregistration/PLAN_KUSZOB_v1.0.md`
(`f865faed91b6ba3fd1b7cdae1629be8f4fbfbdf6ce405c67205783aea0e49cc8`),
a `preregistration/PLAN_KUSZOB_v1.1.md`
(`dfba74ff46b7f08fd0920428e43e603bff8bb0f37adc9bd723e865324aba9044`)
és a `preregistration/PLAN_KUSZOB_v1.2.md`
(`a1c58739c1ddfacae72b765b3890ae71545dc41f9f92636272bd375b67c7cc0b`)
byte-ra változatlanul megmaradnak a történet részeként — csendben átírni TILOS.
A v1.3 a v1.2-t FELÜLÍRJA (superseded) KIZÁRÓLAG abban, hogy a beküldési
payload minden áramköre a `build_kuszob.py` saját `with_measurements()`
lépésével kapja meg a méréseket (a mérés-huzalozás a fagyasztott QASM-okéval
AZONOS — agent-oldali újraépítési ellenőrzés: 17/17 byte-azonos), ÉS hogy
új, kötelező **G8 mérés-kapu** lépett életbe a beküldés útján (l. alább).
Minden más — a seed-hash (`83f43b94…`, változatlan a v1.2-höz képest),
a döntési szabály, a küszöbök, a kar-felépítés, a layout, az opt=0, a
`seed_transpiler=1234`, a CZ-kapu és minden fagyasztott fájl — a v1.2-ből
ÖRÖKLŐDIK. **A seed hash-e NEM változott; adat NEM keletkezett.**
**Dátum:** 2026-11-12 · **Előzmény:** a 2026-11-12 14:49 UTC-kor beadott küszöb-job (`dbqt3q9abdes73fosj8g`) ERROR 1515 hibája és a Control Agent lokalizált szkript-oka · **Repo:** triangle-anchor-memory

## A mérés-hiány ténye (rögzítve — a v1.3 indoka)

A 2026-11-12 14:49 UTC-kor, tulajdonosi döntéssel, a fagyasztott
`submit_kuszob.py` (v1.2) által beadott küszöb-job (`dbqt3q9abdes73fosj8g`,
ibm_kingston, 17 áramkör, 4096 shot) **19:16 UTC-kor ERROR állapotban
végzett, adat NEM KELETKEZETT**. IBM hibakód **1515**:
*„Circuits without measurements are not allowed."*

A Control Agent lokalizált oka: a `submit_kuszob.py` `_pruned_circuits()`
a `build_kuszob.transpile_pruned()` által visszaadott, MÉRÉS NÉLKÜLI
áramköröket adta tovább a `SamplerV2.run()`-nak — a QASM-generálás
(`build_kuszob` §QASM) ezzel szemben a `with_measurements()` lépést
használja. A meglévő kapuk (incl. G7 CZ) a mérést soha nem ellenőrizték —
ezért ment át minden kapun a hibás beküldés. **A döntési szabályra, a
fagyasztott elemzőre és a QASM-okra ez nincs hatással; a kísérlet mérhető-e
a kérdésre a válasz CSAK egy új, külön tulajdonosi/Control Agent döntéssel,
újraküldéssel adható meg.**

## Mi változott és miért (v1.2 → v1.3)

1. **A beküldési payload a `with_measurements()` után megy a backend-transzpilációra**
   (a `submit_kuszob.py` v1.3 `_pruned_circuits()` emellett a
   `transpile_pruned()` által visszaadott `final_layout`-ot is továbbadja;
   a mérés-huzalozás: c0 ← R3, c1 ← R2, c2 ← R1 — a rekordlajstrom balról
   jobbra „R1R2R3", a fagyasztott QASM-okéval AZONOS; ellenőrzés: a 17
   áramkör újraépítése `with_measurements()`-szel bájtra megegyezik a
   fagyasztott QASM-hashekkel).
2. **ÚJ kapu — G8 mérés-kapu (a run() hívás ELŐTT; mind dry-run, mind
   submit úton):** minden payload-áramkör PONTOSAN **3 mérést** tartalmazzon,
   a **c0/c1/c2** clbit-ekre egy-egy; bármely áramkör mérés nélkül (vagy
   nem-3 méréssel) ⇒ **HALT, run() NEM hívható**. A G7 CZ-kapu változatlan
   (a mérés nem érinti a CZ-számot/párokat; 17/17 PASS marad).
3. **Az ERROR-tény a v1.3-ban rögzítve van** (job id, hibakód 1515, adat
   nincs) — a terv, a `submit_manifest_v1.3.json` és a README is utal rá.
   Az ÚJRAKÜLDÉS KÜLÖN tulajdonosi/Control Agent döntés — ez a dokumentum
   NEM ad engedélyt semmilyen beküldésre.

## Mi változott és miért (v1.1 → v1.2; örökül)

1. **A `job_meta.draft.json` initial_layout-ja HIBÁS volt** ([125,117,124,126]).
   A QASM-ok MÁR ROUTOLtak: a prune-olt `q0..q3` = a használt fizikai qubitek
   növekvő sorrendje = **[117,124,125,126]** (a `circuits_manifest.json`
   `used_physical_ids`-jai és a CZ-párok is ezt adják — pl. m+1_k8:
   117-125: 3, 124-125: 44, 125-126: 45). Beküldéskor a
   `[125,117,124,126]` újra-topológiázna: áramkörönként **+3 CZ**
   (m+1_k8: 92 → 95) — vagyis NEM a lefagyasztott áramkör futna.
   **Javítás:** `job_meta.draft_v1.3.json` → `initial_layout: [117,124,125,126]`,
   `optimization_level = 0` (változatlan), `seed_transpiler = 1234` (változatlan).
   A routolt áramkörök, a `build_kuszob.py` (a ROUTING-kori
   `initial_layout = [125,117,124,126]` **helyes** — az a LOGIKAI→FIZIKAI
   megfeleltetés, nem a beküldési layout) és a manifest **NEM változnak**.
2. **Lefagyasztott elemző létrejött**: `submission/kuszob/analyze_kuszob.py`,
   sha256: **`6458a64d616d28436429c06075f0ebdaabc482e1d72d405c3f45ce4871636e3d`**
   (lentebb a hash-kártyán is). A v1.0 §5 (a)–(d) szabálya PONTOSAN,
   egyoldalú 99% Wilson CI-kkal (z = Φ⁻¹(0.99) = 2.3263478740408408),
   fail-closed NaN/hiányzó kar/ shots-eltérés esetén ⇒ **ERVENYTELEN**.
   Az elemző JELEN dokumentummal együtt FAGYASZTOTT: bármely módosítás
   új verzió + új hash + külön commit. (A hash SZÁNDÉKOSAN nem a
   `circuits_manifest.json`-ba került — az a v1.0 fagyasztott fájlja;
   a hash itt, a hash-kártyán és a `job_meta.draft_v1.3.json`-ben él.)
3. **CZ-kapu a `verify_kuszob.py`-be** (build/verify része): minden áramkör
   a QASM-ből számolt CZ-száma és CZ-pár-bontása PONTOSAN egyezzen a
   manifesttel — eltérés ⇒ kilépési kód 1 ⇒ **automatikus HALASZTÁS**.
   2026-11-12 --aer futás: **82/82 kapu PASS** (a 34 CZ-kapu is);
   `verification_last.json` frissítve.
4. **Keverés (shuffle) rögzítve, de TITKOS seeddel — v1.1-es seed ÉRVÉNYTELEN, ÚJ seed:**
   a v1.1-ben publikált seed hash (`6a68d507df95063181a461b988e8b88ae3563a4b766e1c94eb14a5a7ef478f2f`)
   ÉRVÉNYÉT VESZTETTE (a seed-átadás körülményei miatt; mérés nem történt,
   adat nem keletkezett — szabályos, mérés előtti amendment).
   **v1.2 seed hash — ELŐRE publikus:**
   `sha256(utf8(hex(seed))) = 83f43b94f6ab5f75d26ffec94af9dceafdd56ae2a7592a2571a57a89dee4b31c`.
   A nyers seed NINCS a repóban és a v1.2-t előkészítő agent
   munkaterében SEM (a Control Agent generálta és őrzi, out-of-tree, chmod 600);
   beküldéskor/unblindingkor derül ki. Algoritmus (változatlan):
   `ids = sorted(order); rng = random.Random(int(seed_hex, 16)); rng.shuffle(ids)`.
   A `submit_kuszob.py` v1.2-től a várt seed-hash-t MÁR NEM beégetett
   konstansból, hanem a submit-manifestből olvassa; a v1.3-ban ez a
   `submission/kuszob/submit_manifest_v1.3.json` (cross-check: a
   `job_meta.draft_v1.3.json` `shuffle.seed_sha256`-ével);
   ez a dokumentum NEM tartalmazza a v1.3 `submit_kuszob.py` hash-ét —
   **a hash-érvényes hivatkozás a `submit_manifest_v1.3.json`** (l. hash-kártya).
5. **Riport-jelölés (kötelező):** a **ROGZUL** ítélet mellett mindig ki kell
   írni: **„gep-alkalmassagi kapu, tankonyvi varakozas”** — ez NEM
   memória-teszt és nem a Kerék-állítás tesztje.

**Mi NEM változott (v1.3-ban is):** a QASM-ok és a manifest (payload_sha256
`6194ef7adbc74901c57682408b9d421b373c148d67c9389c7de467487dacdb4e` változatlan),
**a seed hash-e (`83f43b94…`, változatlan a v1.2-höz képest)**,
a döntési szabály maga (99%-os küszöbök, nincs többszörös korrekció,
egyetlen elsődleges végpont), a 17 áramkör, shots = 4096, φ_f = π/6, Φ = π/2,
a kar-felépítés, a layout szereposztás (S=125, R1=117, R2=124, R3=126),
és minden v1.0 fagyasztott fájl.

**A v1.0, v1.1 és v1.2 beküldésre NEM használható** (a hibás metadatumok,
ill. a hibakód 1515-öt okozó szkript-hiba miatt). Beküldés KIZÁRÓLAG a
v1.3-as fájlokkal, külön tulajdonosi/Control Agent döntéssel, kötelező
átnézés UTÁN lehetséges; a beküldéskor használandó seed a Control
Agentnél lévő seed (az agent a seed ÉRTÉKÉT SOSEM látja). Az újraküldés
új, külön döntés — az ERROR-job eredménye NEM létezik, semmilyen
következtetést nem hordoz. **Az agent QPU-t SOSEM indít; tokent nem kap,
tokent nem tárol.**

## 1. Határ-null ellenőrzés (a lefagyasztott elemzőön)

2026-11-12 — seedelt, szintetikus tankönyvi-null replay, 4096 shot,
2000 futás próbánként (`analyze_kuszob.py --null-probe 2000`; determinisztikus,
újrajátszással azonos):

| próba | definíció | hamis ROGZUL | elvárás |
|-------|-----------|--------------|---------|
| A (szimmetrikus határ) | P(m+1,k=8) = P(cut,k=8) = 0.5, a többi kar exact referencián | **0/2000 = 0.00%** | ≤ 1.5% ✓ |
| B (differenciál-legkedvezőbb határ) | P(m+1,k=8) = 0.5, cut = exact 0.2460 | **17/2000 = 0.85%** | ≤ 1.5% ✓ |

Megjegyzés: A próbában a `(d)(ii)` pontbecslés-összevetés miatt a 2000
minta 994-szer NULL, 1006-szor SZÉTESŐ ítéletet kapott — ROGZUL egyszer sem.
B-ben 1983 NULL, 17 ROGZUL (≈0.85%; egyezik a binomiális-szignifikancia
várakozással, p ≈ 0.9%). Minden eredmény SZIMULÁCIÓ — nem HARDWARE.

## 2. Fagyasztott döntési szabály (PONTOSAN — a v1.0 §5 (a)–(d) formalizálása)

Egyoldalú 99% Wilson CI (z = Φ⁻¹(0.99) = 2.3263478740408408):

    den    = 1 + z²/n
    center = p + z²/(2n)
    fél    = z·sqrt( p(1−p)/n + z²/(4n²) )
    L(p,n) = (center − fél)/den      (alsó, egyoldalú)
    U(p,n) = (center + fél)/den      (felső, egyoldalú)

Precedencia (fail-closed sorrendben, FAGYASZTVA):
`ERVENYTELEN → HALASZTAS (a) → SZETESO (d) → ROGZUL (b) → NULL (c)`

- **ERVENYTELEN** (fail-closed): a 17 áramkör bármelyikének hiánya, nulla
  összegű/ nem egész/ negatív/ NaN számlálója, illetve — ha a `shots`
  mező adott — az áramkörök összlövés-számának ettől való ELTÉRÉSE ⇒
  ítélet = ERVENYTELEN; fizikai állítás nem készül.
- **(a) Gép-egészség — ELŐKAPU (pontbecslések):** P(m+1,k=0) ≥ 0.70 ÉS a
  három k=0 kar (m+1, m−1, m0) páronkénti spread ≤ 0.10. Bukás ⇒ ítélet =
  **HALASZTAS** (automatikus; nincs elsődleges döntés; lásd v1.0 §7).
- **(d) SZÉTESŐ-vezérlők** (ha az (a) átment; bármelyik kiváltja):
  (i) PC NEM mutatható ki ⇔ ¬[ L(P(m+1,k=0)) − U(P(pc,k=0)) > 0 ] ⇒ SZÉTESŐ;
  (ii) P(cut,k=8) ≥ P(m+1,k=8) (pontbecslések) ⇒ SZÉTESŐ.
  Bármely kivált ⇒ ítélet = **SZETESO**; csomag HALASZTOTT + modell-audit;
  fizikai állítás NEM készül.
- **(b) ELSŐDLEGES (ROGZUL-ág):** L(P(m+1,k=8)) ≥ 0.5 ÉS
  L(P(m+1,k=8)) − U(P(cut,k=8)) > 0 (Wilson-differenciál, SPAM-robust) ⇒
  ítélet = **ROGZUL**.
- **(c)** egyébként ⇒ ítélet = **NULL** — NULL-t NULL-ként jelentjük.
- A v1.0 §5(d) „kalibráció/elemző használhatatlan” feltétele az
  ERVENYTELEN-szabályba lett beolvasztva (fail-closed, szigorúbb):
  használhatatlan BEMENET nem lesz SZETESO, hanem ERVENYTELEN.
- **Jelölés:** ROGZUL mellett kötelező: „gep-alkalmassagi kapu,
  tankonyvi varakozas”; nem Kerék-állítás; Aer-előrejelzés a döntésbe
  soha nem kerül bele — a VALÓDI számlálók döntenek (ha mérés lesz).

## 3. Számláló-JSON formátum (az elemző bemenete)

    {
      "shots": 4096,
      "counts": { "<17 áramkör-id>": { "000": <P_return darabszám>, ... } }
    }

`P_return(id) = counts[id]["000"] / sum(counts[id].values())` — a
mérés-huzalozás miatt a `000` kulcs a jel (a mérés R3→c0, R2→c1, R1→c2;
a rekordlajstrom balról jobbra „R1R2R3”). Kilépési kódok: 0 = ítélet
(ROGZUL/NULL/SZETESO/HALASZTAS) · 3 = ERVENYTELEN · 2 = használati/IO hiba ·
`--null-probe N`: 0 = PASS, 1 = FAIL.

## 4. CZ-kapu (a `verify_kuszob.py` 4b szakasza; a build/verify része)

Minden áramkörre: a QASM-ből kinyert `cz` utasítások darabszáma és
párbontása (sorrendi `q[i],q[j]` → fizikai `used_physical_ids`-en keresztül,
növekvő pár-kulcsok) PONTOSAN egyezzen a `circuits_manifest.json`
`n_cz` / `cz_pairs` mezőjével. Pl. m+1_k8: **92 CZ; 117-125: 3, 124-125: 44,
125-126: 45**. Bármilyen eltérés ⇒ `[FAIL]` ⇒ kilépési kód 1 ⇒
**automatikus HALASZTÁS** (a v1.0 §7 1. trigger).

## 5. Keverés (shuffle) — rögzített, de titkos seed (v1.2 amendment; változatlan a v1.3-ban)

- A v1.1-ben regisztrált seed ÉRVÉNYTELEN (a seed-átadás körülményei;
  mérés nem történt — adat nem keletkezett).
- ÚJ seed: 256-bit, 2026-11-12-én generálva (Control Agent); **a repó SEHOL nem tartalmazza,
  és az előkészítő agent munkaterében SINCSEN** (a tulajdonos/Control Agent őrzi, out-of-tree fájl, chmod 600).
- Előre publikus hash (v1.2): **`83f43b94f6ab5f75d26ffec94af9dceafdd56ae2a7592a2571a57a89dee4b31c`**
  (= sha256 az utf8(hex(seed)) bájtjairól, hex).
- A v1.1-es hash (`6a68d507df95063181a461b988e8b88ae3563a4b766e1c94eb14a5a7ef478f2f`)
  ÉRVÉNYTELEN — semmilyen kapu nem fogadja el.
- Keverés algoritmusa (a beküldéskor a tulajdonos futtatja):
  `ids = sorted(order); rng = random.Random(int(seed_hex, 16)); rng.shuffle(ids)`
- Unblinding: az eredmények beérkezése után a seed közzétehető; bárki
  visszaellenőrizheti a hash-egyezést és a kevert sorrend reprodukcióját.
- A `job_meta.draft_v1.3.json` csak a hash-t és az algoritmust rögzíti;
  `shuffle_seed: null` (szándékosan).

## 6. Mit NEM állít egy ilyen mérés

Nem bizonyítja és nem cáfolja a Kerék-állítást (W1/W2/W3); nem
sötétállapot-teszt; csak: ezen a négyesen, ilyen routinggal, ilyen
időskálán mérhető-e a rövidtávú Peierls-fáziskoherencia. Az Aer-előrejelzés
NEM döntési alap; a mért számlálók döntenek (ha mérés lesz). Aer/Szimuláció
SOHA nem kap „HARDWARE” címkét; NULL-t NULL-ként jelentünk.

## 7. Sorrend (előírva) és tilalmak

1. A csomag v1.3 (ez a dokumentum + `submission/kuszob/` v1.3 fájlok) elkészült;
2. **agent-oldali** ellenőrzés: `verify_kuszob.py --aer` — **82/82 PASS**
   (2026-11-12; `verification_last.json`);
3. **TULAJDONOS / Control Agent felülvizsgálat — KÖTELEZŐ**, mielőtt bármilyen
   beküldésről szó lehet (a v1.0 §8 szerinti sorrend érvényben marad);
4. külön, explicit tulajdonosi döntés: beküldés VAGY halasztás.
   **Az agent a beküldést SOSEM végzi el; tokent nem kap, tokent nem tárol.**

- A teljes Kerék-QPU-job továbbra is **TILOS** ezen a négyesen; a
  küszöb-job kimenete a Kerék fagyasztott verdiktjeit NEM írja át.
- Fagyasztott fájlt tilos felülírni; minden változtatás új verzió,
  új hash, külön commit.

## 8. Hash-kártya (v1.3, 2026-11-12)

| fájl | sha256 |
|------|--------|
| `submission/kuszob/analyze_kuszob.py` (FAGYASZTOTT) | `6458a64d616d28436429c06075f0ebdaabc482e1d72d405c3f45ce4871636e3d` |
| `submission/kuszob/job_meta.draft_v1.3.json` | `3e86195a9fad82b7b4d4c05c8a62e158c6a4b72ae32191bf432720a4492e662f` |
| — v1.2 érintetlen (történeti): `job_meta.draft_v1.2.json` | `b78e5beb273a4c0f5715c3132cf70aba13480cb4e815718be83547857a8feee2` |
| — v1.2 érintetlen: `PLAN_KUSZOB_v1.2.md` | `a1c58739c1ddfacae72b765b3890ae71545dc41f9f92636272bd375b67c7cc0b` |
| — v1.1 érintetlen (történeti): `job_meta.draft_v1.1.json` | `0f6c66298e488ef08305907167f2ef21dadf4e41c93613c5180f351f2d4dedc8` |
| — v1.1 érintetlen: `PLAN_KUSZOB_v1.1.md` | `dfba74ff46b7f08fd0920428e43e603bff8bb0f37adc9bd723e865324aba9044` |
| — v1.1 érintetlen: `submit_manifest_v1.1.json` | `8f579d581ef90174972d975a50e0501873e071ed5df57e870e7ea58c60f75cba` |
| `submission/kuszob/submit_manifest_v1.3.json` (az ÉRVÉNYES hivatkozás a v1.3 `submit_kuszob.py`-ra) | `961fccd9ab9ea382c6db43bb5345f264e5b15abf9e3827c244c712c0122ceb05` |
| — v1.2 érintetlen: `submit_manifest_v1.2.json` | `b27cce45076156a47054a28f20d0b3193fefdc505ef09ca21c32bc2ac9971d39` |
| `preregistration/PLAN_KUSZOB_v1.3.md` (ez a fájl) | (a commit hash rögzíti) |
| `submission/kuszob/verify_kuszob.py` (nem fagyasztott; a v1.1 CZ-kaput tartalmazza) | `e44c6bbfb51f5a78fd5a39f44a94886a3d703560e1e991e7042d983acb024bf5` |
| — v1.0 érintetlen, hash-kártyán: `PLAN_KUSZOB_v1.0.md` | `f865faed91b6ba3fd1b7cdae1629be8f4fbfbdf6ce405c67205783aea0e49cc8` |
| — v1.0 érintetlen: `job_meta.draft.json` | `f425cd9409fb8ff527f6a8747e68f98dcd990be3032fc7d2286279439a1cbbef` |
| — v1.0 érintetlen: `circuits_manifest.json` (payload `6194ef7a…`) | `94048f35ab7012f8027170adbc17b7f783e8b738abb1b17f7113d299cdcaf962` |
| shuffle seed sha256 (publish-before-unblind; v1.1 érvénytelenítve) | `83f43b94f6ab5f75d26ffec94af9dceafdd56ae2a7592a2571a57a89dee4b31c` |

Készítette: agent (Arena) — előkészítés; NEM felülvizsgálat. QPU-beküldés
NEM történt és nem is fog az agent részéről; a beküldés a tulajdonos/
Control Agent külön döntése az átnézés után.
