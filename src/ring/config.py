"""A gyűrű-menet befagyasztandó/konstansok (a 0. fázis előtt a terv szerint)."""
K = 32
STEP_GRID = tuple(range(0, K + 1, 4))   # 9 ellenpont, a csillag-menet rácsa
SHOTS = 4096
BOOTSTRAP_N = 2000
BOOTSTRAP_SEED = 20261111
CI_LEVEL = 0.95                          # a gyűrű-meneten 95% (előre rögzítve)
CORRECTION = "holm"
CLAIM_FAMILY = ["R1", "R2", "pump", "nc"]

PHI = 3.141592653589793 / 16             # θ a kör-élekben (a kerék-menet φ-ével azonos)
PHI_F = 3.141592653589793 / 6            # φ_f / él; teljes fluxus Φ = 3·φ_f = π/2
STATIC_FLUX = 0.0                        # a fluxus-mentes (static) referencia

# pump (a kiegészítés szerint)
PUMP_M = [0.0, 0.1, 0.2, 0.3]
PUMP_FI_P = [0.0, 1.5707963267948966]
PUMP_KICK_P = 2e-4                       # vak-lökés hiba / impulzus (a kerék pumpa-blokkjával azonos mobil)

# döntési küszöbök (előre rögzítve)
TAU_CROSS = 0.75                         # τ_irány: a C(k) < 0.75 keresztezése, lineáris interpoláció
GATE_HEALTH_P0 = 0.70                    # a gép-egészség előkapu (mint a küszöb-job)
DELTA_K0_MAX = 0.10                      # a három kar k=0-értékének max. távolsága

ARMS = [
    ("ring_p",  {"prep_m": +1, "flux": PHI_F, "edges": True,  "cut": False, "pump_m": None, "desc": "keringő gyűrű, m=+1 (a fő kar)"}),
    ("ring_m",  {"prep_m": -1, "flux": PHI_F, "edges": True,  "cut": False, "pump_m": None, "desc": "keringő gyűrű, m=−1 (W2-párhuzam)"}),
    ("ring_0",  {"prep_m": 0,  "flux": PHI_F, "edges": True,  "cut": False, "pump_m": None, "desc": "nem forgó sajátállapot (kontroll)"}),
    ("static",  {"prep_m": +1, "flux": STATIC_FLUX, "edges": True, "cut": False, "pump_m": None, "desc": "fluxus OFF — a keringés kapu-őre (R2)"}),
    ("broken",  {"prep_m": +1, "flux": PHI_F, "edges": True,  "cut": True,  "pump_m": None, "desc": "CUT — csak a (R3,R1) él nyitott (identitás); a többi él AKTÍV — NC, NULL-várt"}),
    ("pump",    {"prep_m": +1, "flux": PHI_F, "edges": True,  "cut": False, "pump_m": "scan", "desc": "parametrikus pumpa — m∈{0,0.1,0.2,0.3}, φ_p∈{0,π/2} (másodlagos)"}),
    ("star",    {"prep_m": None, "flux": None, "edges": False, "cut": False, "pump_m": None, "desc": "(a) csillag-visszaáramlás, azonos össz-kapukosztés — kontroll"}),
    ("lone",    {"prep_m": None, "flux": None, "edges": False, "cut": False, "pump_m": None, "desc": "(b) magányos qubit |1⟩ — tiszta T1/T2-korlát"}),
    ("delayed", {"prep_m": None, "flux": None, "edges": False, "cut": False, "pump_m": None, "desc": "(c) horgony nélküli, csak identitás-kitöltők — tiszta kapukosztás-korlát"}),
]
ARM_NAMES = [a for a, _ in ARMS]
