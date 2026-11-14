#!/usr/bin/env python3
"""scripts/plot_decouple_results.py — Pump-and-Decouple hardver eredmények ábrázolása.

Generálja a docs/img/decouple_hardware_retention.png ábrát:
  - hold_wheel2 (autonóm tárolás) vs hold_idle (tétlen relaxáció) vs continuous (folyamatos szinkron)
  - Heron r2 ibm_marrakesh hardver adatokból
"""
from __future__ import annotations

import json
from pathlib import Path
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = REPO_ROOT / "data" / "dual_wheel_decouple_raw_counts.json"
OUT_DIR = REPO_ROOT / "docs" / "img"
OUT_DIR.mkdir(parents=True, exist_ok=True)

with open(DATA_PATH, "r", encoding="utf-8") as f:
    obs = json.load(f)

ks = [8, 12, 16, 20, 24, 28, 32]

plt.style.use("dark_background")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=300)

# 1. Panel: P(S2) a vevő kerék központján
p_s2_wheel2 = [obs["hold_wheel2"][str(k)]["P_S2"] for k in ks]
p_s2_idle = [obs["hold_idle"][str(k)]["P_S2"] for k in ks]
p_s2_cont = [obs["continuous"][str(k)]["P_S2"] for k in ks]

ax1.plot(ks, p_s2_wheel2, label="Decoupled Hold (Wheel 2 Loop Active)", color="#00E5FF", lw=2.8, marker="o", markersize=8)
ax1.plot(ks, p_s2_cont, label="Continuous Sync (Fully Driven)", color="#76FF03", lw=2.2, marker="s", ls="--", markersize=7)
ax1.plot(ks, p_s2_idle, label="Idle Delay (Bare Transmon Decay)", color="#FF1744", lw=2.2, marker="^", ls=":", markersize=7)

ax1.axvline(x=8, color="#FFEA00", linestyle="--", alpha=0.7, label="Decoupling Point (k=8)")
ax1.set_title("Receiver Hub P(S2) Population", fontsize=13, fontweight="bold", pad=12)
ax1.set_xlabel("Evolution Rounds (k)", fontsize=11)
ax1.set_ylabel("Excitation Probability P(S2=1)", fontsize=11)
ax1.grid(True, linestyle="--", alpha=0.3)
ax1.legend(loc="upper right", framealpha=0.8)

# Highlight difference at k=32
ax1.annotate(
    f"Protection Advantage\n+15.6% vs Idle",
    xy=(32, p_s2_wheel2[-1]),
    xytext=(24, 0.20),
    arrowprops=dict(facecolor="#00E5FF", edgecolor="none", shrink=0.08, width=1.5, headwidth=6),
    fontsize=10,
    fontweight="bold",
    color="#00E5FF",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#1e1e1e", edgecolor="#00E5FF", alpha=0.8),
)

# 2. Panel: Teljes kollektív populáció P_tot = P(S1 v S2)
p_tot_wheel2 = [obs["hold_wheel2"][str(k)]["P_tot"] for k in ks]
p_tot_idle = [obs["hold_idle"][str(k)]["P_tot"] for k in ks]
p_tot_cont = [obs["continuous"][str(k)]["P_tot"] for k in ks]

ax2.plot(ks, p_tot_wheel2, label="Decoupled Hold P(tot)", color="#00E5FF", lw=2.8, marker="o", markersize=8)
ax2.plot(ks, p_tot_cont, label="Continuous Sync P(tot)", color="#76FF03", lw=2.2, marker="s", ls="--", markersize=7)
ax2.plot(ks, p_tot_idle, label="Idle Delay P(tot)", color="#FF1744", lw=2.2, marker="^", ls=":", markersize=7)

ax2.axvline(x=8, color="#FFEA00", linestyle="--", alpha=0.7, label="Decoupling Point (k=8)")
ax2.set_title("Collective Retention P(S1 or S2)", fontsize=13, fontweight="bold", pad=12)
ax2.set_xlabel("Evolution Rounds (k)", fontsize=11)
ax2.set_ylabel("Collective Probability P(tot)", fontsize=11)
ax2.grid(True, linestyle="--", alpha=0.3)
ax2.legend(loc="upper right", framealpha=0.8)

fig.suptitle("IBM Heron r2 (ibm_marrakesh) — Quantum DRAM Pump-and-Decouple Verification", fontsize=15, fontweight="bold", y=0.98)
plt.tight_layout()

png_path = OUT_DIR / "decouple_hardware_retention.png"
svg_path = OUT_DIR / "decouple_hardware_retention.svg"
plt.savefig(png_path, dpi=300, bbox_inches="tight")
plt.savefig(svg_path, format="svg", bbox_inches="tight")
plt.close()

print(f"[OK] Mentve: {png_path} és {svg_path}")
