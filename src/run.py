"""QPU-beküldő — MINDEN AUDIT ELŐTT TILOS FUTTATNI.

A QPU-beküldést a Control Agent végzi a tulajdonos rövid életű tokenjével
(terv 1. fázis). Ez a fájl CSISZOLAT, amelyet a beküldés előtt auditálni kell.

Kemény szabályok (a terv 7. pontjából, változatlanul):
- A tokent KIZÁRÓLAG az IBM_QUANTUM_TOKEN környezeti változóból olvassa;
  semmilyen fájlba, sehova nem kerül token.
- A jobok sorrendje sorsolt (shuffle), a seed és a teljes sorrend a
  data/job_meta.json-ba kerül a beküldés PILLANATÁBAN (külön a lekérdezéstől).
- A job_id csak a job_meta.json-ba íródik; commit-üzenetbe nem kerül.
- A beküldés után a job_meta.json SOHA nem írandó újra.
- A nyers counts azonnal mentendő (data/raw_counts.json) és SHA-256-hash-elendő.

Ennek a fájlnak a futtatása ebben a fázisban TILOS — a feladat része, hogy
létrehozzuk és auditálhatóvá tegyük, de QPU-jobot NE indítson el senki
beszámolás/audit nélkül.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from . import config
from .circuits import build_arm_circuit

REPO_ROOT = Path(__file__).resolve().parents[1]
JOB_META_PATH = REPO_ROOT / "data" / "job_meta.json"
RAW_COUNTS_PATH = REPO_ROOT / "data" / "raw_counts.json"

SHUFFLE_SEED = 20261111  # a 1. fázis jobjának rögzített sorsolás-seedje (a job_meta tartalmazza)


def planned_circuits():
    """Az 1. fázis összes áramköre kanonikus sorrendben (594 db), azonosítóval együtt."""
    items = []
    for arm in config.ARM_NAMES:
        for k in range(config.K + 1):
            for init in config.POP_INITS:
                cid = f"{arm}|population|{init}|k{k}"
                items.append((cid, build_arm_circuit(arm, k, config.BRANCH_POPULATION, init)))
        for k in range(config.K + 1):
            cid = f"{arm}|coherence|+|k{k}"
            items.append((cid, build_arm_circuit(arm, k, config.BRANCH_COHERENCE)))
    return items


def shuffled_order(items, seed: int):
    """Determinista, seedelt sorsolás — az eredeti lista másolatát rendezi újra."""
    import random

    order = list(items)
    random.Random(seed).shuffle(order)
    return order


def canonical_payload_sha256(items) -> str:
    """A körök sorrendjében vett, kanonikus OpenQASM 3 reprezentáció SHA-256-ja."""
    from qiskit import qasm3  # lokális import — csak a beküldési útvonal igényli

    digest = hashlib.sha256()
    for cid, qc in items:
        digest.update(cid.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(qasm3.dumps(qc).encode("utf-8"))
        digest.update(b"\x00")
    return digest.hexdigest()


def write_job_meta_atomic(meta: dict, path: Path = JOB_META_PATH) -> None:
    """job_meta.json atomikusan (tmp + rename) — NEM írható újra."""
    if path.exists():
        raise RuntimeError(
            f"{path} már létezik — a job_meta.json a beküldés pillanatában jön létre, és SOHA nem írható újra."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
        tmp = Path(f.name)
    os.replace(tmp, path)


def submit() -> int:
    token = os.environ.get("IBM_QUANTUM_TOKEN")
    if not token:
        print(
            "LEÁLL: nincs IBM_QUANTUM_TOKEN a környezeti változókban.\n"
            "A token sosem kerül fájlba; a Control Agent a tulajdonos rövid életű\n"
            "tokenjével indítja a jobokat (terv, 1. és 7. fejezet)."
        )
        return 2
    shots = int(os.environ.get("IBM_QUANTUM_SHOTS", str(config.SHOTS)))

    items = planned_circuits()
    order = shuffled_order(items, SHUFFLE_SEED)
    payload_sha256 = canonical_payload_sha256(order)

    try:
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2  # lazy — auditálandó import
    except ImportError as exc:
        print(f"LEÁLL: a qiskit-ibm-runtime csomag nem érhető el ({exc}). A 0. fázishoz nem kell.")
        return 2

    # AUDITÁLANDÓ: a szolgáltatás/csatorna neve a qiskit-ibm-runtime aktuális
    # verziójától függ; a beküldés előtt ellenőrizni kell a Control Agentnek.
    service = QiskitRuntimeService(channel="ibm_quantum", token=token)
    backend_name = os.environ.get("IBM_QUANTUM_BACKEND", "ibm_heron")
    backend = service.backend(backend_name)

    circuit_ids = [cid for cid, _ in order]
    circuits = [qc for _, qc in order]
    sampler = SamplerV2(mode=backend)

    submitted_at = datetime.now(timezone.utc).isoformat()
    job = sampler.run(circuits, shots=shots)

    meta = {
        "job_id": job.job_id(),
        "backend": backend_name,
        "submitted_at": submitted_at,
        "shots": shots,
        "circuit_count": len(circuits),
        "shuffle_seed": SHUFFLE_SEED,
        "order": circuit_ids,
        "payload_sha256": payload_sha256,
        "note": "A job_id a beküldés pillanatában került ide; a lekérdezés külön lépés (fázis 2).",
    }
    write_job_meta_atomic(meta)
    print(f"Job elküldve. job_meta.json mentve ide: {JOB_META_PATH}")
    print("A nyers counts-ot a befejeződés után a fetch_raw_counts() menti és hash-eli.")
    return 0


def fetch_raw_counts(job_id: str) -> int:
    """A nyers counts mentése és hash-elése (fázis 1 vége) — a Control Agent futtatja."""
    token = os.environ.get("IBM_QUANTUM_TOKEN")
    if not token:
        print("LEÁLL: nincs IBM_QUANTUM_TOKEN a környezetben.")
        return 2
    if not JOB_META_PATH.exists():
        print(f"LEÁLL: nincs {JOB_META_PATH} — előbb a beküldés pillanatában kell létrejönnie.")
        return 2
    meta = json.loads(JOB_META_PATH.read_text(encoding="utf-8"))
    if meta.get("job_id") != job_id:
        print("LEÁLL: a megadott job_id nem egyezik a job_meta.json-nal — nem másoljuk rá az adatokat.")
        return 2

    try:
        from qiskit_ibm_runtime import QiskitRuntimeService  # lazy import
    except ImportError as exc:
        print(f"LEÁLL: a qiskit-ibm-runtime csomag nem érhető el ({exc}).")
        return 2

    service = QiskitRuntimeService(channel="ibm_quantum", token=token)
    job = service.job(job_id)
    result = job.result()

    # AUDITÁLANDÓ: a SamplerV2 eredmény-szerkezet kulcsai (kör-sorrendben) itt
    # nyers counts-szá kell alakítandók; a Control Agentnek a futtatás előtt
    # ellenőriznie kell, hogy az `order`-rel azonos sorrendben olvassa ki.
    dataset = {
        "meta": meta,
        "shots": meta.get("shots"),
        "population": {arm: {i: {} for i in config.POP_INITS} for arm in config.ARM_NAMES},
        "coherence": {arm: {config.COH_INIT: {}} for arm in config.ARM_NAMES},
        "note": "ELŐÁLLÍTÁS: audit alatt; a counts-ok kör-sorrendben (order) kerülnek kiolvasásra.",
    }
    with RAW_COUNTS_PATH.open("w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    digest = hashlib.sha256(RAW_COUNTS_PATH.read_bytes()).hexdigest()
    print(f"nyers counts mentve: {RAW_COUNTS_PATH}\nSHA-256: {digest}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--fetch":
        if len(sys.argv) != 3:
            print("használat: python -m src.run --fetch <job_id>")
            raise SystemExit(2)
        raise SystemExit(fetch_raw_counts(sys.argv[2]))
    raise SystemExit(submit())
