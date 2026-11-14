#!/usr/bin/env python3
"""scripts/plot_tri_wheel_results.py — 10-qubites Tri-Wheel Mesh hardver eredmények ábrázolása.

Generálja a docs/img/tri_wheel_hardware_conduction.png és .svg ábrákat:
  - S1 (Adó 105), S2 (Relé 125), S3 (Vevő 123) népességek időfejlődése
  - Sync vs Nosync kontroll összehasonlítás
  - 10-qubites kollektív megtartás
"""
from __future__ import annotations

import json
from pathlib import Path
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = REPO_ROOT / "data" / "tri_wheel_raw_counts.json"
OUT_DIR = REPO_ROOT / "docs" / "img"
OUT_DIR.mkdir(parents=True, exist_ok=True)

with open(DATA_PATH, "r", encoding="utf-8") as f:
    obs = json.load(f)

ks = [0, 4, 8, 12, 16, 20, 24, 28, 32]

plt.style.use("dark_background")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=300)

# 1. Panel: Mindhárom mag populációja a Kvantum-Buszon (Sync)
p_s1_sync = [obs["sync"][str(k)]["P_S1"] for k in ks]
p_s2_sync = [obs["sync"][str(k)]["P_S2"] for k in ks]
p_s3_sync = [obs["sync"][str(k)]["P_S3"] for k in ks]
p_s3_nosync = [obs["nosync"][str(k)]["P_S3"] for k in ks]

ax1.plot(ks, p_s1_sync, label="Hub S1 (Transmitter Q105)", color="#FFD600", lw=2.6, marker="o", markersize=7)
ax1.plot(ks, p_s2_sync, label="Hub S2 (Relay Q125)", color="#00E5FF", lw=2.6, marker="s", markersize=7)
ax1.plot(ks, p_s3_sync, label="Hub S3 (Receiver Q123)", color="#76FF03", lw=2.8, marker="^", markersize=8)
ax1.plot(ks, p_s3_nosync, label="Receiver S3 (Nosync Control)", color="#FF1744", lw=2.0, marker="x", ls=":", markersize=7)

ax1.set_title("3-Way Quantum Bus Conduction & Equipartition", fontsize=13, fontweight="bold", pad=12)
ax1.set_xlabel("Evolution Rounds (k)", fontsize=11)
ax1.set_ylabel("Excitation Probability P(S_i = 1)", fontsize=11)
ax1.grid(True, linestyle="--", alpha=0.3)
ax1.legend(loc="upper right", framealpha=0.85)

# Annotation for equipartition @ k=16
ax1.annotate(
    "3-Way Equipartition\nS1≈35.9%, S2≈25.2%, S3≈30.5%",
    xy=(16, p_s3_sync[4]),
    xytext=(10, 0.48),
    arrowprops=dict(facecolor="#76FF03", edgecolor="none", shrink=0.08, width=1.5, headwidth=6),
    fontsize=9.5,
    fontweight="bold",
    color="#76FF03",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#1e1e1e", edgecolor="#76FF03", alpha=0.85),
)

# 2. Panel: Kollektív 10-qubites populáció
p_tot_sync = [obs["sync"][str(k)]["P_tot"] for k in ks]
p_tot_nosync = [obs["nosync"][str(k)]["P_tot"] for k in ks]

ax2.plot(ks, p_tot_sync, label="Sync Bus Collective P(tot)", color="#00E5FF", lw=2.8, marker="o", markersize=8)
ax2.plot(ks, p_tot_nosync, label="Nosync Isolated P(tot)", color="#FF1744", lw=2.2, marker="s", ls="--", markersize=7)

ax2.set_title("10-Qubit Mesh Collective Retention", fontsize=13, fontweight="bold", pad=12)
ax2.set_xlabel("Evolution Rounds (k)", fontsize=11)
ax2.set_ylabel("Collective Retention P(S1 v S2 v S3)", fontsize=11)
ax2.grid(True, linestyle="--", alpha=0.3)
ax2.legend(loc="upper right", framealpha=0.85)

# Highlight k=32
ax2.annotate(
    f"67.0% Collective Retention\nat k=32 (~200 physical gates)",
    xy=(32, p_tot_sync[-1]),
    xytext=(16, 0.50),
    arrowprops=dict(facecolor="#00E5FF", edgecolor="none", shrink=0.08, width=1.5, headwidth=6),
    fontsize=9.5,
    fontweight="bold",
    color="#00E5FF",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#1e1e1e", edgecolor="#00E5FF", alpha=0.85),
)

fig.suptitle("IBM Heron r2 (ibm_marrakesh) — 10-Qubit Tri-Wheel Quantum Bus Verification", fontsize=15, fontweight="bold", y=0.98)
plt.tight_layout()

png_path = OUT_DIR / "tri_wheel_hardware_conduction.png"
svg_path = OUT_DIR / "tri_wheel_hardware_conduction.svg"
plt.savefig(png_path, dpi=300, bbox_inches="tight")
plt.savefig(svg_path, format="svg", bbox_inches="tight")
plt.close()

print(f"[OK] Mentve: {png_path} és {svg_path}")
