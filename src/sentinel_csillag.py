#!/usr/bin/env python3
"""sentinel_csillag.py — Őrszem szkript a Csillag v1.4 QPU jobok figyelésére és letöltésére.

Figyeli a data/job_meta.json-ban rögzített 4 chunk jobot:
  ['dbrsud8k09pc73avfm1g', 'dbrsue0k09pc73avfm40', 'dbrsuepabdes73fqfmu0', 'dbrsuf1abdes73fqfmug']

Ha mind a 4 lefutott (DONE):
  - letölti a pub számlálókat;
  - összeállítja a data/raw_counts.json fájlt a specifikáció szerint;
  - kiszámítja és elmenti a data/raw_counts.sha256-ot;
  - automatikusan lefuttatja a fagyasztott elemzőt (src.analysis).
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

from src import config

JOB_META_PATH = REPO_ROOT / "data" / "job_meta.json"
RAW_COUNTS_PATH = REPO_ROOT / "data" / "raw_counts.json"
RAW_COUNTS_SHA_PATH = REPO_ROOT / "data" / "raw_counts.sha256"


def get_token() -> str:
    token = os.environ.get("IBM_QUANTUM_TOKEN")
    if token:
        return token
    key_file = Path("c:/Users/mater/Downloads/apikey (1) (1).json")
    if key_file.exists():
        with key_file.open("r", encoding="utf-8") as f:
            d = json.load(f)
            t = d.get("apikey")
            if t:
                return t
    return ""


def check_status_only(service, job_ids: list[str]) -> bool:
    all_done = True
    print("-" * 60)
    for i, jid in enumerate(job_ids):
        try:
            job = service.job(jid)
            st = str(job.status())
            pos = job.queue_position() if hasattr(job, "queue_position") else None
            pos_str = f" (sorpozíció: {pos})" if pos is not None else ""
            print(f"Chunk {i+1}/4 ({jid}): {st}{pos_str}")
            if st != "JobStatus.DONE" and st != "DONE":
                all_done = False
        except Exception as e:
            print(f"Chunk {i+1}/4 ({jid}): Lekérdezési hiba ({e})")
            all_done = False
    print("-" * 60)
    return all_done


def fetch_and_save(service, meta: dict) -> None:
    job_ids = meta["job_ids"]
    order = meta["order"]
    shots = meta.get("shots", config.SHOTS)

    print("Minden job DONE! Számlálók letöltése és összerendezése...")
    all_pub_results = []
    for i, jid in enumerate(job_ids):
        print(f"Letöltés: chunk {i+1}/{len(job_ids)} ({jid})...", flush=True)
        job = service.job(jid)
        res = job.result()
        for pub in res:
            all_pub_results.append(pub)

    if len(all_pub_results) != len(order):
        raise RuntimeError(f"Eltérés a letöltött pubok ({len(all_pub_results)}) és a várt sorrend ({len(order)}) között!")

    dataset = {
        "meta": meta,
        "shots": shots,
        "population": {arm: {init: {} for init in config.POP_INITS} for arm in config.ARM_NAMES},
        "coherence": {arm: {config.COH_INIT: {}} for arm in config.ARM_NAMES},
        "calibration": {},
    }

    for cid, pub in zip(order, all_pub_results):
        # SamplerV2 pub bit array counts extraction
        # A legtöbb SamplerV2 output pub.data.meas.get_counts() vagy pub.data.c.get_counts()
        counts = {}
        for reg_name in dir(pub.data):
            if reg_name.startswith("_"):
                continue
            reg = getattr(pub.data, reg_name)
            if hasattr(reg, "get_counts"):
                counts = reg.get_counts()
                break

        # Besorolás a struktúrába
        if cid.startswith("t1|") or cid.startswith("t2|") or cid.startswith("ro|") or cid.startswith("phi_eff|"):
            dataset["calibration"][cid] = counts
        elif "|population|" in cid:
            parts = cid.split("|")
            arm, _, init, k_part = parts[0], parts[1], parts[2], parts[3]
            k_val = k_part.replace("k", "")
            dataset["population"][arm][init][k_val] = counts
        elif "|coherence|" in cid:
            parts = cid.split("|")
            arm, _, init, k_part = parts[0], parts[1], parts[2], parts[3]
            k_val = k_part.replace("k", "")
            dataset["coherence"][arm][init][k_val] = counts

    # Mentés atomi módon
    content = json.dumps(dataset, indent=2, ensure_ascii=False)
    RAW_COUNTS_PATH.write_text(content, encoding="utf-8")
    h = hashlib.sha256(content.encode("utf-8")).hexdigest()
    RAW_COUNTS_SHA_PATH.write_text(f"{h}  data/raw_counts.json\n", encoding="utf-8")
    print(f"data/raw_counts.json mentve! SHA-256: {h}")

    # Fagyasztott elemző futtatása
    print("\n" + "=" * 72)
    print("FAGYASZTOTT ELEMZŐ INDÍTÁSA A HARDVER-ADATOKRA...")
    print("=" * 72)
    from src.analysis import main as run_analysis
    run_analysis()


def main():
    parser = argparse.ArgumentParser(description="Őrszem — Csillag v1.4 QPU státusz és adatletöltő")
    parser.add_argument("--watch", action="store_true", help="Folyamatos figyelés amíg le nem fut")
    parser.add_argument("--interval", type=int, default=60, help="Lekérdezési időköz másodpercben (alapértelmezett: 60s)")
    args = parser.parse_args()

    if not JOB_META_PATH.exists():
        print("HIBA: nincs data/job_meta.json!")
        return 1

    meta = json.loads(JOB_META_PATH.read_text(encoding="utf-8"))
    job_ids = meta.get("job_ids", [])
    if not job_ids:
        print("HIBA: a data/job_meta.json nem tartalmaz job_id-kat!")
        return 1

    token = get_token()
    if not token:
        print("HIBA: nincs érvényes IBM Quantum token!")
        return 1

    from qiskit_ibm_runtime import QiskitRuntimeService
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token, instance="open-instance")

    print(f"triangle-anchor-memory — CSILLAG v1.4 ŐRSZEM")
    print(f"Backend: {meta.get('backend')}, Jobok száma: {len(job_ids)}")

    if not args.watch:
        check_status_only(service, job_ids)
        return 0

    print("Folyamatos figyelés elindítva (Ctrl+C-vel megszakítható)...")
    while True:
        all_done = check_status_only(service, job_ids)
        if all_done:
            fetch_and_save(service, meta)
            break
        time.sleep(args.interval)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
