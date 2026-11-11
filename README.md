# triangle-anchor-memory

**Háromszög-horgony memória** — preregisztrált kvantumkísérlet IBM Heron-chipre:
egy központi qubit (S) három,
rögzített kezdőállapotú szomszédos horgonyhoz (A1, A2, A3) részleges
SWAP-csatolásokkal („gumikkal") kötve — a kérdés az, hogy ezzel a
geometriával a S-be írt gerjesztés **visszaáramlása** erősödik-e és
gyorsul-e. A teljes, kötelező érvényű tervet lásd:
[`preregistration/PLAN_v1.0.md`](preregistration/PLAN_v1.0.md).

A kísérlettervet **Máté Róbert** ötlete alapján a Control Agent szigorította;
futtatás előtt rögzítve, döntési szabályai utólag nem módosíthatók.

## Állapot: 0. fázis készül

- [x] Repo-váz (ez a fájl, `.gitignore`, `data/` megjelölve nem-ignoroltnak)
- [x] `preregistration/PLAN_v1.0.md` — a terv szó szerinti másolata
- [x] `src/` csomag: `config`, `circuits`, `sim`, `analysis`, `run` (beküldő), `freeze` (0. fázis fagyasztó)
- [x] `dryrun.py` — QPU nélkül minden végigfuttatható
- [ ] 0. fázis szimuláció (zajtalan + zajos, MINTA zajparaméterekkel) — a végrehajtás után frissítve
- [ ] `preregistration/frozen_params.json` — φ, K, csúcs-keresési ablakok, várt görbék, hash-el lezárva
- [ ] QPU-futtatás (1. fázis) — **NEM az agent dolga**: a Control Agent végzi audit után

**A QPU-futtatás még nem történt meg.** A token soha nem kerül fájlba; a
`src/run.py` a tokent kizárólag az `IBM_QUANTUM_TOKEN` környezeti változóból
olvassa. A `data/` mappa szándékosan NINCS `.gitignore`-ban.

## Gyors indítás (0. fázis, QPU nélkül)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m src.freeze     # EGYSZER: fagyasztás + hash (preregistration/)
.venv/bin/python dryrun.py         # elvárt: zajtalan → TEXTBOOK-MEGEROSITVE, kontroll → NULL
```

## Repo-váz (terv 7. fejezete szerint)

```
preregistration/   a terv + a 0. fázis utáni befagyasztott paraméterek (hash-el)
src/config.py      φ, K, karok, referencia-döntési értékek, MINTA zajparaméterek
src/circuits.py    kar-építők + kalibrációs áramkörök (T1, Hahn-T2, kiolvasás, φ_eff)
src/sim.py         zajtalan + zajos (T1/T2/ε) szimuláció; várt görbék; pozitív kontroll
src/analysis.py    D(k), BLP, csúcskeresés, bootstrap CI, ítélet — a döntési szabályt
                   a preregistration/frozen_params.json-ból olvassa (hash-ellenőrzéssel)
src/run.py         beküldő — tokent CSAK környezeti változóból olvas (audit előtt nem futtatható)
src/freeze.py      a 0. fázis fagyasztó-eszköze (egyszer fut le)
dryrun.py          QPU nélkül minden végigfuttat
data/              job_meta.json, raw_counts.json (NEM gitignore-olt!)
```

## Sémák

A leendő chip-pillanatkép (`snapshot.json`) sémája a `src/config.py`-ben
(`SNAPSHOT_SCHEMA_DOC`) rögzítve; a zajmodell egy az egyben behelyettesíthető
(a `src/sim.py: load_noise_snapshot(path=...)` path-argumentummal). A 0. fázis
zajos eredményei **MINTA paraméterekkel** készülnek és **nem** hardware-eredmények.

A `data/raw_counts.json` várt sémáját a [`data/README.md`](data/README.md) rögzíti.

## Szabályok (megszegésük = a feladat elbukott)

1. QPU-futtatást senki nem indít; tokent senki nem ír fájlba.
2. A döntési szabály a preregisztrált fájlból olvasódik; utólag nem módosítható.
3. `data/` sosem kerül `.gitignore`-ba.
4. Szimulációs eredmény soha nem kap „HARDWARE" címkét.
5. A 0. fázis eredményéig (φ, K, ablakok, görbék) a `frozen_params.json` lezárja a paramétereket.
