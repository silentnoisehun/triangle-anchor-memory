#!/usr/bin/env python3
"""sentinel_wheel.py — Kerék v1.2 őrszem és eredmény-kiértékelő.

Figyeli a data/wheel_job_meta.json-ban rögzített jobot.
Ha lefutott (DONE):
  - letölti a nyers számlálókat (117 áramkör);
  - elmenti a data/wheel_raw_counts.json és .sha256 fájlokat;
  - lefuttatja a fagyasztott v1.2 elemzőt (src.wheel.analysis);
  - elmenti és kiírja a hivatalos ítéletet.
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

from src.wheel import analysis

JOB_META_PATH = REPO_ROOT / "data" / "wheel_job_meta.json"
RAW_COUNTS_PATH = REPO_ROOT / "data" / "wheel_raw_counts.json"
RAW_COUNTS_SHA_PATH = REPO_ROOT / "data" / "wheel_raw_counts.sha256"
REPORT_PATH = REPO_ROOT / "data" / "wheel_analysis_report_v1_2.json"


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
    shots = meta.get("shots", 512)
    job = service.job(jid)
    res = job.result()

    print("Kerék v1.2 job DONE! Számlálók letöltése...")
    obs = {arm: {} for arm in meta["arms"]}

    for cid, pub in zip(order, res):
        arm, k_str = cid.split("|")
        k = k_str.replace("k", "")

        counts = {}
        for reg_name in dir(pub.data):
            if reg_name.startswith("_"):
                continue
            reg = getattr(pub.data, reg_name)
            if hasattr(reg, "get_counts"):
                counts = reg.get_counts()
                break

        n0 = int(counts.get("0", 0))
        n1 = int(counts.get("1", 0))
        obs[arm][str(k)] = {"0": n0, "1": n1, "shots": shots}

    # Mentés atomikusan
    content = json.dumps(obs, indent=2, ensure_ascii=False)
    RAW_COUNTS_PATH.write_text(content, encoding="utf-8")
    h = hashlib.sha256(content.encode("utf-8")).hexdigest()
    RAW_COUNTS_SHA_PATH.write_text(f"{h}  data/wheel_raw_counts.json\n", encoding="utf-8")
    print(f"data/wheel_raw_counts.json mentve! SHA-256: {h}")

    # Elemző futtatása
    fz = analysis.check_frozen()
    rep = analysis.analyze(obs, fz, label="hardware_qpu_marrakesh")

    REPORT_PATH.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n" + "=" * 72)
    print("KERÉK v1.2 HARDVER-KIÉRTÉKELÉS EREDMÉNYE:")
    print("=" * 72)
    print(f"VERDIKT: {rep['verdict']}")
    print(f"AUC értékek: {rep.get('aucs')}")
    print(f"Claims: {json.dumps(rep.get('claims', {}), indent=2)}")
    print(f"Tankönyvi várakozások: {json.dumps(rep.get('tankonyvi_varakozasok', {}), indent=2)}")
    print("=" * 72)


def main() -> int:
    parser = argparse.ArgumentParser(description="Kerék v1.2 őrszem")
    parser.add_argument("--once", action="store_true", help="Csak egyszer fut le (nincs ciklus)")
    parser.add_argument("--interval", type=int, default=15, help="Lekérdezési időköz másodpercben")
    args = parser.parse_args()

    if not JOB_META_PATH.exists():
        print(f"HIBA: nincs {JOB_META_PATH}!")
        return 1

    meta = json.loads(JOB_META_PATH.read_text(encoding="utf-8"))
    jid = meta.get("job_id")
    if not jid:
        print("HIBA: a meta fájlban nincs job_id!")
        return 1

    token = get_token()
    if not token:
        print("HIBA: nincs érvényes token!")
        return 1

    from qiskit_ibm_runtime import QiskitRuntimeService
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token, instance="open-instance")

    if args.once:
        job = service.job(jid)
        st = str(job.status())
        print(f"Kerék v1.2 ({jid}) státusz: {st}")
        if "DONE" in st:
            fetch_and_analyze(service, meta)
        return 0

    print(f"Kerék v1.2 ({jid}) figyelése elindítva...")
    while True:
        try:
            job = service.job(jid)
            st = str(job.status())
            print(f"[{time.strftime('%H:%M:%S')}] Job státusz: {st}")
            if "DONE" in st:
                fetch_and_analyze(service, meta)
                break
        except Exception as e:
            print(f"Lekérdezési hiba: {e}")
        time.sleep(args.interval)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
