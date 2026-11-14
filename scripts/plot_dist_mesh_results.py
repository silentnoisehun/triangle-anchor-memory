#!/usr/bin/env python3
"""scripts/plot_dist_mesh_results.py — Elosztott Memória Hálózat hardver eredmények ábrázolása."""
from __future__ import annotations

import json
from pathlib import Path
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = REPO_ROOT / "data" / "dist_mesh_raw_counts.json"
OUT_DIR = REPO_ROOT / "docs" / "img"
OUT_DIR.mkdir(parents=True, exist_ok=True)

with open(DATA_PATH, "r", encoding="utf-8") as f:
    obs = json.load(f)

ks = [8, 12, 16, 20, 24, 28, 32]

plt.style.use("dark_background")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=300)

# Panel 1: Mindhárom leválasztott szatellit mag populációja
p1 = [obs["hold_mesh"][str(k)]["P_S1"] for k in ks]
p2 = [obs["hold_mesh"][str(k)]["P_S2"] for k in ks]
p3 = [obs["hold_mesh"][str(k)]["P_S3"] for k in ks]

ax1.plot(ks, p1, label="Decoupled NW Cell S1 (Q105)", color="#00E5FF", lw=2.6, marker="o", markersize=7)
ax1.plot(ks, p2, label="Decoupled NE Cell S2 (Q127)", color="#76FF03", lw=2.6, marker="s", markersize=7)
ax1.plot(ks, p3, label="Decoupled S Cell S3 (Q123)", color="#E040FB", lw=2.6, marker="^", markersize=7)

ax1.axvline(x=8, color="#FFEA00", linestyle="--", alpha=0.75, label="Global Decoupling (k=8)")
ax1.set_title("3 Decoupled Autonomous Cells: Local Hub Retention", fontsize=13, fontweight="bold", pad=12)
ax1.set_xlabel("Evolution Rounds (k)", fontsize=11)
ax1.set_ylabel("Hub Excitation Probability P(S_i = 1)", fontsize=11)
ax1.grid(True, linestyle="--", alpha=0.3)
ax1.legend(loc="upper right", framealpha=0.85)

ax1.annotate(
    "Balanced Autonomous Storage\nS1≈39.1%, S2≈27.5%, S3≈30.9%",
    xy=(32, p1[-1]),
    xytext=(16, 0.44),
    arrowprops=dict(facecolor="#00E5FF", edgecolor="none", shrink=0.08, width=1.5, headwidth=6),
    fontsize=9.5,
    fontweight="bold",
    color="#00E5FF",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#1e1e1e", edgecolor="#00E5FF", alpha=0.85),
)

# Panel 2: Kollektív elosztott megtartás vs idle
psat_hold = [obs["hold_mesh"][str(k)]["P_sat"] for k in ks]
psat_idle = [obs["hold_idle"][str(k)]["P_sat"] for k in ks]
psat_cont = [obs["continuous"][str(k)]["P_sat"] for k in ks]

ax2.plot(ks, psat_hold, label="Decoupled Autonomous Mesh P(sat)", color="#00E5FF", lw=3.0, marker="o", markersize=8)
ax2.plot(ks, psat_cont, label="Continuously Driven P(sat)", color="#76FF03", lw=2.2, marker="s", ls="--", markersize=7)
ax2.plot(ks, psat_idle, label="Idle Delay (Bare Transmon Decay)", color="#FF1744", lw=2.4, marker="x", ls=":", markersize=8)

ax2.axvline(x=8, color="#FFEA00", linestyle="--", alpha=0.75, label="Global Decoupling (k=8)")
ax2.set_title("Distributed Network Collective Retention", fontsize=13, fontweight="bold", pad=12)
ax2.set_xlabel("Evolution Rounds (k)", fontsize=11)
ax2.set_ylabel("Collective Satellite Retention P(sat)", fontsize=11)
ax2.grid(True, linestyle="--", alpha=0.3)
ax2.legend(loc="lower left", framealpha=0.85)

ax2.annotate(
    "Protection Advantage\n+26.2% vs Idle Decay",
    xy=(32, psat_hold[-1]),
    xytext=(20, 0.76),
    arrowprops=dict(facecolor="#00E5FF", edgecolor="none", shrink=0.08, width=1.5, headwidth=6),
    fontsize=10,
    fontweight="bold",
    color="#00E5FF",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#1e1e1e", edgecolor="#00E5FF", alpha=0.85),
)

fig.suptitle("IBM Heron r2 (ibm_marrakesh) — Distributed Autonomous Quantum Memory Network", fontsize=15, fontweight="bold", y=0.98)
plt.tight_layout()

png_path = OUT_DIR / "dist_mesh_hardware_retention.png"
svg_path = OUT_DIR / "dist_mesh_hardware_retention.svg"
plt.savefig(png_path, dpi=300, bbox_inches="tight")
plt.savefig(svg_path, format="svg", bbox_inches="tight")
plt.close()

print(f"[OK] Mentve: {png_path}")
