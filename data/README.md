# data/ — mérési adatok (SOHA nem kerülnek .gitignore-ba!)

Ez a mappa a QPU-futtatás kimeneteit fogadja. A 0. fázis (szimuláció) során
NEM keletkezik itt adat; a fájlformátumok mégis előre rögzítve vannak.

## Várható fájlok (az 1. fázis után, a Control Agent gyártja)

- **snapshot.json** — a backend-pillanatkép a job beküldésének pillanatában
  (T1/T2/ε mind a 4 érintett qubitre, `dt_s`, teljes `coupling_map`, 2Q-párhibák,
  kapuidők, backend-név, kiválasztási rangsor). A `src/run.py` a job indítása
  ELŐTT írja, és a `sim.validate_snapshot()`-on megy át — egy az egyben
  behelyettesíthető a zajmodellbe (`src/sim.py: load_noise_snapshot`).
- **job_meta.json** — a beküldés pillanatában jön létre (QPU-job indításakor,
  a lekérdezéstől külön). Tartalma pl.: `job_id`, `backend`, `channel`
  (`ibm_quantum_platform`), `submitted_at` (ISO-8601), `shots`, `circuit_count`
  (kalibráció + karok), `calibration_count`, `layout`, `selection`,
  `shuffle_seed`, a körök sorrendje és a payload SHA-256-ja. A beküldés után
  SOHA nem írandó újra.
- **raw_counts.json** — a nyers mérési eredmények, betétszámokkal.
  Formátum: `{ "meta": {...}, "shots": int, "population": {arm: {init: {k: counts}}},
  "coherence": {arm: {"+": {k: counts}}}, "calibration": {circuit_id: counts} }`,
  ahol a `k` a string-kulcs, a `counts` kulcsai bitstringek (qiskit-formátum,
  a jobb szélső bit a c0/S qubit). A nyers fájlt a `fetch_raw_counts()` menti,
  és a hash-t **raw_counts.sha256**-ba írja a mentés után azonnal.

## Szabályok

1. A `data/` tartalma NEM törölhető és NEM módosítható utólag — csak új fájlok
   adhatók hozzá.
2. A QPU-futtatást a Control Agent végzi a tulajdonos rövid életű tokenjével;
   a token SEMMILYEN formában nem kerülhet ide.
3. A döntési szabály a `preregistration/frozen_params.json`-ból olvasandó
   (és a hozzá tartozó `frozen_params.sha256`-nal ellenőrizendő), nem a
   kódba égetve.
