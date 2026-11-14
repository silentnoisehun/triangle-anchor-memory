#!/usr/bin/env python3
"""src/sentinel_dual_wheel.py — Dual-Wheel Mesh hardver eredmény-kiértékelő."""
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

JOB_META_PATH = REPO_ROOT / "data" / "dual_wheel_job_meta.json"
RAW_COUNTS_PATH = REPO_ROOT / "data" / "dual_wheel_raw_counts.json"
RAW_COUNTS_SHA_PATH = REPO_ROOT / "data" / "dual_wheel_raw_counts.sha256"
REPORT_PATH = REPO_ROOT / "data" / "dual_wheel_report.json"


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

    print("Dual-Wheel job DONE! Számlálók letöltése...")
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

        # little-endian 2-bit register: bit 0 = S1, bit 1 = S2
        tot = sum(counts.values())
        p_s1 = sum(c for bits, c in counts.items() if bits.replace(" ", "")[-1] == "1") / tot
        p_s2 = sum(c for bits, c in counts.items() if bits.replace(" ", "")[-2] == "1") / tot
        p_any = sum(c for bits, c in counts.items() if "1" in bits) / tot

        obs[arm][str(k)] = {
            "counts": counts,
            "P_S1": float(p_s1),
            "P_S2": float(p_s2),
            "P_tot": float(p_any),
            "shots": shots,
        }

    # Mentés atomikusan
    content = json.dumps(obs, indent=2, ensure_ascii=False)
    RAW_COUNTS_PATH.write_text(content, encoding="utf-8")
    h = hashlib.sha256(content.encode("utf-8")).hexdigest()
    RAW_COUNTS_SHA_PATH.write_text(f"{h}  data/dual_wheel_raw_counts.json\n", encoding="utf-8")
    print(f"data/dual_wheel_raw_counts.json mentve! SHA-256: {h}")

    # Értékelés a fagyasztott kritériumok szerint
    frozen_path = REPO_ROOT / "preregistration" / "frozen_dual_wheel_params.json"
    fz = json.loads(frozen_path.read_text(encoding="utf-8"))

    # 1. Sync Conduction
    s2_vals = [obs["sync"][str(k)]["P_S2"] for k in [4, 8, 12, 16, 20, 24, 28, 32]]
    conduction_ok = all(v >= 0.10 for v in s2_vals)
    mean_s2_sync = sum(s2_vals) / len(s2_vals)

    # 2. Equipartition @ k=8
    p_s1_k8 = obs["sync"]["8"]["P_S1"]
    p_s2_k8 = obs["sync"]["8"]["P_S2"]
    diff_k8 = abs(p_s1_k8 - p_s2_k8)
    equipartition_ok = diff_k8 <= fz["predictions"]["equipartition_k8_diff_threshold"]

    # 3. Collective Retention @ k=32
    retention_k32 = obs["sync"]["32"]["P_tot"]
    retention_ok = retention_k32 >= 0.35

    report = {
        "job_id": jid,
        "backend": meta["backend"],
        "mean_s2_sync_k4_to_32": mean_s2_sync,
        "conduction_check": bool(conduction_ok),
        "equipartition_diff_k8": diff_k8,
        "equipartition_check": bool(equipartition_ok),
        "retention_k32": retention_k32,
        "retention_check": bool(retention_ok),
        "verdict": "CONFIRMED" if (conduction_ok and equipartition_ok and retention_ok) else "PARTIAL",
        "obs": obs,
    }

    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n" + "=" * 72)
    print("DUAL-WHEEL MESH HARDVER KIÉRTÉKELÉS:")
    print("=" * 72)
    print(f"VERDIKT: {report['verdict']}")
    print(f"1. Koherens Átfolyás (S2 átlag): {mean_s2_sync:.4f} (Elvárt: >= 0.15, Check: {conduction_ok})")
    print(f"2. Szinkron Ekvipartíció @ k=8: |P(S1)-P(S2)| = {diff_k8:.4f} (Elvárt: <= 0.15, Check: {equipartition_ok})")
    print(f"3. Kollektív Háló-Retenció @ k=32: {retention_k32:.4f} (Elvárt: >= 0.35, Check: {retention_ok})")
    print("=" * 72)


def main() -> int:
    parser = argparse.ArgumentParser(description="Dual-Wheel őrszem")
    parser.add_argument("--once", action="store_true", help="Csak egyszeri lekérdezés")
    args = parser.parse_args()

    if not JOB_META_PATH.exists():
        print("HIBA: nincs job_meta.json!")
        return 1

    meta = json.loads(JOB_META_PATH.read_text(encoding="utf-8"))
    jid = meta.get("job_id")
    token = get_token()

    from qiskit_ibm_runtime import QiskitRuntimeService
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token, instance="open-instance")

    job = service.job(jid)
    st = str(job.status())
    print(f"Dual-Wheel Job ({jid}) státusz: {st}")
    if "DONE" in st:
        fetch_and_evaluate(service, meta)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
