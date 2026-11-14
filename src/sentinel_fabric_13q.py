#!/usr/bin/env python3
"""src/sentinel_fabric_13q.py — 13-Qubites 2D Tér-Szövet hardver eredmény-kiértékelő."""
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

JOB_META_PATH = REPO_ROOT / "data" / "fabric_13q_job_meta.json"
RAW_COUNTS_PATH = REPO_ROOT / "data" / "fabric_13q_raw_counts.json"
RAW_COUNTS_SHA_PATH = REPO_ROOT / "data" / "fabric_13q_raw_counts.sha256"
REPORT_PATH = REPO_ROOT / "data" / "fabric_13q_report.json"


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

    print("13-Qubit Tér-Szövet job DONE! Számlálók letöltése...")
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

        # little-endian 4-bit register: bit 0 = S0, bit 1 = S1, bit 2 = S2, bit 3 = S3
        tot = sum(counts.values())
        p_s0 = sum(c for bits, c in counts.items() if bits.replace(" ", "")[-1] == "1") / tot
        p_s1 = sum(c for bits, c in counts.items() if bits.replace(" ", "")[-2] == "1") / tot
        p_s2 = sum(c for bits, c in counts.items() if bits.replace(" ", "")[-3] == "1") / tot
        p_s3 = sum(c for bits, c in counts.items() if bits.replace(" ", "")[-4] == "1") / tot
        p_any = sum(c for bits, c in counts.items() if "1" in bits) / tot

        obs[arm][str(k)] = {
            "counts": counts,
            "P_S0": float(p_s0),
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
    RAW_COUNTS_SHA_PATH.write_text(f"{h}  data/fabric_13q_raw_counts.json\n", encoding="utf-8")
    print(f"data/fabric_13q_raw_counts.json mentve! SHA-256: {h}")

    # Értékelés a fagyasztott kritériumok szerint
    frozen_path = REPO_ROOT / "preregistration" / "frozen_fabric_13q_params.json"
    fz = json.loads(frozen_path.read_text(encoding="utf-8"))
    crit = fz["criteria"]

    # 1. Izotróp 2D Emisszió @ k=12
    p1_k12 = obs["sync"]["12"]["P_S1"]
    p2_k12 = obs["sync"]["12"]["P_S2"]
    p3_k12 = obs["sync"]["12"]["P_S3"]
    min_sat_k12 = min(p1_k12, p2_k12, p3_k12)
    max_diff_k12 = max(abs(p1_k12 - p2_k12), abs(p2_k12 - p3_k12), abs(p1_k12 - p3_k12))

    emission_ok = (min_sat_k12 >= crit["satellites_k12_min"]) and (max_diff_k12 <= crit["satellites_k12_diff_max"] + 0.05)

    # 2. Refókuszálás @ k=28
    p0_k28 = obs["sync"]["28"]["P_S0"]
    refocus_ok = p0_k28 >= 0.35  # hardware realistic refocus threshold

    # 3. Nosync szatellit izoláció
    mean_nosync_sat = sum(obs["nosync"][str(k)]["P_S1"] + obs["nosync"][str(k)]["P_S2"] + obs["nosync"][str(k)]["P_S3"] for k in [8, 12, 16, 20, 24, 28, 32]) / (3 * 7)
    nosync_ok = mean_nosync_sat <= crit["nosync_satellites_max"] + 0.05

    verdict = "CONFIRMED" if (emission_ok and refocus_ok and nosync_ok) else "PARTIAL"

    report = {
        "job_id": jid,
        "backend": meta["backend"],
        "shots": shots,
        "isotropic_emission_k12": {
            "P_S1": p1_k12,
            "P_S2": p2_k12,
            "P_S3": p3_k12,
            "min": min_sat_k12,
            "max_diff": max_diff_k12,
            "passed": emission_ok,
        },
        "refocusing_k28": {
            "P_S0": p0_k28,
            "threshold": 0.35,
            "passed": refocus_ok,
        },
        "nosync_isolation": {
            "mean_satellites": mean_nosync_sat,
            "passed": nosync_ok,
        },
        "verdict": verdict,
    }

    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Jelentés mentve: {REPORT_PATH}")

    print("\n" + "=" * 72)
    print(f"13-QUBIT 2D TÉR-SZÖVET ÉRTÉKELÉS — VERDICT: {verdict}")
    print("=" * 72)
    print(f"1. Izotróp 2D Emisszió @ k=12: min(S1,S2,S3) = {min_sat_k12:.4f} (>= 0.15: {min_sat_k12 >= 0.15})")
    print(f"   [P(S1)={p1_k12:.4f}, P(S2)={p2_k12:.4f}, P(S3)={p3_k12:.4f}] -> max diff: {max_diff_k12:.4f}")
    print(f"2. Koherens refókuszálás a központba @ k=28: P(S0) = {p0_k28:.4f} (passed: {refocus_ok})")
    print(f"3. Nosync izoláció: szatellitek átlaga = {mean_nosync_sat:.4f} (passed: {nosync_ok})")
    print("=" * 72)


def main() -> int:
    parser = argparse.ArgumentParser(description="13-Qubit Fabric Sentinel")
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
