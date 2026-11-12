"""Áramkör-építők — karok + kalibráció (terv 3.2 és 3.3).

Konvenciók:
- Qubit-indexek: q0 = S, q1 = A1, q2 = A2, q3 = A3; a klasszikus bit i ↔ qubit i,
  tehát a counts bitstringjének JOBB SZÉLSŐ bitje az S mérése.
- Részleges SWAP (PSWAP) egység: mátrix
      [[1, 0, 0, 0],
       [0, cosφ, −i sinφ, 0],
       [0, −i sinφ, cosφ, 0],
       [0, 0, 0, 1]]
  az egygerjesztés-altérben φ-t forgat; φ = π/2 esetén iSWAP-szerű teljes csere.
  A PSWAP az áramkörben 'unitary' kapuként jelenik meg (a UnitaryGate neve
  kódszinten rögzített); a zajmodell ehhez a névhez köt 2Q-hibát, és a
  körökben a 'unitary' kapuk KIZÁRÓLAG PSWAP-ok.
  Hardveren az auditálás során natív kapukra kell majd bontani (ez az 1. fázis /
  Control Agent dolga; itt U(φ) egy UnitaryGate-ként szerepel).
- Minden kör (round) 3 időrést (slot) tartalmaz: A1A2A3 → A2A3A1 → A3A1A2
  sorrend-forgatással (terv 3.2, szimmetria-szabály). Minden slot VAGY PSWAP
  (aktív páron), VAGY kitöltő 'id' kapu mindkét érintett qubiten — így minden kar
  össz-időtartama azonos (3 slot × K kör, t2q_us időtartamú slotonként).
- 'cut' kar: az A3-slot ELHAGYJA a PSWAP-ot és kitöltő 'id'-t kap — a horgonyok
  mind jelen vannak, a teljes idő változatlan (terv 3.2).
- 'noisy' kar: a horgonyok |+⟩-ből indulnak (H minden horgonyon a körök előtt).
- KARHOSSZ-KIEGYENLÍTÉS (v1.3, 4. pont): az ``idle_pad_dt`` paraméter dt-ben
  (default: None = automatikus, src/kingston_routing.py számítja a FakeKingston
  ALAP-időzítéséből, initial_layout=[125,117,124,126], opt0, seed 1234; explicit
  int ≥ 0 felülírja; 0 kikapcsolja) a mérés ELÉ minden qubitre egy ``delay``-t
  szúr be, hogy minden kar ALAP-hossza a közös cél-idővel egyezzen, k-nként
  (cél-idő = az n3 kar hossza; kivétel a population/init="0" csoport, ahol a
  ``noisy`` kar horgony-H szintézise 8 dt-vel hosszabb az n3-nál — ott a cél a
  noisy hossza; lásd src/kingston_routing.py). A kerekített, transzpilált
  hosszekvivalencia kapuja a dryrun kötelező PASS-pontja: |hossz(arm) − cél| ≤ 1 dt.
- Koherencia-ág: S inicializálása H-val; a mérés előtt újabb H (X-bázisú olvasás).
  A koherencia-ág MÁSODLAGOS (terv 3.2) — nem kerül a fő ítéletbe.
"""
from __future__ import annotations

import math

import numpy as np
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import UnitaryGate

from . import config

ANCHOR_TO_QUBIT = {"A1": config.Q_A1, "A2": config.Q_A2, "A3": config.Q_A3}


def partial_swap_unitary(phi: float) -> np.ndarray:
    """A φ szögű részleges SWAP egységmátrixa (lásd modul-docstring)."""
    c, s = math.cos(phi), math.sin(phi)
    return np.array(
        [[1.0, 0.0, 0.0, 0.0],
         [0.0, c, -1j * s, 0.0],
         [0.0, -1j * s, c, 0.0],
         [0.0, 0.0, 0.0, 1.0]],
        dtype=complex,
    )


def _pswap_gate(phi: float) -> UnitaryGate:
    # Az utasítás neve a Qiskitben 'unitary' (a címke csak megjelenítés);
    # a zajmodell ezért az 'unitary' névhez köt 2Q-hibát (lásd modul-docstring).
    return UnitaryGate(partial_swap_unitary(phi), label="pswap")


def _idle_pair(qc: QuantumCircuit, q_a: int, q_b: int) -> None:
    # Kitöltő idő: mindkét qubiten 1-1 'id' kapu (a zajmodell t2q_us-ként éri majd őket).
    qc.id(q_a)
    qc.id(q_b)


def build_arm_circuit(
    arm: str,
    k_rounds: int,
    branch: str = config.BRANCH_POPULATION,
    init_state: str | None = None,
    coupling_scale: float = 1.0,
    measure: bool = True,
    idle_pad_dt: int | None = None,
) -> QuantumCircuit:
    """Egy kar áramköre ``k_rounds`` (0..K) kör után.

    branch: 'population' (S ∈ |0⟩,|1⟩, Z-mérés) vagy 'coherence' (S ≡ |+⟩, X-mérés).
    init_state: population ágban '0' vagy '1'; coherence ágban figyelmen kívül hagyható.
    coupling_scale: a PSWAP szögét skálázza — az 1.0 az igazi kísérlet; a 0.0 a
        pozitív (szándékosan rontott) kontroll: "csatolások kikapcsolva".
    idle_pad_dt: üres várakozás (dt) a mérés ELÉ, minden qubitre — a kar
        ALAP-hosszának n3-ra igazítása (v1.3 4. pont). ``None`` = automatikus
        számítás a FakeKingston-ALAP-időzítésből (src/kingston_routing.py);
        explicit int ≥ 0 felülírja; ``0`` = kikapcsolva (nyers kör).
    """
    if idle_pad_dt is None:
        from .kingston_routing import idle_pad_dt as _auto_pad

        idle_pad_dt = _auto_pad(arm, k_rounds, branch, init_state, coupling_scale)
    if int(idle_pad_dt) < 0:
        raise ValueError(f"idle_pad_dt ≥ 0 kell legyen, kapott: {idle_pad_dt}")
    if arm not in config.ARM_DEFS:
        raise ValueError(f"ismeretlen kar: {arm}")
    if not 0 <= k_rounds <= config.K:
        raise ValueError(f"k_rounds tartománya 0..{config.K}, kapott: {k_rounds}")
    if branch not in (config.BRANCH_POPULATION, config.BRANCH_COHERENCE):
        raise ValueError(f"branch: '{config.BRANCH_POPULATION}' vagy '{config.BRANCH_COHERENCE}'")
    if branch == config.BRANCH_POPULATION and init_state not in config.POP_INITS:
        raise ValueError("population ágban init_state ∈ {'0','1'}")

    defn = config.ARM_DEFS[arm]
    coupled = set(defn["coupled"])
    phi = config.PHI * float(coupling_scale)

    q = QuantumRegister(config.N_QUBITS, name="q")
    cregs = ClassicalRegister(config.N_QUBITS, name="c")
    qc = QuantumCircuit(q, cregs, name=f"{arm}_k{k_rounds}_{branch}")

    # --- Inicializálás ---
    if branch == config.BRANCH_POPULATION:
        if init_state == "1":
            qc.x(config.Q_S)
    else:  # coherence ág
        qc.h(config.Q_S)
    if defn["anchors_init"] == "+":
        for anchor in (config.Q_A1, config.Q_A2, config.Q_A3):
            qc.h(anchor)

    # --- Körök: 3 slot, forgatott sorrend, PSWAP vagy kitöltő idő ---
    for r in range(k_rounds):
        order = config.SLOT_ORDERS[r % 3]
        for slot, anchor in enumerate(order):
            qa = config.Q_S
            qn = ANCHOR_TO_QUBIT[anchor]
            if anchor in coupled and coupling_scale != 0.0:
                qc.append(_pswap_gate(phi), [qa, qn])
            else:
                _idle_pair(qc, qa, qn)

    # --- Mérés ---
    if int(idle_pad_dt) > 0:
        # Karhossz-kiegyenlítés (v1.3): üres várakozás a mérés ELÉ,
        # minden qubitre — |hossz(arm) − hossz(n3)| ≤ 1 dt (ALAP, FakeKingston).
        for qubit in q:
            qc.delay(int(idle_pad_dt), qubit, unit="dt")
    if measure:
        if branch == config.BRANCH_COHERENCE:
            qc.h(config.Q_S)  # X → Z bázis
        qc.measure(q, cregs)
    return qc


# ---------------------------------------------------------------------------
# Kalibrációs áramkörök (terv 3.3) — a 0. fázisban NEM futnak, csak definiálva vannak
# ---------------------------------------------------------------------------
def build_t1_circuit(qubit: int, delay_us: float) -> QuantumCircuit:
    """T1-karakterizáció: |1⟩ előkészítése, várakozás, Z-mérés."""
    qc = QuantumCircuit(1, 1, name=f"t1_q{qubit}_{delay_us}us")
    qc.x(0)
    qc.delay(delay_us, 0, unit="us")
    qc.measure(0, 0)
    return qc


def build_hahn_t2_circuit(qubit: int, delay_us: float) -> QuantumCircuit:
    """Hahn-echo T2: |+⟩ → π/2 → várakozás → π-impulzus → várakozás → X-mérés."""
    half = delay_us / 2.0
    qc = QuantumCircuit(1, 1, name=f"hahn_t2_q{qubit}_{delay_us}us")
    qc.h(0)
    qc.delay(half, 0, unit="us")
    qc.x(0)
    qc.delay(half, 0, unit="us")
    qc.h(0)
    qc.measure(0, 0)
    return qc


def build_readout_circuit(qubit: int, prep: str) -> QuantumCircuit:
    """Kiolvasási hiba kalibráció: prep ∈ {'0','1'} → azonnali mérés."""
    if prep not in ("0", "1"):
        raise ValueError("prep ∈ {'0','1'}")
    qc = QuantumCircuit(1, 1, name=f"ro_q{qubit}_{prep}")
    if prep == "1":
        qc.x(0)
    qc.measure(0, 0)
    return qc


def build_pswap_calibration_circuit(arm: str = "n1", k_rounds: int = 1) -> QuantumCircuit:
    """Csatolás-erősség kalibráció az n1 karból: a csere-oszcilláció periódusából
    tényleges φ_eff nyerhető minden S–Ai párra (a 15%-os eltérést a preregisztrált
    elemzésnek jeleznie kell — utólagos 'szimmetrizálás' tilos)."""
    if arm != "n1":
        raise ValueError("a φ_eff kalibráció az n1 karból történik (terv 3.3)")
    return build_arm_circuit("n1", k_rounds, config.BRANCH_POPULATION, "1")


def build_pair_pswap_circuit(
    anchor: str,
    k_rounds: int,
    init_state: str = "1",
    coupling_scale: float = 1.0,
    measure: bool = True,
) -> QuantumCircuit:
    """Egyetlen S–Ai pár PSWAP-oszcillációja — φ_eff kalibráció (terv 3.3).

    2-qubitos áramkör (qv0 = S, qv1 = Ai): x(S) ha init_state == '1';
    k_rounds × PSWAP(φ); Z-mérés. A csere-oszcilláció periódusából a 2. fázisban
    tényleges φ_eff nyerhető minden S–Ai párra (ha a három pár 15%-nál jobban
    eltér, azt a preregisztrált elemzésnek a szimmetria-állításnál jeleznie
    kell — utólagos „szimmetrizálás" tilos).
    """
    if anchor not in ANCHOR_TO_QUBIT:
        raise ValueError(f"anchor ∈ {{'A1','A2','A3'}}, kapott: {anchor}")
    if init_state not in ("0", "1"):
        raise ValueError("init_state ∈ {'0','1'}")
    if not 0 <= k_rounds <= config.K:
        raise ValueError(f"k_rounds tartománya 0..{config.K}")
    phi = config.PHI * float(coupling_scale)
    qc = QuantumCircuit(2, 2, name=f"phi_eff_{anchor}_k{k_rounds}")
    if init_state == "1":
        qc.x(0)
    for _ in range(k_rounds):
        if coupling_scale != 0.0:
            qc.append(_pswap_gate(phi), [0, 1])
        else:
            qc.id(0)
            qc.id(1)
    if measure:
        qc.measure(range(2), range(2))
    return qc


def all_circuits() -> list[QuantumCircuit]:
    """Összes mérési áramkör (kalibráció nélkül), mind a két ágban, k = 0..K.

    6 kar × (2 populációs init × 33 k + 1 koherencia × 33 k) = 594 áramkör.
    """
    circuits = []
    for arm in config.ARM_NAMES:
        for k in range(config.K + 1):
            for init in config.POP_INITS:
                circuits.append(build_arm_circuit(arm, k, config.BRANCH_POPULATION, init))
        for k in range(config.K + 1):
            circuits.append(build_arm_circuit(arm, k, config.BRANCH_COHERENCE))
    return circuits
