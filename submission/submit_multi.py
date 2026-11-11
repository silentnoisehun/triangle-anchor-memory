#!/usr/bin/env python3
"""Haromszog-horgony 1. fazis bekuldes (Control Agent). Tobb jobba vagva,
mert a backend max_experiments=300 < 757. A token csak kornyezetbol jon.
Ez a 2026-11-11-i (20:52 UTC) futas bekuldoje (/tmp/tri kornyezetben futott); a repoban
valtozatlanul, referencia-kent orizzuk; ujrafuttatashoz a /tmp/tri utvonalakat a helyi klon gyokerehez kell igazitani."""
import json, os, sys, hashlib
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/tmp/tri")
os.chdir("/tmp/tri")
token = os.environ.get("IBM_QUANTUM_TOKEN")
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
from src.run import select_backend_and_layout, build_snapshot, write_snapshot_atomic, all_job_circuits, canonical_payload_sha256, SNAPSHOT_PATH
from src import config

service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
backend, selection = select_backend_and_layout(service)
chosen = selection["chosen"]
layout = {"S": int(chosen["S"]), "A1": int(chosen["anchors"][0]),
          "A2": int(chosen["anchors"][1]), "A3": int(chosen["anchors"][2])}
print("layout:", layout, "backend:", backend.name)

snapshot = build_snapshot(backend, selection)
write_snapshot_atomic(snapshot)
print("snapshot mentve")

items = all_job_circuits(layout, backend)
print("aramkorok osszesen:", len(items))
payload = canonical_payload_sha256(items)

CHUNK = 250
sampler = SamplerV2(mode=backend)
job_ids = []
chunks = []
submitted_at = datetime.now(timezone.utc).isoformat()
for ci in range(0, len(items), CHUNK):
    part = items[ci:ci + CHUNK]
    job = sampler.run([qc for _, qc in part], shots=config.SHOTS)
    jid = job.job_id()
    job_ids.append(jid)
    chunks.append({"job_id": jid, "from": ci, "to": ci + len(part)})
    print(f"chunk {len(job_ids)}: {jid}  [{ci}:{ci+len(part)}]", flush=True)

meta = {
    "job_ids": job_ids,
    "chunks": chunks,
    "backend": backend.name,
    "channel": "ibm_quantum_platform",
    "submitted_at": submitted_at,
    "shots": config.SHOTS,
    "circuit_count": len(items),
    "layout": layout,
    "selection": selection,
    "shuffle_seed": 20261111,
    "order": [cid for cid, _ in items],
    "payload_sha256": payload,
    "snapshot_file": "data/snapshot.json",
    "snapshot_sha256": hashlib.sha256(SNAPSHOT_PATH.read_bytes()).hexdigest(),
    "note": "A backend max_experiments=300 korlatja miatt 4 egymas utani job, azonos munkamenetben, azonos beallitasokkal. A kalibracio az elso job elejen fut.",
}
Path("data/job_meta.json").write_text(json.dumps(meta, indent=2))
print("job_meta mentve. JOB IDS:", job_ids)
