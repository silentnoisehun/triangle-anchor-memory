"""Szimuláció — zajtalan és zajos (T1/T2/ε-paraméteres) — 0. fázis.

Két szint:
1. ``sweep_exact``      — pontos (statevector / density_matrix) elvárt értékek;
   ezt használja a fagyasztás (src/freeze.py) a várt görbékhez és az
   ANOMÁLIA-referenciához. Determinista, lövés-zaj NINCS benne.
2. ``sweep_counts``     — Aer qasm shot-alapú counts; ezt használja a dryrun a
   teljes (elemzést is magába foglaló) folyamathoz, seed-el, hogy
   reprodukálható legyen.

Zajmodell (dokumentált választások):
- T1/T2 → qiskit_aer.noise.thermal_relaxation_error minden kapura, a tényleges
  kapuidővel (1Q: t1q_us, kitöltő 'id': t2q_us, 2Q ('unitary'/PSWAP): t2q_us);
- eps_1q / eps_2q → depolarizáló csatorna a termikus csatorna UTÁN (compose);
- a 2Q-hiba páronként eps_2q(S) + eps_2q(Ai) (konzervatív összeg, dokumentálva);
- eps_readout → simetrikus kiolvasási hibamátrix qubitenként.

A HIBAFORRÁS-FÜGGŐ részletek a snapshot sémában (src/config.py SNAPSHOT_SCHEMA_DOC)
rögzítve; a leendő chip-pillanatkép egy az egyben betölthető a path-argumentummal.

POZITÍV KONTROLL (terv 5. fejezet, 0. fázis): ``coupling_scale=0.0`` mellett az
összes PSWAP eltűnik (kitöltő 'id'-k maradnak) → D(k) ≡ konstans → az elemzőnek
NULL ítéletet kell adnia. Ez a száraz futás kötelező kontrollága.
"""
from __future__ import annotations

import copy
import json
import warnings
from pathlib import Path

from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error, thermal_relaxation_error
from qiskit.quantum_info import DensityMatrix, Statevector

from . import config
from .circuits import build_arm_circuit

REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Snapshot (zajpillanatkép) betöltése és validálása
# ---------------------------------------------------------------------------
def load_noise_snapshot(path: str | Path | None = None) -> dict:
    """Zajos paraméterek betöltése.

    path=None → config.SNAPSHOT_SAMPLE (dokumentált MINTAÉRTÉKEK, is_sample=True).
    A tényleges QPU-futtatás előtt a Control Agent állít elő snapshot.json-t ugyanazzal
    a sémával; ekkor path=<snapshot.json> — a kód nem változik.
    """
    if path is None:
        return copy.deepcopy(config.SNAPSHOT_SAMPLE)
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        snap = json.load(f)
    validate_snapshot(snap)
    if snap.get("is_sample"):
        warnings.warn("a snapshot is_sample=True-nak van jelölve — ez NEM éles chip-adat!", stacklevel=2)
    return snap


def validate_snapshot(snap: dict) -> None:
    if not isinstance(snap, dict):
        raise ValueError("a snapshot-nak JSON-objektumot kell tartalmaznia")
    for key in ("qubits", "gate_durations"):
        if key not in snap:
            raise ValueError(f"snapshot: hiányzó kulcs: {key}")
    required_q = {"T1_us", "T2_us", "eps_1q", "eps_2q", "eps_readout"}
    for name in ("S", "A1", "A2", "A3"):
        if name not in snap["qubits"]:
            raise ValueError(f"snapshot: hiányzó qubit-bejegyzés: {name}")
        q = snap["qubits"][name]
        missing = required_q - q.keys()
        if missing:
            raise ValueError(f"snapshot: {name} hiányzó paraméterei: {sorted(missing)}")
        for p in ("T1_us", "T2_us"):
            if not (0.0 < q[p]):
                raise ValueError(f"snapshot: {name}.{p} pozitívnak kell lennie")
        if q["T2_us"] > 2.0 * q["T1_us"]:
            warnings.warn(f"snapshot: {name} T2 > 2·T1 — fizikailag gyanús, ellenőrizd!", stacklevel=2)
        for p in ("eps_1q", "eps_2q", "eps_readout"):
            if not (0.0 <= q[p] < 1.0):
                raise ValueError(f"snapshot: {name}.{p} ∈ [0, 1) tartomány kell legyen")
    for p in ("t1q_us", "t2q_us", "treadout_us"):
        if p not in snap["gate_durations"] or not (0.0 < snap["gate_durations"][p]):
            raise ValueError(f"snapshot: gate_durations.{p} pozitív szám kell legyen")


# ---------------------------------------------------------------------------
# Zajmodell (qiskit-aer)
# ---------------------------------------------------------------------------
_ANCHOR_IDX = {"A1": config.Q_A1, "A2": config.Q_A2, "A3": config.Q_A3}


def build_noise_model(snap: dict) -> NoiseModel:
    validate_snapshot(snap)
    nm = NoiseModel()
    dur = snap["gate_durations"]
    t1q, t2q = float(dur["t1q_us"]), float(dur["t2q_us"])

    for name, qi in (("S", config.Q_S), *_ANCHOR_IDX.items()):
        q = snap["qubits"][name]
        t1, t2 = float(q["T1_us"]), float(q["T2_us"])

        # 1Q-kapuk (H, X) — tényleges 1Q-kapuidővel
        therm_1q = thermal_relaxation_error(t1, t2, t1q)
        nm.add_quantum_error(
            therm_1q.compose(depolarizing_error(float(q["eps_1q"]), 1)),
            ["h", "x"],
            [qi],
        )
        # Kitöltő 'id' — egy 2Q-slot időtartamával (a terv 3.2 időkitöltése)
        therm_id = thermal_relaxation_error(t1, t2, t2q)
        nm.add_quantum_error(
            therm_id.compose(depolarizing_error(float(q["eps_1q"]), 1)),
            ["id"],
            [qi],
        )
        # Kiolvasási hiba (szimmetrikus)
        e = float(q["eps_readout"])
        nm.add_readout_error(ReadoutError([[1.0 - e, e], [e, 1.0 - e]]), [qi])

    # PSWAP ('unitary') páronként: S–Ai — eps_2q összeggel (dokumentált választás)
    qs = snap["qubits"]["S"]
    for anchor, qi in _ANCHOR_IDX.items():
        qa = snap["qubits"][anchor]
        eps2 = float(qs["eps_2q"]) + float(qa["eps_2q"])
        therm_pair = thermal_relaxation_error(
            float(qs["T1_us"]), float(qs["T2_us"]), t2q
        ).tensor(thermal_relaxation_error(float(qa["T1_us"]), float(qa["T2_us"]), t2q))
        nm.add_quantum_error(
            therm_pair.compose(depolarizing_error(eps2, 2)),
            ["unitary"],
            [config.Q_S, _ANCHOR_IDX[anchor]],
        )
    return nm


# ---------------------------------------------------------------------------
# Pontos elvárt értékek (lövés-zaj nélkül)
# ---------------------------------------------------------------------------
def expectation_probs(
    arm: str,
    branch: str,
    k_rounds: int,
    init_state: str | None = None,
    snapshot: dict | None = None,
    coupling_scale: float = 1.0,
) -> dict[str, float]:
    """P(S=0), P(S=1) a k-adik kör után, mérés NÉLKÜL.

    A koherencia-ágban a mérés előtti H-t itt is alkalmazzuk (ugyanaz a forgatás),
    így az eredmény a Z-mérés kimenete: p0 = P(+ outcome), p1 = P(− outcome).
    """
    if branch == config.BRANCH_POPULATION:
        init = init_state
    else:
        init = config.COH_INIT
    qc = build_arm_circuit(arm, k_rounds, branch, init, coupling_scale=coupling_scale, measure=False)
    if branch == config.BRANCH_COHERENCE:
        qc.h(config.Q_S)

    if snapshot is None:
        sv = Statevector.from_instruction(qc)
        probs = sv.probabilities(qargs=[config.Q_S])
    else:
        nm = build_noise_model(snapshot)
        sim = AerSimulator(method="density_matrix", noise_model=nm, seed_simulator=config.SEED)
        qc.save_density_matrix()
        result = sim.run(qc, shots=1).result()
        dm = DensityMatrix(result.data(0)["density_matrix"])
        probs = dm.probabilities(qargs=[config.Q_S])
    return {"p0": float(probs[0]), "p1": float(probs[1])}


def sweep_exact(
    snapshot: dict | None = None,
    coupling_scale: float = 1.0,
    ks: range | None = None,
) -> dict:
    """Minden karra, mindkét ágra, k = 0..K: pontos {'p0','p1'} listák."""
    ks = ks if ks is not None else range(config.K + 1)
    out: dict[str, dict] = {}
    for arm in config.ARM_NAMES:
        out[arm] = {"population": {i: [] for i in config.POP_INITS}, "coherence": {config.COH_INIT: []}}
        for k in ks:
            for init in config.POP_INITS:
                out[arm]["population"][init].append(
                    expectation_probs(arm, config.BRANCH_POPULATION, k, init, snapshot, coupling_scale)
                )
            out[arm]["coherence"][config.COH_INIT].append(
                expectation_probs(arm, config.BRANCH_COHERENCE, k, None, snapshot, coupling_scale)
            )
    return out


# ---------------------------------------------------------------------------
# Lövés-alapú counts (dryrun / később a QPU statisztika helyettesítője)
# ---------------------------------------------------------------------------
def simulate_counts(
    arm: str,
    branch: str,
    k_rounds: int,
    init_state: str | None,
    shots: int,
    seed: int,
    snapshot: dict | None = None,
    coupling_scale: float = 1.0,
) -> dict[str, int]:
    if branch == config.BRANCH_POPULATION:
        init = init_state
    else:
        init = config.COH_INIT
    qc = build_arm_circuit(arm, k_rounds, branch, init, coupling_scale=coupling_scale, measure=True)
    if snapshot is not None:
        nm = build_noise_model(snapshot)
        sim = AerSimulator(noise_model=nm, seed_simulator=seed)
    else:
        sim = AerSimulator(seed_simulator=seed)
    return sim.run(qc, shots=shots).result().get_counts(qc)


def sweep_counts(
    snapshot: dict | None = None,
    coupling_scale: float = 1.0,
    shots: int = config.SHOTS,
    seed: int = config.SEED,
    ks: range | None = None,
) -> dict:
    """Minden karra, mindkét ágra, k = 0..K: counts-szótár.

    A visszatérés: {'population': {arm: {init: {k: counts}}},
                    'coherence':  {arm: {'+': {k: counts}}},
                    'shots': int, 'seed': int, 'coupling_scale': float}
    """
    ks = ks if ks is not None else range(config.K + 1)
    dataset = {
        "population": {arm: {i: {} for i in config.POP_INITS} for arm in config.ARM_NAMES},
        "coherence": {arm: {config.COH_INIT: {}} for arm in config.ARM_NAMES},
        "shots": int(shots),
        "seed": int(seed),
        "coupling_scale": float(coupling_scale),
        "is_sample_noise": bool(snapshot is not None and snapshot.get("is_sample", False)),
    }
    for arm in config.ARM_NAMES:
        for k in ks:
            for init in config.POP_INITS:
                dataset["population"][arm][init][str(k)] = simulate_counts(
                    arm, config.BRANCH_POPULATION, k, init, shots, seed, snapshot, coupling_scale
                )
            dataset["coherence"][arm][config.COH_INIT][str(k)] = simulate_counts(
                arm, config.BRANCH_COHERENCE, k, None, shots, seed, snapshot, coupling_scale
            )
    return dataset


def exact_D_curves(exact: dict) -> dict[str, dict[str, list[float]]]:
    """Az exact-sweepből D(k) görbék: population: |p1(1)−p1(0)|; coherence: |2·p0−1|."""
    out: dict[str, dict[str, list[float]]] = {}
    for arm, arms in exact.items():
        pop1 = [d["p1"] for d in arms["population"]["1"]]
        pop0 = [d["p1"] for d in arms["population"]["0"]]
        coh0 = [d["p0"] for d in arms["coherence"][config.COH_INIT]]
        out[arm] = {
            "population": [abs(a - b) for a, b in zip(pop1, pop0)],
            "coherence": [abs(2.0 * a - 1.0) for a in coh0],
        }
    return out
