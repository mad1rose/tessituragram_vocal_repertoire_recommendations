"""
Publication figure: RQ1 oracle self-retrieval for primary metrics HR@1 and MRR only.
Two panels (Experiment 1 compact library, Experiment 2 expanded), grouped bars with
95% bootstrap percentile CIs. Output: 300 dpi PNG for Word (CADSCOM template).

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

# Point estimate and 95% CI [lo, hi] from Table 2 (canonical JSON / paper).
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
    ax.set_title(title, fontsize=11, fontweight="bold", pad=10)
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
            "figure.dpi": 150,
            "savefig.dpi": 300,
        }
    )

    # ~6.5 in wide (CADSCOM text block). Manual margins avoid suptitle/legend overlap
    # with constrained_layout (shared legend below panels; no legend on axes).
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 3.75))
    _panel(
        axes[0],
        EXP1,
        "Experiment 1 (101 lines, 50 queries)",
    )
    _panel(
        axes[1],
        EXP2,
        "Experiment 2 (1,655 lines, 200 queries)",
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
        "RQ1: Oracle self-retrieval (primary metrics)",
        fontsize=11,
        fontweight="bold",
        y=0.995,
    )

    # top=0.72 leaves a clear band above panels for the suptitle (avoids overlap with Experiment titles)
    fig.subplots_adjust(left=0.09, right=0.98, top=0.72, bottom=0.22, wspace=0.28)

    fig.savefig(OUT_PNG, dpi=300, bbox_inches="tight", facecolor="white", pad_inches=0.08)
    plt.close()
    print(f"Wrote {OUT_PNG} (300 dpi)")


if __name__ == "__main__":
    main()
