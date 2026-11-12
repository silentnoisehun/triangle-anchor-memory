# Küszöb-job csomag — ELŐKÉSZÍTVE, NEM BEKÜLDVE (v1.1)

> **v1.1 (2026-11-12, Maya beküldés előtti átnézése nyomán):** a v1.0
> `job_meta.draft.json` initial_layout-ja HIBÁS volt ([125,117,124,126] —
> a QASM-ok routoltak, q0..q3 = fizikai [117,124,125,126]; a v1.0 layouttal
> áramkörönként +3 CZ, pl. m+1_k8: 92 → 95). Javítva:
> [`job_meta.draft_v1.1.json`](job_meta.draft_v1.1.json) (`initial_layout =
> [117,124,125,126]`, `optimization_level = 0`). Új: lefagyasztott elemző
> ([`analyze_kuszob.py`](analyze_kuszob.py), sha256 a PLAN-ban) + CZ-kapu a
> verify-ben (minden áramkör CZ-száma/párjai pontosan a manifesttel;
> eltérés ⇒ HALASZTÁS). A döntési szabály maga NEM változott (99% Wilson,
> (a)–(d)); a határ-null próba: hamis ROGZUL 0/2000 (A) és 17/2000 = 0.85% (B)
> ≤ 1.5% ✓. **A v1.0 fájljai byte-ra változatlanok (történeti).**

> **Állapot: ELŐKÉSZÍTVE — NEM BEKÜLDVE.**
> A Kerék-menet W3 = SZÉTESŐ ágán a teljes QPU-job NEM tervezhető; ez a
> csomag az egyetlen szóba jövő — és a legolcsóbb — következő lépés
> (Ring-Ramsey fáziszár-teszt, 17 áramkör, 69 632 shot, 1 job-darab).
> **A beküldést az agent SOSEM végzi el.** A beküldésről (vagy a halasztásról)
> külön, explicit tulajdonosi/Control Agent döntés szól, a kötelező
> felülvizsgálat UTÁN (PLAN_KUSZOB_v1.1 §7; a v1.0 §8 eljárása változatlan).
> Ha az agent-oldali ellenőrzés bármely kapuja bukna, a csomag státusza
> automatikusan **HALASZTOTT — a kerek ezen a négyesen vár**.

Terv és döntési szabály (v1.1, AMENDED): [`preregistration/PLAN_KUSZOB_v1.1.md`](../../preregistration/PLAN_KUSZOB_v1.1.md)
(a v1.0: [`PLAN_KUSZOB_v1.0.md`](../../preregistration/PLAN_KUSZOB_v1.0.md) — történeti, beküldésre NEM használható)

## Mit tartalmaz

| fájl | szerep |
|------|--------|
| `plan` fent | a mérés, a kontrollok és a döntési szabály előre rögzítve |
| `build_kuszob.py` | QPU-mentes áramkör-építő: prep → Peierls-körök → prep† echo; routolt (opt=0) transzpiláció, prune, mérés-bekötés; manifest + gate_table generálás |
| `circuits/*.qasm` | a 17 TÉNYLEGES routolt áramkör (Qiskit-dialektusú QASM 2.0: `cz/rz/sx/x` — auditra; beküldéshez a Python-építő az autoritatív) |
| `circuits_manifest.json` | áramkörönként: id, kar, k, QASM-SHA256, kapuszámok, pár-bontású CZ-tábla, becsült 2Q-hiba, mélység, t_est, tárolás-hányados, **zajtalan exact referencia** (`p000_exact`), payload-SHA256 |
| `gate_table.json` | páronként a CZ-darabszámok és várható hibák (a W3 számvitellel azonos) |
| `job_meta.draft.json` | v1.0 job_meta tervezet — **HIBÁS initial_layout; csak történeti, beküldésre TILOS** |
| `job_meta.draft_v1.1.json` | **v1.1 tervezet — ez használható (átnézés után)**: `initial_layout: [117,124,125,126]`, `optimization_level: 0`, titkos shuffle seed előre publikus hash-e, a lefagyasztott elemző hash-e, `job_ids: []` |
| `analyze_kuszob.py` | **LEFAGYASZTOTT elemző (v1.1)** — PLAN §5 (a)–(d) Wilson 99%, fail-closed (ERVENYTELEN), kötelező ROGZUL-jelölés; `--null-probe 2000` |
| `verify_kuszob.py` | agent-oldali ellenőrző (NEM független!); v1.1: **CZ-kapu** (minden áramkör CZ-száma/párjai pontosan a manifesttel; eltérés ⇒ kilépési kód 1 ⇒ HALASZTÁS); `--aer` kapcsolóval zaj-próbával |
| `verification_last.json` | az utolsó agent-oldali ellenőrzés teljes rekordja (2026-11-12, --aer: **82/82 PASS**) |

## A protokoll egy sorban

`prep(m) → k kör Peierls-gyűrű (φ_f = π/6; Φ = π/2) → prep†`, és
**P_return = P(R1R2R3 = 000)** — az echo a vákuumba ad vissza. A populáció-only
látás erre a kérdésre NEM lenne elég (fázisérzékeny mennyiség);
az S qubit csak kötőelem (nem mérjük); nincs 5 µs kitartás; nincsenek
identitás-kitöltők (ez újísérlet, nem a Kerék kaputilus-illesztése).

## Karok (17 áramkör)

| kar | k ellenpontok | miért |
|-----|---------------|-------|
| `m+1`, `m−1`, `m0` | 0, 2, 4, 8 | a fáziszár-jel (mindhárom keringési sajátállapot) |
| `pc` (RZ(π/3) a prep után) | 0, 4 | pozitív kontroll — zajtalan **7/9** (analitikus); az elemzőnek kimutatnia kell |
| `cut` (R3–R1 gyűrű-él → identitás) | 2, 4, 8 | negatív kontroll — nyílt gyűrű; k≥4-nél elmarad a zárttól |

Layout (a csillag-/Kerék-menet fagyasztott layoutja): **S=125, R1=117, R2=124, R3=126**.
**Beküldési `initial_layout` (v1.1): `[117,124,125,126]`** — a routolt QASM-ok q0..q3-ának fizikai
sorrendje (a `used_physical_ids` növekvő sorrendje); a routing-kori
`initial_layout = [125,117,124,126]` (build_kuszob.py) a LOGIKAI→FIZIKAI
megfeleltetés, és változatlan marad.
Routing: a valós `data/snapshot.json` coupling-map, `opt_level = 0`, `seed_transpiler = 1234`,
basis `cz/rz/sx/x/delay/id`.

## Költség- és határértékek (mért, nem becsült)

| ellenpont | CZ | várható 2Q-hiba | mélység | t_est |
|-----------|-----|-----------------|---------|-------|
| k=0 (prep+echo) | 11 | 0.017 | ~54 | 2.1 µs |
| k=2 | 29 | 0.047 | ~134 | 5.5 µs |
| k=4 | 50 | 0.081 | ~221 | 9.2 µs |
| k=8 | **92** | **0.126** | ~392 | **16.7 µs** |

- A kapuhiba-költséglet a W3-küszöb (**0.5**) alatt van, **4× tartalékkal** — vagyis a
  kapu-költséglet ezen az újísérleten NEM bukik el; a W3 bukása a teljes
  Kerék-áramkör 700-CZ-s terhére szólt, nem a gyűrű-elverés önmagában vett
  létére. (Pontosan ezért értelmes a küszöb-job, és pontosan ezért nem pótlékokul
  szolgál a Kerék számára.)
- Tárolási padló: a legrosszabb qubit (A3, T1 = 256.9 µs) esetén ≥ **0.937** — bőven
  a W3-padló felett.
- Aer-zaj előrejelzés (teljes zaj-próba): P(m+1, k=8) ≈ **0.61 raw**, pc k=0 ≈ 0.70,
  cut k=8 ≈ 0.18 — a gép-egészség és a két kontroll iránya mind helyes.

## Döntési szabály (röviden — a teljes, lefagyasztva: PLAN_KUSZOB_v1.1 §2; v1.0 §5)

A ROGZUL ítélet kötelező jelölése: **„gep-alkalmassagi kapu, tankonyvi varakozas”** — ez nem memória-teszt.

1. **Gép-egészség (előkapu):** P(m+1, k=0) ≥ 0.70 és a három kar k=0-értéke egymástól ≤ 0.10-nel tér el. Bukás ⇒ **automatikus HALASZTÁS**.
2. **Elsődleges (ROGZUL-ág):** P(m+1, k=8) egyoldalú 99% CI alsó határa ≥ 0.5 **ÉS** P(m+1,k=8) − P(cut,k=8) egyoldalú 99% CI > 0.
3. **NULL:** (2) nem teljesül — fáziszár nem mutatható ki ezen a négyesen/routingon.
4. **SZÉTESŐ:** PC nem mutatható ki, vagy cut ≥ m+1 k=8, vagy használhatatlan kalibráció ⇒ **automatikus HALASZTÁS** + modell-audit; fizikai állítás NEM készül.

## Ellenőrzés (agent-oldali; NEM a független felülvizsgálat)

2026-11-12 — `.venv/bin/python submission/kuszob/verify_kuszob.py --aer` (v1.1, CZ-kapuval):
**ÖSSZESÍTÉS: PASS (82/82 kapu, 3 Aer-próba is PASS; a 34 CZ-kapu mind PASS)** —
lásd `verification_last.json`. (A v1.0-ás, CZ-kapu nélküli futás: PASS 48/48, 2026-11-11.)
Ellenőrzött: minden QASM-hash; **determinisztikus újraépítés** (a seed-ek fixek —
minden áramkör byte-azonosan reprodukálódik); Statevector-exact referencia
(k=0 → 1.0; pc → 7/9; cut k=8 → 0.246 ≪ m+1 k=8 → 0.838); CZ-párok a három
snapshot-élen; tárolás ≥ 0.937; **a snapshot SHA-256 egyezik a csillag
`data/job_meta.json` snapshot_sha256-jával** (2acfda2e…); **a Kerék-fájl
(`frozen_wheel_params.json`) hash-integritása érintetlen** (52f84b c6…).

## Amit a TULAJDONOSNAK / Control Agentnek kell tennie a beküldés ELŐTT

1. Átnézni ezt a csomagot és a PLAN_KUSZOB_v1.1-et (fogalmak, küszöbök, kontrollok);
2. ellenőrizni a `snapshot_sha256`-t és a backend-tokent a SZOKÁSOS módon (a repo
   szabályai szerint; az agent tokent nem kezel);
3. futtatni saját gépen a `verify_kuszob.py --aer`-t — ha nem PASS, **HALASZTÁS**;
4. döntést hozni: **beküldés** (record-first: a beadott-állapot commitja megelőzi
   az eredményeket; NULL is record-first) **vagy halasztás**;
5. beküldéskor a `job_meta.draft_v1.1.json` kitöltése (`job_ids`, `submitted_at`,
   valódi backend-normalizált `payload_sha256`; a keveréshez a titkos seed —
   a repóban csak a sha256 hash-e szerepel: `6a68d507…`; algoritmus és
   unblinding: PLAN_KUSZOB_v1.1 §5) —
   ez a tulajdonos művelete, nem az agenté.

**Ne felejtsük: ezen a négyesen a teljes Kerék-QPU-job továbbra is TILOS.
A küszöb-job kimenete nem írja át a Kerék fagyasztott verdiktjeit.**
