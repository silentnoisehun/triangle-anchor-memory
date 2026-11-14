#!/usr/bin/env python3
"""sentinel_ring.py — Gyűrű v1.2 őrszem és eredmény-kiértékelő.

Figyeli a data/ring_job_meta.json-ban rögzített jobot:
  'dbrsvnfv5hds73di9fp0'

Ha lefutott (DONE):
  - letölti a nyers számlálókat;
  - elmenti a data/ring_raw_counts.json és .sha256 fájlokat;
  - lefuttatja a fagyasztott v1.2 elemzőt (src.ring.analysis).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.ring import analysis

JOB_META_PATH = REPO_ROOT / "data" / "ring_job_meta.json"
RAW_COUNTS_PATH = REPO_ROOT / "data" / "ring_raw_counts.json"
RAW_COUNTS_SHA_PATH = REPO_ROOT / "data" / "ring_raw_counts.sha256"


def get_token() -> str:
    token = os.environ.get("IBM_QUANTUM_TOKEN")
    if token:
        return token
    for candidate in [
        Path("c:/Users/mater/Downloads/apikey (2) (1).json"),
        Path("c:/Users/mater/Downloads/apikey (2) (2).json"),
        Path("c:/Users/mater/Downloads/apikey (1) (1).json"),
    ]:
        if candidate.exists():
            with candidate.open("r", encoding="utf-8") as f:
                d = json.load(f)
                t = d.get("apikey") or d.get("token")
                if t:
                    return t
    return ""


def fetch_and_analyze(service, meta: dict) -> None:
    jid = meta["job_id"]
    order = meta["order"]
    job = service.job(jid)
    res = job.result()

    print("Gyűrű job DONE! Számlálók letöltése...")
    obs = {}
    for cid, pub in zip(order, res):
        arm, k_str = cid.split("|")
        k = k_str.replace("k", "")
        if arm not in obs:
            obs[arm] = {}

        counts = {}
        for reg_name in dir(pub.data):
            if reg_name.startswith("_"):
                continue
            reg = getattr(pub.data, reg_name)
            if hasattr(reg, "get_counts"):
                counts = reg.get_counts()
                break

        tot = sum(counts.values())
        n000 = counts.get("000", 0)
        obs[arm][k] = {"000": n000, "shots": tot}

    payload = {"meta": meta, "obs": obs}
    content = json.dumps(payload, indent=2, ensure_ascii=False)
    RAW_COUNTS_PATH.write_text(content, encoding="utf-8")
    h = hashlib.sha256(content.encode("utf-8")).hexdigest()
    RAW_COUNTS_SHA_PATH.write_text(f"{h}  data/ring_raw_counts.json\n", encoding="utf-8")
    print(f"data/ring_raw_counts.json mentve! SHA-256: {h}")

    # Elemzés a fagyasztott paraméterekkel
    fz = analysis.check_frozen()
    rep = analysis.compare(obs, fz, label="hardware_qpu_kingston", model="routed")
    print("\n" + "=" * 72)
    print("GYŰRŰ v1.2 HARDVER-KIÉRTÉKELÉS EREDMÉNYE:")
    print("=" * 72)
    print(f"VERDIKT: {rep['verdict']}")
    print(f"Indoklás / részletek: {rep.get('verdict_reason', 'n/a')}")
    print("=" * 72)


def main():
    if not JOB_META_PATH.exists():
        print("HIBA: nincs data/ring_job_meta.json!")
        return 1

    meta = json.loads(JOB_META_PATH.read_text(encoding="utf-8"))
    jid = meta.get("job_id")
    token = get_token()

    from qiskit_ibm_runtime import QiskitRuntimeService
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token, instance="open-instance")

    job = service.job(jid)
    st = str(job.status())
    print(f"Gyűrű v1.2 ({jid}) státusz: {st}")

    if st in ("JobStatus.DONE", "DONE"):
        fetch_and_analyze(service, meta)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
