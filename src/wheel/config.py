"""Kerék-menet — központi konfiguráció (PLAN_WHEEL_v1.2 alapján).

Források:
- Terv: preregistration/PLAN_WHEEL_v1.2.md (amended, érvényes; a v1.0/v1.1 transport változatlan; a v1.1 superseded).
- A mért pillanatkép: data/snapshot.json (2026-11-11, ibm_kingston, VALÓS
  backend-pillanatkép a csillag-menet beküldésének pillanatában — dokumentált
  kiindulás, NEM hardver-eredmény; a zajos szimuláció kiindulópontja).

FONTOS: a döntési küszöbök NEM innen élnek — a preregistration/frozen_wheel_params_v1.2.json
(hash: frozen_wheel_params_v1.2.json.sha256) a forrás; a src/wheel/analysis.py minden futtatáskor
ellenőrzi. Az itt lévő értékek a 0. fázis által KIJELÖLT, fagyasztott értékek másolatai.
"""
from __future__ import annotations

import math

# ---------------------------------------------------------------------------
# Qubit-szerepek (a csillag-menet layoutja — PLAN_WHEEL_v1.1, javítás #1)
# q0 = S (középpont, a mért bit), q1..q3 = gyűrű R1..R3
# Fizikai leképezés (dokumentált, rögzített): S=125, R1=117, R2=124, R3=126 (ibm_kingston)
# ---------------------------------------------------------------------------
Q_S, Q_R1, Q_R2, Q_R3 = 0, 1, 2, 3
N_QUBITS = 4
ROLE_TO_PHYS = {"S": 125, "R1": 117, "R2": 124, "R3": 126}
SNAPSHOT_QUBIT_KEY = {"S": "S", "R1": "A1", "R2": "A2", "R3": "A3"}  # snapshot.json-kulcsok (önkényes, rögzített)
BACKEND_NAME = "ibm_kingston"

# ---------------------------------------------------------------------------
# Fizikai állandók — a 0. fázis szimulációja alapján, fagyasztva (v1.1)
# ---------------------------------------------------------------------------
PHI = math.pi / 16                 # élenként lépés/kör szög (a csillaggal azonos nyelvezet)
PHI_F = math.pi / 6                # körbejárási fázistolás (szintetikus fluxus) / él; Φ = 3·φ_f = π/2
K = 32                             # lépésszám (0..K)
T_HOLD_US = 5.0                    # tárolási kitöltés / lépés (a lépés időtartamának nagy része)
N_2Q_SLOTS_PER_ROUND = 6           # 3 gyűrű-él + 3 küllő — MINDEN karban azonos számú 2Q-slot
T_STEP_US = T_HOLD_US + N_2Q_SLOTS_PER_ROUND * 0.068  # lépésköz ≈ 5.408 µs
THETA_SP = PHI                     # küllő-szög — A PRIORI döntés: azonos PHI-vel (nincs paraméter-halászat)
OMEGA_DIR = (2 * 1.0477) / 3       # irány-szétválás szögfrekvenciája / kör (supercell, zajtalan) ≈ 0.6984 rad
PUMP_FREQ = 2.0 * OMEGA_DIR        # a vak pumpa modulációs frekvenciája = 2Ω
M_BLIND = 0.20                     # vak pumpa mélysége — A PRIORI rögzített (középső érték)
PUMP_FI_P = 0.0                    # vak pumpa fázisa — A PRIORI rögzített
M_DIR = 0.20                       # W4 iránykövető lökés mélysége — A PRIORI rögzített

# Az irány-sajátállapotok és a 0. fázisban számolt körzet (dokumentálva, nem mért adat)
SUPERCELL_PHASES = [-1.0477, 0.0, 1.0477]  # rad / 3 kör, φ_f = π/6 (zajtalan)

# ---------------------------------------------------------------------------
# Karok — MINDEN kar azonos számú 2Q-slottal (gate-count matching, javítás #3)
# variant: "ideal" (közvetlen PSWAP, absztrakt gyűrű) vagy "routed"
#          (a tényleges elrendezésen SWAP-hálózattal végigvitt, virtualis gyűrű)
# ---------------------------------------------------------------------------
ARM_DEFS = {
    "wheel":      {"m_ring": +1, "spokes": "rotating", "echo": False, "role": "a teljes szerkezet (fogó gyűrű + küllők)"},
    "wheel_rev":  {"m_ring": -1, "spokes": "rotating", "echo": False, "role": "fordított keringési irány (W2)"},
    "static":     {"m_ring": +1, "spokes": "static",   "echo": False, "role": "álló küllők (0/120/240 minta, forgatás nélkül)"},
    "ring_only":  {"m_ring": +1, "spokes": "none",     "echo": False, "role": "keringő gyűrű, középpont küllők nélkül"},
    "alone":      {"m_ring": +1, "spokes": "none",     "echo": False, "role": "középpont magában (azonos idő, 6 üres 2Q-slot)", "ring_off": True},
    "alone_DD":   {"m_ring": +1, "spokes": "none",     "echo": True,  "role": "középpont magában + minden lépésben pi-echo (a DD-kontroll, javítás #3)", "ring_off": True},
    "pump_blind": {"m_ring": +1, "spokes": "rotating", "echo": False, "role": "wheel + vak parametrikus pumpa (másodlagos)", "pump": "blind"},
    "pump_dir":   {"m_ring": +1, "spokes": "rotating", "echo": False, "role": "wheel + iránykövető lökések (másodlagos, W4, csak középpont-megtartás)", "pump": "dir"},
    "pump_wrong": {"m_ring": +1, "spokes": "rotating", "echo": False, "role": "wheel + fordított sorrendű lökések (W4 kontrollja)", "pump": "wrong"},
    "cut":        {"m_ring": +1, "spokes": "rotating", "echo": False, "role": "megszakított gyűrű (él 3–1 kihagyva) — az ANOMALIA/W3 negatív kontrollja", "cut_edge": "02"},
    # sotetallápot-teszt (javítás #6): a ring NEM forgo/ellenforgo vs nem forgó — S=|1> kezd
    "dark_m1":    {"m_ring": +1, "spokes": "rotating", "echo": False, "role": "sotetallapot-teszt, m=+1 forgó gyűrű", "dark": True},
    "dark_m0":    {"m_ring":  0, "spokes": "rotating", "echo": False, "role": "sotetallapot-teszt, m=0 nem forgó gyűrű", "dark": True},
    "dark_mm1":   {"m_ring": -1, "spokes": "rotating", "echo": False, "role": "sotetallapot-teszt, m=-1 ellenforgó gyűrű", "dark": True},
}
ARM_NAMES = list(ARM_DEFS)
DARK_ARMS = ["dark_m1", "dark_m0", "dark_mm1"]
MAIN_ARMS = ["wheel", "wheel_rev", "static", "ring_only", "alone", "alone_DD"]
SECONDARY_ARMS = ["pump_blind", "pump_dir", "pump_wrong"]
CONTROL_ARMS = ["cut"]

# Állítás-család (Holm-korrekció, javítás #7) — A PRIORI, előre felsorolva
CLAIM_FAMILY = ["W1", "W2", "W4_secondary", "sotetallapot"]
CI_LEVEL = 0.99          # a szigorúbb szint (v1.1, javítás #7)
HOLM = True
BOOTSTRAP_N = 2000
BOOTSTRAP_SEED = 20261111
SHOTS = 4096
SEED = 42

# Pozitív kontroll (javítás #5): ismert erősségű, beépített stabilizáló hatás
POSITIVE_CONTROL = {
    "description": "a középpontra minden lépésben Ry(2*EPS_RESTORE) a |1> felé (ismert erősségű, beépített stabilizáló hatás — csak szimulációs diagnosztika, SOSEM QPU-kar)",
    "EPS_RESTORE": 0.15,
    "required_effect": "az elemzőnek a beépített hatást >5 szigma szinten ki kell mutatnia (retention-különbség a kontroll-karhoz képest); ha nem mutatja ki, az elemző hibás, nem a fizika",
}

# A branch-ek
BRANCH_POPULATION = "population"   # S ∈ {|0>, |1>}, Z-mérés; D_S fő ág
BRANCH_COHERENCE = "coherence"     # S ≡ |+>, X-mérés (másodlagos)
POP_INITS = ["0", "1"]
COH_INIT = "+"
