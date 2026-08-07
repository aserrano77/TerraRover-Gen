#!/usr/bin/env python3
"""Generate the frozen manuscript figures for TerraRover-Gen.

The quantitative figures consume only the frozen CSV outputs from the
paper-analysis pipeline.  The terrain montage uses archived screenshots from
the TFG PDF renders and is intended as the manuscript layout/source selection;
native Unity screenshots should replace these crops if higher-resolution
originals are recovered before production.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "frozen_inputs"
OUT = ROOT / "paper_figures"
OUT.mkdir(exist_ok=True)

TERRAIN_ORDER = [
    "V3_F3_02",
    "BigRock",
    "HardTerrain",
    "BumpyGround",
    "Complete",
    "DeepHoles",
]


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.labelsize": 9,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
            "legend.fontsize": 8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def terrain_montage() -> None:
    sources = {
        "V3_F3_02": (ROOT / "tmp/pdfs/page_91.png", (225, 920, 685, 1067)),
        "BigRock": (ROOT / "tmp/pdfs/page_92.png", (128, 928, 505, 1106)),
        "HardTerrain": (ROOT / "tmp/pdfs/page_93.png", (128, 246, 548, 379)),
        "BumpyGround": (ROOT / "tmp/pdfs/page_93.png", (128, 1025, 555, 1169)),
        "Complete": (ROOT / "tmp/pdfs/page_93.png", (128, 616, 546, 819)),
        "DeepHoles": (ROOT / "tmp/pdfs/page_94.png", (128, 246, 532, 440)),
    }
    descriptors = {
        "V3_F3_02": "Reference terrain",
        "BigRock": "Larger obstacles",
        "HardTerrain": "Rough/hilly terrain + holes/slope",
        "BumpyGround": "Extreme roughness",
        "Complete": "Combined stress condition",
        "DeepHoles": "Deep-hole condition",
    }

    fig, axes = plt.subplots(2, 3, figsize=(7.2, 4.2), constrained_layout=True)
    for i, (ax, terrain) in enumerate(zip(axes.flat, TERRAIN_ORDER)):
        path, crop = sources[terrain]
        img = Image.open(path).convert("RGB").crop(crop)
        ax.imshow(img)
        ax.set_axis_off()
        ax.set_title(f"({chr(97+i)}) {terrain}\n{descriptors[terrain]}", fontsize=8.7, pad=4)

    fig.savefig(OUT / "fig01_terrain_families.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def primary_effect_plot() -> None:
    df = pd.read_csv(INPUT / "paper_results_primary.csv").set_index("terrain").loc[TERRAIN_ORDER]
    y = np.arange(len(df))[::-1]
    effect = df["diff_rl_minus_heuristic_pp"].to_numpy()
    lo = df["diff_bca95_low_pp"].to_numpy()
    hi = df["diff_bca95_high_pp"].to_numpy()
    reject = df["mcnemar_holm_reject_0_05"].astype(bool).to_numpy()

    fig, ax = plt.subplots(figsize=(6.6, 3.65), constrained_layout=True)
    ax.axvline(0, color="#4D4D4D", lw=1, ls="--", zorder=0)
    ax.axvspan(-55, 0, color="#F4F4F4", zorder=-2)
    for yi, e, l, h, sig in zip(y, effect, lo, hi, reject):
        ax.plot([l, h], [yi, yi], color="#1F4E79", lw=1.8, zorder=2)
        ax.plot([l, l], [yi - 0.08, yi + 0.08], color="#1F4E79", lw=1.2)
        ax.plot([h, h], [yi - 0.08, yi + 0.08], color="#1F4E79", lw=1.2)
        ax.scatter(
            [e], [yi], s=42, marker="o",
            facecolor="#1F4E79" if sig else "white",
            edgecolor="#1F4E79", linewidth=1.4, zorder=3,
        )

    ax.set_yticks(y, TERRAIN_ORDER)
    ax.set_xlim(-55, 20)
    ax.set_xlabel("Difference in success rate, RL minus heuristic (percentage points)")
    ax.set_ylabel("")
    ax.grid(axis="x", color="#E2E2E2", lw=0.6)
    ax.text(-52.5, len(df) - 0.15, "Heuristic favoured", va="top", ha="left", fontsize=8, color="#555555")
    ax.text(17.5, len(df) - 0.15, "RL favoured", va="top", ha="right", fontsize=8, color="#555555")
    ax.scatter([], [], s=38, facecolor="#1F4E79", edgecolor="#1F4E79", label="Holm-adjusted p < 0.05")
    ax.scatter([], [], s=38, facecolor="white", edgecolor="#1F4E79", label="Holm-adjusted p ≥ 0.05")
    ax.legend(loc="lower right", frameon=False)

    for ext in ("png", "eps"):
        kwargs = {"dpi": 600} if ext == "png" else {}
        fig.savefig(OUT / f"fig02_primary_success_effect.{ext}", bbox_inches="tight", **kwargs)
    plt.close(fig)


def failure_modes_plot() -> None:
    df = pd.read_csv(INPUT / "paper_results_failure_modes.csv")
    df["terrain"] = pd.Categorical(df["terrain"], TERRAIN_ORDER, ordered=True)
    df["system"] = pd.Categorical(df["system"], ["RL", "HEU"], ordered=True)
    df = df.sort_values(["terrain", "system"])

    categories = [
        ("success_pct", "Success", "#2A9D8F", ""),
        ("stuck_pct", "Stuck", "#E9C46A", "//"),
        ("fall_pct", "Fall", "#E76F51", "xx"),
        ("collision_pct", "Collision", "#6D597A", ".."),
    ]

    labels, positions = [], []
    pos = 0.0
    for terrain in TERRAIN_ORDER:
        for system in ("RL", "HEU"):
            labels.append(f"{terrain} - {system}")
            positions.append(pos)
            pos += 0.72
        pos += 0.35
    positions = np.asarray(positions)

    fig, ax = plt.subplots(figsize=(7.2, 5.0), constrained_layout=True)
    left = np.zeros(len(df))
    for col, label, color, hatch in categories:
        vals = df[col].to_numpy()
        ax.barh(
            positions, vals, left=left, height=0.56, label=label,
            color=color, edgecolor="white", linewidth=0.6, hatch=hatch,
        )
        left += vals

    ax.set_yticks(positions, labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Episode outcome share (%)")
    ax.set_ylabel("")
    ax.grid(axis="x", color="#E2E2E2", lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(ncol=4, loc="lower center", bbox_to_anchor=(0.5, 1.005), frameon=False)

    for ext in ("png", "eps"):
        kwargs = {"dpi": 300} if ext == "png" else {}
        fig.savefig(OUT / f"fig03_failure_modes.{ext}", bbox_inches="tight", **kwargs)
    plt.close(fig)


def main() -> None:
    _style()
    terrain_montage()
    primary_effect_plot()
    failure_modes_plot()


if __name__ == "__main__":
    main()
