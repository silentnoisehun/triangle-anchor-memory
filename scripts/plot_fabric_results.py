#!/usr/bin/env python3
"""scripts/plot_fabric_results.py — 13-Qubites 2D Tér-Szövet hardver eredmények ábrázolása."""
from __future__ import annotations

import json
from pathlib import Path
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = REPO_ROOT / "data" / "fabric_13q_raw_counts.json"
OUT_DIR = REPO_ROOT / "docs" / "img"
OUT_DIR.mkdir(parents=True, exist_ok=True)

with open(DATA_PATH, "r", encoding="utf-8") as f:
    obs = json.load(f)

ks = [0, 4, 8, 12, 16, 20, 24, 28, 32]

plt.style.use("dark_background")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=300)

p0 = [obs["sync"][str(k)]["P_S0"] for k in ks]
p1 = [obs["sync"][str(k)]["P_S1"] for k in ks]
p2 = [obs["sync"][str(k)]["P_S2"] for k in ks]
p3 = [obs["sync"][str(k)]["P_S3"] for k in ks]

ax1.plot(ks, p0, label="Master Center S0 (Q125)", color="#FFD600", lw=2.8, marker="o", markersize=8)
ax1.plot(ks, p1, label="Satellite NW S1 (Q105)", color="#00E5FF", lw=2.4, marker="s", markersize=7)
ax1.plot(ks, p2, label="Satellite NE S2 (Q127)", color="#76FF03", lw=2.4, marker="^", markersize=7)
ax1.plot(ks, p3, label="Satellite S S3 (Q123)", color="#E040FB", lw=2.4, marker="d", markersize=7)

ax1.set_title("2D Omni-Directional 4-Hub Equipartition", fontsize=13, fontweight="bold", pad=12)
ax1.set_xlabel("Evolution Rounds (k)", fontsize=11)
ax1.set_ylabel("Hub Excitation P(S_i = 1)", fontsize=11)
ax1.grid(True, linestyle="--", alpha=0.3)
ax1.legend(loc="upper right", framealpha=0.85)

# Annotation for 4-way balance
ax1.annotate(
    "2D Macroscopic Equipartition\nS0≈47.5%, S1≈32.2%, S2≈30.9%, S3≈31.1%",
    xy=(32, p0[-1]),
    xytext=(12, 0.55),
    arrowprops=dict(facecolor="#FFD600", edgecolor="none", shrink=0.08, width=1.5, headwidth=6),
    fontsize=9.5,
    fontweight="bold",
    color="#FFD600",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#1e1e1e", edgecolor="#FFD600", alpha=0.85),
)

ptot_sync = [obs["sync"][str(k)]["P_tot"] for k in ks]
ptot_nosync = [obs["nosync"][str(k)]["P_tot"] for k in ks]

ax2.plot(ks, ptot_sync, label="2D Fabric Collective Retention P(tot)", color="#00E5FF", lw=3.0, marker="o", markersize=8)
ax2.plot(ks, ptot_nosync, label="Isolated Center P(tot)", color="#FF1744", lw=2.2, marker="x", ls="--", markersize=7)

ax2.set_title("13-Qubit Fabric Collective Bound State", fontsize=13, fontweight="bold", pad=12)
ax2.set_xlabel("Evolution Rounds (k)", fontsize=11)
ax2.set_ylabel("Collective Retention P(tot)", fontsize=11)
ax2.grid(True, linestyle="--", alpha=0.3)
ax2.legend(loc="lower right", framealpha=0.85)

ax2.annotate(
    "83.4% Collective Retention\nat k=32 (~200 physical gates)",
    xy=(32, ptot_sync[-1]),
    xytext=(14, 0.40),
    arrowprops=dict(facecolor="#00E5FF", edgecolor="none", shrink=0.08, width=1.5, headwidth=6),
    fontsize=9.5,
    fontweight="bold",
    color="#00E5FF",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#1e1e1e", edgecolor="#00E5FF", alpha=0.85),
)

fig.suptitle("IBM Heron r2 (ibm_marrakesh) — 13-Qubit 2D Quantum Space-Fabric", fontsize=15, fontweight="bold", y=0.98)
plt.tight_layout()

png_path = OUT_DIR / "fabric_13q_hardware_plateau.png"
svg_path = OUT_DIR / "fabric_13q_hardware_plateau.svg"
plt.savefig(png_path, dpi=300, bbox_inches="tight")
plt.savefig(svg_path, format="svg", bbox_inches="tight")
plt.close()

print(f"[OK] Mentve: {png_path}")
