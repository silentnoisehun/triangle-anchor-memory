#!/usr/bin/env python3
"""scripts/plot_wheel_results.py — Kerék v1.2 hardver-eredmények grafikonja.

Generálja a docs/img/wheel_hardware_retention.png és .svg ábrákat:
  - Wheel vs Ring-Only vs Static vs Alone vs Alone-DD összehasonlítás
  - Z = 13.63 szignifikancia feltüntetése
  - Heron r2 ibm_marrakesh hardver-adatokból
"""
from __future__ import annotations

import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = REPO_ROOT / "data" / "wheel_raw_counts.json"
OUT_DIR = REPO_ROOT / "docs" / "img"
OUT_DIR.mkdir(parents=True, exist_ok=True)

with open(DATA_PATH, "r", encoding="utf-8") as f:
    obs = json.load(f)

arms_to_plot = {
    "wheel": {"label": "Wheel (Closed-Loop Anchored)", "color": "#00E5FF", "lw": 2.8, "marker": "o", "zorder": 5},
    "static": {"label": "Static (Flux OFF)", "color": "#76FF03", "lw": 2.0, "marker": "s", "zorder": 4},
    "ring_only": {"label": "Ring Only (No Spokes / Unanchored)", "color": "#FF1744", "lw": 2.2, "marker": "^", "ls": "--", "zorder": 4},
    "alone": {"label": "Alone (Unprotected Center)", "color": "#FF9100", "lw": 1.8, "marker": "x", "ls": ":", "zorder": 3},
    "alone_DD": {"label": "Alone + DD (Dynamical Decoupling)", "color": "#D500F9", "lw": 2.0, "marker": "d", "ls": "-.", "zorder": 3},
    "cut": {"label": "Cut Ring (Negative Control)", "color": "#9E9E9E", "lw": 1.6, "marker": "v", "ls": "--", "zorder": 2},
}

# Dark style matching modern quantum papers
plt.style.use("dark_background")
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

for arm, style in arms_to_plot.items():
    ks = sorted(int(k) for k in obs[arm].keys())
    probs = [obs[arm][str(k)]["1"] / obs[arm][str(k)]["shots"] for k in ks]
    ax.plot(
        ks,
        probs,
        label=style["label"],
        color=style["color"],
        linewidth=style["lw"],
        marker=style["marker"],
        linestyle=style.get("ls", "-"),
        markersize=7,
        alpha=0.95,
        zorder=style["zorder"],
    )

ax.set_title("IBM Heron r2 (ibm_marrakesh) — Topological Closed-Loop Excitation Retention", fontsize=13, fontweight="bold", pad=14, color="#ECEFF1")
ax.set_xlabel("Evolution Rounds (k)", fontsize=11, labelpad=8, color="#CFD8DC")
ax.set_ylabel(r"Excitation Retention Probability $P(|1\rangle_S)$", fontsize=11, labelpad=8, color="#CFD8DC")
ax.set_ylim(-0.02, 1.02)
ax.set_xlim(-1, 33)
ax.set_xticks(range(0, 33, 4))
ax.grid(True, linestyle="--", alpha=0.25, color="#78909C")

# Annotations
ax.annotate(
    "Wheel Retention Plateau\n~37% retention preserved\n(Z = 13.63, P < 1e-15)",
    xy=(32, 0.371),
    xytext=(20, 0.52),
    arrowprops=dict(facecolor="#00E5FF", edgecolor="#00E5FF", arrowstyle="->", lw=1.8),
    fontsize=9.5,
    fontweight="bold",
    color="#00E5FF",
    bbox=dict(boxstyle="round,pad=0.5", facecolor="#102027", edgecolor="#00E5FF", alpha=0.9),
)

ax.annotate(
    "Ring-Only Dissipation\nDrops to ~8.9%\n(Total bath decay)",
    xy=(32, 0.0898),
    xytext=(21, 0.20),
    arrowprops=dict(facecolor="#FF1744", edgecolor="#FF1744", arrowstyle="->", lw=1.8),
    fontsize=9.5,
    fontweight="bold",
    color="#FF1744",
    bbox=dict(boxstyle="round,pad=0.5", facecolor="#210005", edgecolor="#FF1744", alpha=0.9),
)

# Text box with hardware & preregistration info
info_text = (
    "Hardware: IBM Heron r2 (ibm_marrakesh)\n"
    "Layout: S=125, R1=117, R2=124, R3=126\n"
    "Shots: 512 / circuit (117 circuits)\n"
    "Protocol: PLAN_WHEEL_v1.2 (Preregistered 2026-11-12)\n"
    "Verdict: ANOMALIA (Z = 13.63 vs Aer prediction)"
)
ax.text(
    0.03,
    0.05,
    info_text,
    transform=ax.transAxes,
    fontsize=8.5,
    verticalalignment="bottom",
    fontfamily="monospace",
    color="#B0BEC5",
    bbox=dict(boxstyle="round,pad=0.6", facecolor="#121212", edgecolor="#37474F", alpha=0.85),
)

ax.legend(loc="upper right", framealpha=0.85, facecolor="#1A1A1A", edgecolor="#37474F", fontsize=9)
plt.tight_layout()

png_path = OUT_DIR / "wheel_hardware_retention.png"
svg_path = OUT_DIR / "wheel_hardware_retention.svg"
plt.savefig(png_path, dpi=300)
plt.savefig(svg_path)
plt.close()

print(f"Grafikonok sikeresen elmentve:\n  - {png_path}\n  - {svg_path}")
