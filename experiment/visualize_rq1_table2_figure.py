"""
Publication figure: RQ1 synthetic self-retrieval for primary metrics HR@1 and MRR only.
Two panels (Experiment 1 compact library, Experiment 2 expanded), grouped bars with
95% bootstrap percentile CIs. Output: PNG sized for **6.5 in × ~3.05 in** at **300 dpi** (≈1950×915 px) with **300 dpi embedded**
in the file so Microsoft Word uses the correct print width (Insert → Picture → From File; avoid
resizing in Word, which bloats PDFs—see CADSCOM template). `bbox_inches="tight"` is **not** used,
so pixel dimensions match figure size × dpi exactly.

Run from repo root: python experiment/visualize_rq1_table2_figure.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "paper_draft" / "figures"
OUT_PNG = OUT_DIR / "rq1_oracle_hr1_mrr.png"

# CADSCOM body width is 6.5 in; match that so Word does not guess 96 dpi and blow up the layout.
PRINT_DPI = 300
FIG_W_IN = 6.5
FIG_H_IN = 3.05

# Point estimate and 95% CI [lo, hi] from canonical RQ1 JSON / paper.
# Keys: model label -> metric -> (point, lo, hi)
EXP1 = {
    "Null": {"HR@1": (0.06, 0.00, 0.14), "MRR": (0.18, 0.12, 0.26)},
    "Cosine": {"HR@1": (0.80, 0.68, 0.90), "MRR": (0.88, 0.82, 0.94)},
    "Full": {"HR@1": (0.76, 0.64, 0.88), "MRR": (0.86, 0.79, 0.93)},
}
EXP2 = {
    "Null": {"HR@1": (0.02, 0.00, 0.04), "MRR": (0.06, 0.04, 0.09)},
    "Cosine": {"HR@1": (0.545, 0.477, 0.614), "MRR": (0.69, 0.64, 0.74)},
    "Full": {"HR@1": (0.550, 0.480, 0.619), "MRR": (0.69, 0.64, 0.73)},
}

MODELS = ["Null", "Cosine", "Full"]
METRICS = ["HR@1", "MRR"]
COLORS = {"HR@1": "#2e86ab", "MRR": "#c73e1d"}


def _yerr(point: float, lo: float, hi: float) -> tuple[float, float]:
    return (point - lo, hi - point)


def _panel(ax, data: dict, title: str) -> None:
    x = np.arange(len(MODELS))
    w = 0.36
    for i, metric in enumerate(METRICS):
        vals = []
        el = [[], []]
        for m in MODELS:
            p, lo, hi = data[m][metric]
            vals.append(p)
            lo_e, hi_e = _yerr(p, lo, hi)
            el[0].append(lo_e)
            el[1].append(hi_e)
        offset = (i - 0.5) * w
        ax.bar(
            x + offset,
            vals,
            width=w,
            label=metric,
            color=COLORS[metric],
            edgecolor="#333333",
            linewidth=0.8,
            yerr=el,
            capsize=3,
            error_kw={"linewidth": 1.0, "ecolor": "#333333"},
        )
    ax.set_xticks(x)
    ax.set_xticklabels(
        ["Null (random)", "Cosine (α=0)", "Full (α=0.5)"],
        fontsize=9,
    )
    ax.set_ylabel("Mean metric (95% bootstrap CI)", fontsize=10)
    ax.set_ylim(0, 1.05)
    ax.set_title(title, fontsize=10, fontweight="bold", pad=8)
    ax.grid(axis="y", alpha=0.35, linestyle="--", linewidth=0.6)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Georgia", "DejaVu Serif", "Times New Roman", "Times"],
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 8,
            "figure.dpi": 100,
            "savefig.dpi": PRINT_DPI,
        }
    )

    # Fixed figure size in inches → exact pixel size at PRINT_DPI (no bbox_inches="tight").
    fig, axes = plt.subplots(1, 2, figsize=(FIG_W_IN, FIG_H_IN))
    # Two-line titles keep each line short so the right panel title is not clipped at the figure edge.
    _panel(
        axes[0],
        EXP1,
        "Experiment 1\n(101 lines, 50 queries)",
    )
    _panel(
        axes[1],
        EXP2,
        "Experiment 2\n(1,655 lines, 200 queries)",
    )

    legend_handles = [
        mpatches.Patch(facecolor=COLORS["HR@1"], edgecolor="#333333", linewidth=0.8, label="HR@1"),
        mpatches.Patch(facecolor=COLORS["MRR"], edgecolor="#333333", linewidth=0.8, label="MRR"),
    ]
    fig.legend(
        handles=legend_handles,
        loc="lower center",
        ncol=2,
        fontsize=9,
        frameon=True,
        fancybox=False,
        edgecolor="#cccccc",
        bbox_to_anchor=(0.5, 0.02),
    )

    fig.suptitle(
        "RQ1: Synthetic self-retrieval (primary metrics)",
        fontsize=11,
        fontweight="bold",
        y=0.995,
    )

    # right < 1.0 leaves margin so long panel titles are not clipped; top for suptitle; bottom for legend
    fig.subplots_adjust(left=0.10, right=0.95, top=0.72, bottom=0.24, wspace=0.30)

    fig.savefig(
        OUT_PNG,
        dpi=PRINT_DPI,
        facecolor="white",
        pad_inches=0.08,
        metadata={"Software": "matplotlib; CADSCOM 300dpi"},
    )
    plt.close()

    # Word uses PNG resolution metadata; without 300 dpi embedded it may assume ~96 dpi → huge on page.
    try:
        from PIL import Image

        with Image.open(OUT_PNG) as im:
            im.save(OUT_PNG, dpi=(PRINT_DPI, PRINT_DPI), optimize=True)
    except ImportError:
        pass

    w_px = int(round(FIG_W_IN * PRINT_DPI))
    h_px = int(round(FIG_H_IN * PRINT_DPI))
    print(f"Wrote {OUT_PNG} ({FIG_W_IN} in x {FIG_H_IN} in @ {PRINT_DPI} dpi ~= {w_px}x{h_px} px, dpi embedded)")


if __name__ == "__main__":
    main()
