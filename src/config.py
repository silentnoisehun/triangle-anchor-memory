"""Központi konfiguráció — triangle-anchor-memory, 0. fázis (szimuláció).

FONTOS SZABÁLYOK (a preregisztrált terv 7. pontjából):
- A döntési küszöbök (P1/P2/P3, bootstrap, CI-szint, csúcs-keresési ablakok)
  NEM innen élnek a futtatás során: a preregisztrált
  ``preregistration/frozen_params_v1.2.json``-ból olvasandók (ld. src/analysis.py),
  integritását ``preregistration/frozen_params_v1.2.sha256`` ellenőrzi.
  (A v1.0/v1.1 most superseded — a v1.2 AMENDED: 99% CI + Holm.)
  Az itt található DECISION_* értékek CSAK referencia-másolatok a terv 4. fejezetéből.
- A ``SNAPSHOT_SAMPLE`` alábbi zajparaméterei DOKUMENTÁLT MINTAÉRTÉKEK,
  NEM a Heron chip mért pillanatképei. A chip-pillanatkép (snapshot.json) később,
  a Control Agent jóvoltából készül; az ``src/sim.py:load_noise_snapshot`` szó
  szerint ugyanazt a sémát várja, mint ez a minta, így a snapshot.json egy az
  egyben behelyettesíthető (path-argumentummal, kódmódosítás nélkül).
- Token SOHA nem szerepelhet ebben a fájlban; a beküldő (src/run.py) a tokent
  kizárólag az IBM_QUANTUM_TOKEN környezeti változóból olvassa.
"""
from __future__ import annotations

import math

# ---------------------------------------------------------------------------
# Fizikai egység- és időkonstansok (0. fázis, a terv 3.2 pontjához)
# ---------------------------------------------------------------------------
PHI = math.pi / 16  # részleges SWAP (PSWAP) szög / lépés / S–Ai pár
K = 32              # lépésszám; a futtatott körök k = 0..K
# A 3.2 pont szerint: φ és K a 0. fázisból, futtatás előtt rögzítve (várhatóan π/16, 32).

# Qubit-indexek a szimulációs áramkörben (konzisztens a futtatási sorrenddel):
#   q0 = S (a megőrzött bit), q1 = A1, q2 = A2, q3 = A3
Q_S, Q_A1, Q_A2, Q_A3 = 0, 1, 2, 3
N_QUBITS = 4
ARM_NAMES = ["n0", "n1", "n2", "n3", "cut", "noisy"]

# Karok definíciója: mely S–Ai csatolások aktívak, és a horgonyok kezdőállapota.
ARM_DEFS = {
    "n0":    {"coupled": [],          "anchors_init": "0", "role": "alapvonal (saját T1/T2 romlás)"},
    "n1":    {"coupled": ["A1"],      "anchors_init": "0", "role": "egy gumi (a rezonátor 3. fázis megfelelője)"},
    "n2":    {"coupled": ["A1", "A2"],"anchors_init": "0", "role": "két gumi"},
    "n3":    {"coupled": ["A1", "A2", "A3"], "anchors_init": "0", "role": "a háromszög"},
    "cut":   {"coupled": ["A1", "A2"],"anchors_init": "0",
              "role": "'elvágott gumi' kontroll: 3 horgony JELEN (A3 dekóherál), A3 csatolása kimarad, idő kitöltve"},
    "noisy": {"coupled": ["A1", "A2", "A3"], "anchors_init": "+", "role": "zajos környezet kontroll (horgonyok |+⟩-ből indulnak)"},
}
# Szerkezeti megjegyzés a cut karról: áramköri szinten a cut és az n2 ugyanazt a
# kapuszekvenciát hajtja végre (S–A1, S–A2 részleges SWAP-ok + idők kitöltve). A
# különbség fizikai: a cut-ban a JELEN LÉVŐ, de csatolatlan A3 dekóherálódik
# (és a valós chipen áthallást/kereszt-fázist okozhat). A jelen szimulációban —
# áthallásmodell nélkül — a két görbe azonos; ez a terv 3.2 szerinti kitöltést
# követi, és nincs benne "beállítottság", ami utólagos optimalizálásnak
# minősülhetne.

# Szimmetria-szabály (terv 3.2): a körönkénti páronkénti csatolások sorrendjét
# forgatjuk: A1A2A3 → A2A3A1 → A3A1A2.
SLOT_ORDERS = [["A1", "A2", "A3"], ["A2", "A3", "A1"], ["A3", "A1", "A2"]]

# Mérési ágak és kezdőállapotok (terv 3.2)
BRANCH_POPULATION = "population"  # Z-mérés; S ∈ {|0⟩, |1⟩}
BRANCH_COHERENCE = "coherence"    # X-mérés; S ≡ |+⟩ (MÁSODLAGOS, nem keverhető a fő ítéletbe)
POP_INITS = ["0", "1"]
COH_INIT = "+"

# Szimulációs alapbeállítások (fázis 0 / dryrun; NEM a QPU-lövés-szám!)
SHOTS = 4096
SEED = 42
BOOTSTRAP_N = 2000
BOOTSTRAP_SEED = 20261111

# ---------------------------------------------------------------------------
# Zajos paraméterek — DOKUMENTÁLT MINTAÉRTÉKEK, nem mérési adatok!
# Heron r2-típusú, nagyságrendileg reális értékek a zajmodell kipróbálásához.
# A végleges snapshot.json a Control Agent / a tulajdonos által készül, ugyanazzal
# a sémával (src/sim.py: load_noise_snapshot); az értékek ekkor CSERÉLŐDNEK,
# a kód nem változik.
# ---------------------------------------------------------------------------
SNAPSHOT_SAMPLE = {
    "source": "SAMPLE — dokumentált mintaértékek, NEM chip-pillanatkép (0. fázis)",
    "is_sample": True,
    "captured_at": None,
    "qubits": {
        "S":  {"T1_us": 180.0, "T2_us": 140.0, "eps_1q": 2.5e-4, "eps_2q": 3.0e-3, "eps_readout": 1.0e-2},
        "A1": {"T1_us": 160.0, "T2_us": 120.0, "eps_1q": 3.0e-4, "eps_2q": 3.5e-3, "eps_readout": 1.2e-2},
        "A2": {"T1_us": 200.0, "T2_us": 150.0, "eps_1q": 2.0e-4, "eps_2q": 2.8e-3, "eps_readout": 0.9e-2},
        "A3": {"T1_us": 150.0, "T2_us": 110.0, "eps_1q": 3.2e-4, "eps_2q": 4.0e-3, "eps_readout": 1.4e-2},
    },
    # Kapuszám-időtartamok (reprezentatív, minta); mikroszekundumban olvassa a zajmodell.
    "gate_durations": {"t1q_us": 0.050, "t2q_us": 0.300, "treadout_us": 0.800},
}

# A snapshot séma, hogy a leendő snapshot.json "egy az egyben" behelyettesíthető legyen:
SNAPSHOT_SCHEMA_DOC = """\
{
  "source": "string — honnan származik (kötelező, 'SAMPLE' tilos éles futtatásban)",
  "is_sample": false,
  "captured_at": "ISO-8601 vagy szám — a pillanatkép ideje",
  "qubits": {
    "S":  {"T1_us": float, "T2_us": float, "eps_1q": float, "eps_2q": float, "eps_readout": float},
    "A1": { ... ugyanaz a séma ... },
    "A2": { ... },
    "A3": { ... }
  },
  "gate_durations": {"t1q_us": float, "t2q_us": float, "treadout_us": float}
}
A 2Q-hibát páronként eps_2q(S) + eps_2q(Ai) összegként építi a zajmodell
(konzervatív, dokumentált választás). Az eps_* depolarizáló, a T1/T2 termikus
relaxációs csatornaként (qiskit_aer.noise.thermal_relaxation_error) kerül az
áramkör minden kapujára. Az üres (kitöltő) lépés = 'id' kapu t2q_us időtartammal.
"""

# ---------------------------------------------------------------------------
# DÖNTÉSI REFERENCIA (a terv 4. fejezetéből — az irányadó forrás a
# preregistration/frozen_params.json; itt csak tájékoztatásképp)
# ---------------------------------------------------------------------------
DECISION_REFERENCE = {
    "p1_expected_ratios": {"n1": 1.0, "n2": 0.71, "n3": 0.58},  # 1 : 0.71 : 0.58
    "p1_ratio_tol_rel": 0.20,
    "p2_ci_level": 0.99,        # A_vissza(n3) ≥ A_vissza(n1) az n3 első csúcsánál, 99% CI (v1.2, Holm)
    "p3_height_rel": 0.20,      # cut ≥ 20%-kal alacsonyabb VAGY
    "p3_shift_min_steps": 2,    # ≥ 2 lépéssel eltolódik n3-hoz képest
    "p3_ci_level": 0.99,
    "bootstrap_n": 2000,
    "dip_frac": 0.95,           # D-nek ezalatt kell esnie, mielőtt a visszatérési csúcsot keressük (nem CI-döntés)
}

ARMS = tuple(ARM_NAMES)
