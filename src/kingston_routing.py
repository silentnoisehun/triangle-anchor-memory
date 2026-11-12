"""FakeKingston-routolt Aer-valószínűségek és karhossz-kiegyenlítés (Csillag v1.3).

Miért van ez a modul (lásd preregistration/PLAN_v1.3.md):

1. **Karhossz-kiegyenlítés** — a feladat v1.3 4. pontja: minden karban üres
   várakozás, k-nként, minden (branch, init) csoportra. A közös cél-idő az n3
   kar ütemezett (ALAP) hossza; KIVÉTEL a population/init="0" csoport, ahol a
   ``noisy`` kar horgony-H szintézise minden k-ra pontosan 8 dt-vel hosszabb az
   n3-nál — a leghosszabb kart nem lehet utólag rövidíteni, ezért ott a cél-idő
   a ``noisy`` hossza (dokumentált, plan-szakasz: PLAN_v1.3.md). A padding a
   FakeKingston-célra (dt = 4e-9 s), fix layouttal (``initial_layout=
   [125, 117, 124, 126]``, q0=S=125, q1=A1=117, q2=A2=124, q3=A3=126),
   ``optimization_level=0``, ``scheduling_method="alap"``,
   ``seed_transpiler=1234`` mellett számolt ALAP-időzítésre készül. A kapu
   (dryrun kotelezo PASS-pontja): transpile + ALAP utan |hossz(arm) - cél| <=
   1 dt minden k-ra, minden (branch, init) csoportban és coupling_scale-en.

2. **FakeKingston-routolt Aer-valószínűségek** — Maya elkerhetó furt-ajánlatának
   (agent_feladat_csillag_v13.txt, 5. pont) megfelelóen: a transpile-olt
   (ALAP) körpéldány instrukcióit helyi (4-qubitos) áramkörbe másolva — a
   156-qubitos teljes eszköz-szimuláció Aer-density_matrix-szal futtathatatlan
   (memória) —, a FakeKingston-kalibrációból épített zajmodellel, 4 qubiton
   futtatva. A mérés a számolt Sűrűség-mátrixból analitikusan, a kiolvasási
   hiba analitikus (szimmetrikus) rávetítésével számítható.

**Dokumentált korlátok (öszintén):**
- A kitöltő ``delay``-eken NEM fut T1/T2-zaj ebben a verzióban (a FakeKingston
  ``target`` sem hordoz delay-zajt); az 1Q (sx/x) és 2Q (cz) kapuk NOISE-modellje
  viszont valós (termál relaxáció a kapuidőre + depolarizáció a cél-hibával),
  a kiolvasás pedig hibás (a target kiolvasási rátája, szimmetrikus közelítéssel).
- A zaj eloszlása a kapu-időtartamokkal arányos; a ``rz`` virtuális (dur 0, err 0) —
  zaj nélkül marad.
- Ez a modul NEM állít semmit a hardver-futásról; szimuláció SOHA nem HARDWARE.
  A beküldés a tulajdonos külön döntésével, a run.py-n keresztül történne.
- A layoutot és a dt-t a végső hardver-beküldés előtt (csak tulajdonosi döntésre)
  újra ellenőrizni kell a tényleges backend-target ellen.
"""
from __future__ import annotations

import warnings
from functools import lru_cache

import numpy as np

from . import config

# q0=S=125, q1=A1=117, q2=A2=124, q3=A3=126 (initial_layout)
LAYOUT = (125, 117, 124, 126)
PHYS_TO_LOCAL = {phys: local for local, phys in enumerate(LAYOUT)}
CZ_PAIRS = tuple(sorted({tuple(sorted(p)) for p in ((125, 117), (125, 124), (125, 126))}))
SEED_TRANSPILER = 1234
DT_NS = 4.0  # FakeKingston dt = 4e-9 s

_backend = None


def _be():
    global _backend
    if _backend is None:
        from qiskit_ibm_runtime.fake_provider import FakeKingston

        _backend = FakeKingston()
    return _backend


def dt_seconds() -> float:
    return float(getattr(_be(), "dt", DT_NS * 1e-9))


def transpile_alap(qc):
    """A beküldő áramkörök időzítése: opt0, fix initial_layout, ALAP, seedelt."""
    from qiskit import transpile

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return transpile(
            qc,
            backend=_be(),
            initial_layout=list(LAYOUT),
            optimization_level=0,
            scheduling_method="alap",
            seed_transpiler=SEED_TRANSPILER,
        )


def alap_duration_dt(qc) -> int:
    tqc = transpile_alap(qc)
    secs = float(tqc.estimate_duration(_be().target))
    return int(round(secs / dt_seconds()))


# ---------------------------------------------------------------------------
# Karhossz-kiegyenlítés (v1.3, 4. pont)
# ---------------------------------------------------------------------------
_n3_ref_cache: dict[tuple[str, str | None, int], int] = {}
_target_cache: dict[tuple[str, str | None, int], int] = {}
_arm_dur_cache: dict[tuple[str, int, str, str | None, float], int] = {}


def n3_reference_dt(branch: str, init: str | None, k: int) -> int:
    """Az n3 kar ALAP-hossza dt-ben, coupling_scale=1.0 mellett.

    Ez a TERV SZERINTI referencia-kar; a tényleges közös cél-idő:
    lásd ``equalization_target_dt``.
    """
    key = (branch, init, int(k))
    if key not in _n3_ref_cache:
        from .circuits import build_arm_circuit

        qc = build_arm_circuit("n3", k, branch, init, coupling_scale=1.0, measure=True, idle_pad_dt=0)
        _n3_ref_cache[key] = alap_duration_dt(qc)
    return _n3_ref_cache[key]


def equalization_target_dt(branch: str, init: str | None, k: int) -> int:
    """A közös cél-idő dt-ben minden (branch, init, k) csoportra.

    Az n3 a természetes referencia (a leghosszabb szimmetrikus kar minden
    k>0-ra a mérések szerint), KIVÉVE a population/init="0" csoportban, ahol a
    ``noisy`` kar horgony-H szintézise minden k-ra pontosan 8 dt-vel (1 sx,
    32 ns) hosszabb az n3-nál. A leghosszabb kart utólag nem lehet rövidebbre
    húzni (csak üres várakozás szúrható be), ezért a közös cél-idő ott a
    ``noisy`` hossza — a hosszekvivalencia így minden karban minden k-ra
    teljesül (|Δ| ≤ 1 dt), a v1.3 4. pontjának megfelelően.
    """
    key = (branch, init, int(k))
    if key not in _target_cache:
        ref = n3_reference_dt(branch, init, k)
        longest = ref
        for arm in config.ARM_NAMES:
            longest = max(longest, arm_duration_dt(arm, k, branch, init, 1.0))
        _target_cache[key] = int(longest)
    return _target_cache[key]


def arm_duration_dt(arm: str, k: int, branch: str, init: str | None, coupling_scale: float) -> int:
    key = (arm, int(k), branch, init, float(coupling_scale))
    if key not in _arm_dur_cache:
        from .circuits import build_arm_circuit

        qc = build_arm_circuit(arm, k, branch, init, coupling_scale=coupling_scale, measure=True, idle_pad_dt=0)
        _arm_dur_cache[key] = alap_duration_dt(qc)
    return _arm_dur_cache[key]


def idle_pad_dt(arm: str, k: int, branch: str, init: str | None, coupling_scale: float = 1.0) -> int:
    """Üres várakozás (dt), amellyel a kar ALAP-hossza a közös cél-időre nő.

    A cél-idő a scale=1.0-s karok maximumából adódik (alapból az n3; a
    population/init="0" csoportban a noisy-é, amely 8 dt-vel hosszabb);
    a csatolások-kikapcsolva kontroll (scale=0.0) is ugyanezt az abszolút
    célidőt kapja — ez a kontroll őszinteségének feltétele.
    """
    ref = equalization_target_dt(branch, init, k)
    dur = arm_duration_dt(arm, k, branch, init, coupling_scale)
    pad = ref - dur
    if pad < 0:
        raise RuntimeError(
            f"karhossz-kiegyenlítés: a kar hosszabb a cél-időnél: {arm} k={k} {branch} {init} "
            f"scale={coupling_scale}: {dur} dt > {ref} dt — ÁLLJ MEG és jelentsd."
        )
    return int(pad)


def equalized_arm_circuit(
    arm: str,
    k: int,
    branch: str,
    init: str | None,
    coupling_scale: float = 1.0,
    measure: bool = True,
):
    """Az áramkör üres várakozással kiegyenlítve az n3 (scale=1.0) hosszára."""
    from .circuits import build_arm_circuit

    pad = idle_pad_dt(arm, k, branch, init, coupling_scale)
    return build_arm_circuit(
        arm, k, branch, init, coupling_scale=coupling_scale, measure=measure, idle_pad_dt=pad
    )


def equalization_report(ks=None) -> tuple[list[dict], int]:
    """Minden kart kiegyenlít és transpile+ALAP után ellenőrzi az |Δhossz| ≤ 1 dt kaput.

    Visszaad: (sorok listája, maximális abszolút eltérés dt-ben).
    """
    if ks is None:
        ks = range(config.K + 1)
    rows: list[dict] = []
    max_abs = 0
    for k in ks:
        for branch, init in (("population", "0"), ("population", "1"), ("coherence", None)):
            ref = equalization_target_dt(branch, init, k)
            ref_n3 = n3_reference_dt(branch, init, k)
            for arm in config.ARM_NAMES:
                for scale in (1.0, 0.0):
                    qc = equalized_arm_circuit(arm, k, branch, init, scale, measure=True)
                    d = alap_duration_dt(qc)
                    delta = int(d) - int(ref)
                    max_abs = max(max_abs, abs(delta))
                    rows.append(
                        {
                            "arm": arm,
                            "branch": branch,
                            "init": init,
                            "k": int(k),
                            "coupling_scale": float(scale),
                            "target_dt": int(ref),
                            "n3_ref_dt": int(ref_n3),
                            "arm_dt": int(d),
                            "delta_dt": int(delta),
                            "delta_vs_n3_dt": int(int(d) - int(ref_n3)),
                        }
                    )
    return rows, int(max_abs)


# ---------------------------------------------------------------------------
# Routolt, helyi (4-qubitos) Aer-valószínűségek
# ---------------------------------------------------------------------------
_branch_init_groups = (("population", "0"), ("population", "1"), ("coherence", None))


def _routed_slice(arm: str, k: int, branch: str, init: str | None, coupling_scale: float):
    """A transpile+ALAP áramkör S–Ai qubitjeire kivágott, helyi 4q áramkör.

    - a delay-ek dt-ben maradnak (a helyi szimuláció identityként kezeli őket);
    - a mérés kimarad (a valószínűség a density matrixból jön, a kiolvasási
      hibát analitikusan vetítjük rá).
    """
    from qiskit import QuantumCircuit

    from .circuits import build_arm_circuit

    pad = idle_pad_dt(arm, k, branch, init, coupling_scale)
    qc = build_arm_circuit(
        arm, k, branch, init, coupling_scale=coupling_scale, measure=False, idle_pad_dt=pad
    )
    tqc = transpile_alap(qc)
    local = QuantumCircuit(len(LAYOUT), name=f"slice_{qc.name}")
    for instr in tqc.data:
        op = instr.operation
        name = op.name
        if name == "measure":
            continue
        bit_idxs = [tqc.find_bit(q).index for q in instr.qubits]
        if not set(bit_idxs) <= set(PHYS_TO_LOCAL):
            # ALAP által minden eszköz-qubitre tett kitöltő delay-ek az
            # S–Ai qubiten kívül — a helyi áramkörnek nincs rájuk szüksége
            if any(b in PHYS_TO_LOCAL for b in bit_idxs):
                raise RuntimeError(
                    f"a routed kör instrukciója részben az S–Ai qubitekre nyúlik: {name!r} {bit_idxs}"
                )
            continue
        idxs = [PHYS_TO_LOCAL[b] for b in bit_idxs]
        params = op.params
        if name == "delay":
            # dt-ben őrizzük meg a kerek-egész várakozást
            local.delay(op.duration, idxs, unit=op.unit)
        elif name == "cz":
            local.cz(idxs[0], idxs[1])
        elif name == "rz":
            local.rz(params[0], idxs[0])
        elif name == "sx":
            local.sx(idxs[0])
        elif name == "x":
            local.x(idxs[0])
        elif name == "id":
            local.id(idxs[0])
        elif name == "h":
            local.h(idxs[0])
        else:
            raise RuntimeError(f"ismeretlen, nem kivágható instrukció a routed körből: {name!r}")
    return local, pad


@lru_cache(maxsize=1)
def build_local_noise_model():
    """A FakeKingston-kalibrációból épített helyi zajmodell (4 qubit).

    sx/x/cz: termál relaxáció (T1, T2 a kapuidőre) ∘ depolarizáló(target-hiba);
    rz: zajtalan (virtuális); delay: zajtalan (lásd modul-docstring korlátok);
    readout: analitikusan a valószínűségekre vetítve (lásd routed_probabilities).
    """
    from qiskit_aer.noise import NoiseModel, depolarizing_error, thermal_relaxation_error

    be = _be()
    props = be.properties()
    target = be.target
    nm = NoiseModel()
    dt = dt_seconds()

    def _t_err(q: int, dur_s: float, err: float, n: int):
        t1, t2 = props.t1(q), props.t2(q)
        therm = thermal_relaxation_error(t1, t2, max(float(dur_s), 1e-12))
        if err and err > 0.0:
            return therm.compose(depolarizing_error(float(err), n))
        return therm

    # 1Q: sx és x (dur 3.2e-8 s), rz (dur 0, err 0 — zajtalan marad)
    for q in LAYOUT:
        l = PHYS_TO_LOCAL[q]
        one_q = target["sx"][(q,)]
        dur_1q = float(one_q.duration)
        e_sx = float(one_q.error or 0.0)
        e_x = float(target["x"][(q,)].error or 0.0)
        nm.add_quantum_error(_t_err(q, dur_1q, e_sx, 1), ["sx"], [l])
        nm.add_quantum_error(_t_err(q, dur_1q, e_x, 1), ["x"], [l])
        # 'id' kitöltők (ha a routed kör megtartaná őket): ugyanaz a 1q ablak
        try:
            e_id = float(target["id"][(q,)].error or 0.0)
            nm.add_quantum_error(_t_err(q, dur_1q, e_id, 1), ["id"], [l])
        except Exception:
            pass

    # 2Q: cz, irányfüggetlen átlóként (a target páronként ad hibát)
    for pair in CZ_PAIRS:
        q0, q1 = pair
        lpair = (PHYS_TO_LOCAL[q0], PHYS_TO_LOCAL[q1])
        inst = target["cz"][(q0, q1)]
        dur_2q = float(inst.duration)
        e_cz = float(inst.error or 0.0)
        therm_pair = thermal_relaxation_error(
            props.t1(q0), props.t2(q0), dur_2q
        ).tensor(thermal_relaxation_error(props.t1(q1), props.t2(q1), dur_2q))
        if e_cz and e_cz > 0.0:
            therm_pair = therm_pair.compose(depolarizing_error(e_cz, 2))
        nm.add_quantum_error(therm_pair, ["cz"], list(lpair))

    return nm


def readout_error_s() -> float:
    """Az S (fizikai 125) kiolvasási hibának szimmetrikus közelítése a targetből."""
    be = _be()
    return float(be.target["measure"][(125,)].error or 0.0)


_prob_cache: dict[tuple[str, int, str, str | None, float], tuple[float, float]] = {}


def routed_probabilities(
    arm: str, k: int, branch: str, init: str | None, coupling_scale: float = 1.0
) -> tuple[float, float]:
    """P(S=0), P(S=1) a routed+ALAP-időzített, helyi FakeKingston-zajos Aer-density_matrixból.

    A kiolvasási hiba analitikusan vetül rá (szimmetrikus modell):
    p1_obs = p1*(1-e) + (1-p1)*e.
    """
    key = (arm, int(k), branch, init, float(coupling_scale))
    if key in _prob_cache:
        return _prob_cache[key]

    from qiskit_aer import AerSimulator
    from qiskit.quantum_info import DensityMatrix

    local, _pad = _routed_slice(arm, k, branch, init, coupling_scale)
    nm = build_local_noise_model()
    local.save_density_matrix()
    sim = AerSimulator(method="density_matrix", noise_model=nm)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = sim.run(local, shots=1).result()
    dm = DensityMatrix(result.data(0)["density_matrix"])
    probs = dm.probabilities(qargs=[0])
    p0, p1 = float(probs[0]), float(probs[1])
    e = readout_error_s()
    p1_obs = p1 * (1.0 - e) + (1.0 - p1) * e
    out = (float(1.0 - p1_obs), float(p1_obs))
    _prob_cache[key] = out
    return out


def sweep_routed_probabilities(coupling_scale: float, ks=None) -> dict:
    """sweep_exact-séma szerinti kimenet — az összes karra és ágra, k-ra."""
    if ks is None:
        ks = range(config.K + 1)
    out: dict[str, dict] = {}
    for arm in config.ARM_NAMES:
        out[arm] = {"population": {i: [] for i in config.POP_INITS}, "coherence": {config.COH_INIT: []}}
        for k in ks:
            for init in config.POP_INITS:
                p0, p1 = routed_probabilities(arm, k, config.BRANCH_POPULATION, init, coupling_scale)
                out[arm]["population"][init].append({"p0": p0, "p1": p1})
            p0, p1 = routed_probabilities(arm, k, config.BRANCH_COHERENCE, None, coupling_scale)
            out[arm]["coherence"][config.COH_INIT].append({"p0": p0, "p1": p1})
    return out
