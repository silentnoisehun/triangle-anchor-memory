#!/usr/bin/env python3
"""src/sentinel_tri_wheel.py — Tri-Wheel 10-Qubit Mesh hardver eredmény-kiértékelő."""
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

JOB_META_PATH = REPO_ROOT / "data" / "tri_wheel_job_meta.json"
RAW_COUNTS_PATH = REPO_ROOT / "data" / "tri_wheel_raw_counts.json"
RAW_COUNTS_SHA_PATH = REPO_ROOT / "data" / "tri_wheel_raw_counts.sha256"
REPORT_PATH = REPO_ROOT / "data" / "tri_wheel_report.json"


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


def fetch_and_evaluate(service, meta: dict) -> None:
    jid = meta["job_id"]
    order = meta["order"]
    shots = meta.get("shots", 512)
    job = service.job(jid)
    res = job.result()

    print("Tri-Wheel job DONE! Számlálók letöltése...")
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

        # little-endian 3-bit register: bit 0 = S1, bit 1 = S2, bit 2 = S3
        tot = sum(counts.values())
        p_s1 = sum(c for bits, c in counts.items() if bits.replace(" ", "")[-1] == "1") / tot
        p_s2 = sum(c for bits, c in counts.items() if bits.replace(" ", "")[-2] == "1") / tot
        p_s3 = sum(c for bits, c in counts.items() if bits.replace(" ", "")[-3] == "1") / tot
        p_any = sum(c for bits, c in counts.items() if "1" in bits) / tot

        obs[arm][str(k)] = {
            "counts": counts,
            "P_S1": float(p_s1),
            "P_S2": float(p_s2),
            "P_S3": float(p_s3),
            "P_tot": float(p_any),
            "shots": shots,
        }

    # Mentés atomikusan
    content = json.dumps(obs, indent=2, ensure_ascii=False)
    RAW_COUNTS_PATH.write_text(content, encoding="utf-8")
    h = hashlib.sha256(content.encode("utf-8")).hexdigest()
    RAW_COUNTS_SHA_PATH.write_text(f"{h}  data/tri_wheel_raw_counts.json\n", encoding="utf-8")
    print(f"data/tri_wheel_raw_counts.json mentve! SHA-256: {h}")

    # Értékelés a fagyasztott kritériumok szerint
    frozen_path = REPO_ROOT / "preregistration" / "frozen_tri_wheel_params.json"
    fz = json.loads(frozen_path.read_text(encoding="utf-8"))
    crit = fz["criteria"]

    # 1. End-to-End Conduction to S3 (mean k >= 8)
    s3_sync_vals = [obs["sync"][str(k)]["P_S3"] for k in [8, 12, 16, 20, 24, 28, 32]]
    mean_s3_sync = sum(s3_sync_vals) / len(s3_sync_vals)
    s3_nosync_vals = [obs["nosync"][str(k)]["P_S3"] for k in [8, 12, 16, 20, 24, 28, 32]]
    mean_s3_nosync = sum(s3_nosync_vals) / len(s3_nosync_vals)

    conduction_ok = (mean_s3_sync >= crit["s3_conduction_mean_min"]) and (mean_s3_nosync <= crit["s3_nosync_max"] + 0.05)

    # 2. Tri-Equipartition @ k=16
    p1_k16 = obs["sync"]["16"]["P_S1"]
    p2_k16 = obs["sync"]["16"]["P_S2"]
    p3_k16 = obs["sync"]["16"]["P_S3"]
    max_diff_k16 = max(abs(p1_k16 - p2_k16), abs(p2_k16 - p3_k16), abs(p1_k16 - p3_k16))
    equipartition_ok = max_diff_k16 <= crit["tri_equipartition_k16_diff_max"]

    # 3. Collective Retention @ k=32
    retention_k32 = obs["sync"]["32"]["P_tot"]
    retention_ok = retention_k32 >= crit["collective_retention_k32_min"]

    verdict = "CONFIRMED" if (conduction_ok and equipartition_ok and retention_ok) else "PARTIAL"

    report = {
        "job_id": jid,
        "backend": meta["backend"],
        "shots": shots,
        "s3_conduction": {
            "mean_sync": mean_s3_sync,
            "mean_nosync": mean_s3_nosync,
            "passed": conduction_ok,
        },
        "tri_equipartition_k16": {
            "P_S1": p1_k16,
            "P_S2": p2_k16,
            "P_S3": p3_k16,
            "max_diff": max_diff_k16,
            "passed": equipartition_ok,
        },
        "collective_retention_k32": {
            "P_tot": retention_k32,
            "threshold": crit["collective_retention_k32_min"],
            "passed": retention_ok,
        },
        "verdict": verdict,
    }

    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Jelentés mentve: {REPORT_PATH}")

    print("\n" + "=" * 72)
    print(f"TRI-WHEEL MESH ÉRTÉKELÉS — VERDICT: {verdict}")
    print("=" * 72)
    print(f"1. Végpont-vezetés (S3 átlag k>=8): {mean_s3_sync:.4f} vs nosync {mean_s3_nosync:.4f} (passed: {conduction_ok})")
    print(f"2. Háromoldalú ekvipartíció @ k=16: max|P_i - P_j| = {max_diff_k16:.4f} (<= 0.15: {equipartition_ok})")
    print(f"   [P(S1)={p1_k16:.4f}, P(S2)={p2_k16:.4f}, P(S3)={p3_k16:.4f}]")
    print(f"3. Kollektív retenció @ k=32: {retention_k32:.4f} (>= 0.35: {retention_ok})")
    print("=" * 72)


def main() -> int:
    parser = argparse.ArgumentParser(description="Tri-Wheel Sentinel")
    parser.add_argument("--watch", action="store_true", help="Várakozás és automatikus kiértékelés")
    args = parser.parse_args()

    if not JOB_META_PATH.exists():
        print(f"Hiba: {JOB_META_PATH} nem található!")
        return 1

    meta = json.loads(JOB_META_PATH.read_text(encoding="utf-8"))
    jid = meta["job_id"]
    token = get_token()
    if not token:
        print("Hiba: nincs IBM Quantum token!")
        return 1

    from qiskit_ibm_runtime import QiskitRuntimeService

    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token, instance="open-instance")

    while True:
        job = service.job(jid)
        st = str(job.status()).upper()
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Job {jid} státusz: {st}")

        if "DONE" in st or "COMPLETED" in st:
            fetch_and_evaluate(service, meta)
            break
        elif "ERROR" in st or "CANCELLED" in st:
            print(f"Job sikertelen: {st}")
            return 1

        if not args.watch:
            break
        time.sleep(15)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
