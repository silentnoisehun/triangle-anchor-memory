#!/usr/bin/env python3
"""src/sentinel_dual_wheel_decouple.py — Pump-and-Decouple hardver eredmény-kiértékelő."""
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

JOB_META_PATH = REPO_ROOT / "data" / "dual_wheel_decouple_job_meta.json"
RAW_COUNTS_PATH = REPO_ROOT / "data" / "dual_wheel_decouple_raw_counts.json"
RAW_COUNTS_SHA_PATH = REPO_ROOT / "data" / "dual_wheel_decouple_raw_counts.sha256"
REPORT_PATH = REPO_ROOT / "data" / "dual_wheel_decouple_report.json"


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

    print("Pump-and-Decouple job DONE! Számlálók letöltése...")
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
    RAW_COUNTS_SHA_PATH.write_text(f"{h}  data/dual_wheel_decouple_raw_counts.json\n", encoding="utf-8")
    print(f"data/dual_wheel_decouple_raw_counts.json mentve! SHA-256: {h}")

    # Értékelés a fagyasztott kritériumok szerint
    frozen_path = REPO_ROOT / "preregistration" / "frozen_dual_wheel_decouple_params.json"
    fz = json.loads(frozen_path.read_text(encoding="utf-8"))
    crit = fz["criteria"]

    # 1. Handover Equipartition @ k=8
    p_s1_k8 = obs["hold_wheel2"]["8"]["P_S1"]
    p_s2_k8 = obs["hold_wheel2"]["8"]["P_S2"]
    diff_k8 = abs(p_s1_k8 - p_s2_k8)
    handover_ok = (diff_k8 <= crit["handover_equipartition_k8_diff_max"]) and (p_s2_k8 >= crit["handover_s2_min"])

    # 2. Decoupled Retention @ k=32
    s2_k32_hold = obs["hold_wheel2"]["32"]["P_S2"]
    hold_ok = s2_k32_hold >= crit["hold_wheel2_s2_k32_min"]

    # 3. Protection Advantage vs Idle @ k=32
    s2_k32_idle = obs["hold_idle"]["32"]["P_S2"]
    delta_protection = s2_k32_hold - s2_k32_idle
    protection_ok = delta_protection >= crit["protection_advantage_k32_min"]

    verdict = "CONFIRMED" if (handover_ok and hold_ok and protection_ok) else "PARTIAL"

    report = {
        "job_id": jid,
        "backend": meta["backend"],
        "shots": shots,
        "handover_k8": {
            "P_S1": p_s1_k8,
            "P_S2": p_s2_k8,
            "diff": diff_k8,
            "passed": handover_ok,
        },
        "hold_wheel2_k32": {
            "P_S2": s2_k32_hold,
            "threshold": crit["hold_wheel2_s2_k32_min"],
            "passed": hold_ok,
        },
        "protection_advantage_k32": {
            "hold_wheel2": s2_k32_hold,
            "hold_idle": s2_k32_idle,
            "delta": delta_protection,
            "threshold": crit["protection_advantage_k32_min"],
            "passed": protection_ok,
        },
        "verdict": verdict,
    }

    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Jelentés mentve: {REPORT_PATH}")

    print("\n" + "=" * 72)
    print(f"PUMP-AND-DECOUPLE ÉRTÉKELÉS — VERDICT: {verdict}")
    print("=" * 72)
    print(f"1. Kézfogás (k=8 átadás): |P(S1)-P(S2)| = {diff_k8:.4f} (<= 0.15: {handover_ok}), P(S2) = {p_s2_k8:.4f} (>= 0.20: {p_s2_k8 >= 0.20})")
    print(f"2. Autonóm retenció (k=32 S2): {s2_k32_hold:.4f} (>= 0.25: {hold_ok})")
    print(f"3. Védelem előny az üresjárathoz képest: Delta = {delta_protection:+.4f} (>= +0.05: {protection_ok})")
    print(f"   [hold_wheel2: {s2_k32_hold:.4f} vs hold_idle: {s2_k32_idle:.4f}]")
    print("=" * 72)


def main() -> int:
    parser = argparse.ArgumentParser(description="Pump-and-Decouple Sentinel")
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
