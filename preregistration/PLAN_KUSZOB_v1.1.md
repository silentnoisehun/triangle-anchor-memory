# PLAN_KUSZOB v1.1 — AMENDED (felülírja a v1.0-t a beküldés útját illetően; a v1.0 byte-ra változatlan)

**EZ A FÁJL AMENDMENT.** A `preregistration/PLAN_KUSZOB_v1.0.md`
(`f865faed91b6ba3fd1b7cdae1629be8f4fbfbdf6ce405c67205783aea0e49cc8`)
byte-ra változatlanul megmarad a történet részeként — csendben átírni TILOS.
A v1.1 a v1.0 dokumentumait és metadátumait FELÜLÍRJA (superseded) a
beküldés útján: a döntési szabály (v1.0 §5 (a)–(d)) MAGA NEM VÁLTOZOTT —
csak formalizálva, lefagyasztva és hash-elve lett.
**Dátum:** 2026-11-12 · **Előzmény:** Maya beküldés előtti átnézése (2026-11-12 09:05 UTC) · **Repo:** triangle-anchor-memory

## Mi változott és miért (v1.0 → v1.1)

1. **A `job_meta.draft.json` initial_layout-ja HIBÁS volt** ([125,117,124,126]).
   A QASM-ok MÁR ROUTOLtak: a prune-olt `q0..q3` = a használt fizikai qubitek
   növekvő sorrendje = **[117,124,125,126]** (a `circuits_manifest.json`
   `used_physical_ids`-jai és a CZ-párok is ezt adják — pl. m+1_k8:
   117-125: 3, 124-125: 44, 125-126: 45). Beküldéskor a
   `[125,117,124,126]` újra-topológiázna: áramkörönként **+3 CZ**
   (m+1_k8: 92 → 95) — vagyis NEM a lefagyasztott áramkör futna.
   **Javítás:** `job_meta.draft_v1.1.json` → `initial_layout: [117,124,125,126]`,
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
   a hash itt, a hash-kártyán és a `job_meta.draft_v1.1.json`-ben él.)
3. **CZ-kapu a `verify_kuszob.py`-be** (build/verify része): minden áramkör
   a QASM-ből számolt CZ-száma és CZ-pár-bontása PONTOSAN egyezzen a
   manifesttel — eltérés ⇒ kilépési kód 1 ⇒ **automatikus HALASZTÁS**.
   2026-11-12 --aer futás: **82/82 kapu PASS** (a 34 CZ-kapu is);
   `verification_last.json` frissítve.
4. **Keverés (shuffle) rögzítve, de TITKOS seeddel**: a seed hash-e ELŐRE
   publikus — `sha256(utf8(hex(seed))) = 6a68d507df95063181a461b988e8b88ae3563a4b766e1c94eb14a5a7ef478f2f`.
   A nyers seed NINCS a repóban (a tulajdonos/Control Agent őrzi,
   out-of-tree); beküldéskor/unblindingkor derül ki. Algoritmus:
   `ids = sorted(order); rng = random.Random(int(seed_hex, 16)); rng.shuffle(ids)`.
5. **Riport-jelölés (kötelező):** a **ROGZUL** ítélet mellett mindig ki kell
   írni: **„gep-alkalmassagi kapu, tankonyvi varakozas”** — ez NEM
   memória-teszt és nem a Kerék-állítás tesztje.

**Mi NEM változott:** a QASM-ok és a manifest (payload_sha256
`6194ef7adbc74901c57682408b9d421b373c148d67c9389c7de467487dacdb4e` változatlan),
a döntési szabály maga (99%-os küszöbök, nincs többszörös korrekció,
egyetlen elsődleges végpont), a 17 áramkör, shots = 4096, φ_f = π/6, Φ = π/2,
a kar-felépítés, a layout szereposztás (S=125, R1=117, R2=124, R3=126),
és minden v1.0 fagyasztott fájl.

**A v1.0 beküldésre NEM használható** (a hibás metadatumok miatt);
beküldés KIZÁRÓLAG a v1.1-es fájlokkal, külön tulajdonosi/Control Agent
döntéssel, kötelező átnézés UTÁN lehetséges. **Az agent QPU-t SOSEM indít;
tokent nem kap, tokent nem tárol.**

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

## 5. Keverés (shuffle) — rögzített, de titkos seed

- Seed: 256-bit, 2026-11-12-én generálva; **a repó SEHOL nem tartalmazza**
  (a tulajdonos/Control Agent őrzi, out-of-tree fájl).
- Előre publikus hash: **`6a68d507df95063181a461b988e8b88ae3563a4b766e1c94eb14a5a7ef478f2f`**
  (= sha256 az utf8(hex(seed)) bájtjairól, hex).
- Keverés algoritmusa (a beküldéskor a tulajdonos futtatja):
  `ids = sorted(order); rng = random.Random(int(seed_hex, 16)); rng.shuffle(ids)`
- Unblinding: az eredmények beérkezése után a seed közzétehető; bárki
  visszaellenőrizheti a hash-egyezést és a kevert sorrend reprodukcióját.
- A `job_meta.draft_v1.1.json` csak a hash-t és az algoritmust rögzíti;
  `shuffle_seed: null` (szándékosan).

## 6. Mit NEM állít egy ilyen mérés

Nem bizonyítja és nem cáfolja a Kerék-állítást (W1/W2/W3); nem
sötétállapot-teszt; csak: ezen a négyesen, ilyen routinggal, ilyen
időskálán mérhető-e a rövidtávú Peierls-fáziskoherencia. Az Aer-előrejelzés
NEM döntési alap; a mért számlálók döntenek (ha mérés lesz). Aer/Szimuláció
SOHA nem kap „HARDWARE” címkét; NULL-t NULL-ként jelentünk.

## 7. Sorrend (előírva) és tilalmak

1. A csomag v1.1 (ez a dokumentum + `submission/kuszob/` v1.1 fájlok) elkészült;
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

## 8. Hash-kártya (v1.1, 2026-11-12)

| fájl | sha256 |
|------|--------|
| `submission/kuszob/analyze_kuszob.py` (FAGYASZTOTT) | `6458a64d616d28436429c06075f0ebdaabc482e1d72d405c3f45ce4871636e3d` |
| `submission/kuszob/job_meta.draft_v1.1.json` | `0f6c66298e488ef08305907167f2ef21dadf4e41c93613c5180f351f2d4dedc8` |
| `preregistration/PLAN_KUSZOB_v1.1.md` (ez a fájl) | (a commit hash rögzíti) |
| `submission/kuszob/verify_kuszob.py` (nem fagyasztott; a v1.1 CZ-kaput tartalmazza) | `e44c6bbfb51f5a78fd5a39f44a94886a3d703560e1e991e7042d983acb024bf5` |
| — v1.0 érintetlen, hash-kártyán: `PLAN_KUSZOB_v1.0.md` | `f865faed91b6ba3fd1b7cdae1629be8f4fbfbdf6ce405c67205783aea0e49cc8` |
| — v1.0 érintetlen: `job_meta.draft.json` | `f425cd9409fb8ff527f6a8747e68f98dcd990be3032fc7d2286279439a1cbbef` |
| — v1.0 érintetlen: `circuits_manifest.json` (payload `6194ef7a…`) | `94048f35ab7012f8027170adbc17b7f783e8b738abb1b17f7113d299cdcaf962` |
| shuffle seed sha256 (publish-before-unblind) | `6a68d507df95063181a461b988e8b88ae3563a4b766e1c94eb14a5a7ef478f2f` |

Készítette: agent (Arena) — előkészítés; NEM felülvizsgálat. QPU-beküldés
NEM történt és nem is fog az agent részéről; a beküldés a tulajdonos/
Control Agent külön döntése az átnézés után.
