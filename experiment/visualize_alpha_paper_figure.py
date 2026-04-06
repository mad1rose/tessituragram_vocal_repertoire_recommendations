"""
Publication figure: α-sensitivity (Figure 2 in paper): HR@1, MRR (RQ1) and mean τ (RQ2)
for Experiment 1 (101-line library JSON) and Experiment 2 (expanded library JSON).

Layout: **one row, two panels** (not 2×2) to minimize vertical height for Word/page flow.
Same data as before: Exp 1 = solid lines, Exp 2 = dashed; legend encodes metric + experiment.

Output: paper_draft/figures/alpha_sensitivity_hr1_mrr_tau.png — ~6.25 in x ~2.05 in @ 300 dpi, dpi embedded (Pillow), no bbox_inches=\"tight\".

Run from repo root: python experiment/visualize_alpha_paper_figure.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "paper_draft" / "figures"
OUT_PNG = OUT_DIR / "alpha_sensitivity_hr1_mrr_tau.png"

JSON_EXP1 = ROOT / "previous_paper_and_experiments" / "previous_experiment_results" / "old_alpha_sensitivity_results.json"
JSON_EXP2 = ROOT / "experiment_results" / "alpha_sensitivity_results.json"

PRINT_DPI = 300
# Short: single row fits at bottom of a text page without forcing a huge white gap.
FIG_W_IN = 6.25
FIG_H_IN = 2.05

COLORS = {"HR@1": "#2e86ab", "MRR": "#c73e1d"}
TAU_COLOR = "#1a535c"


def _as_arrays(alpha_values: list[float], rq1: dict, key: str):
    xs = np.array(alpha_values, dtype=float)
    ys, lo, hi = [], [], []
    for a in alpha_values:
        m = rq1[str(a)][key]
        ys.append(m["value"])
        lo.append(m["ci_95"][0])
        hi.append(m["ci_95"][1])
    return xs, np.array(ys), np.array(lo), np.array(hi)


def _tau_arrays(alpha_values: list[float], rq2: dict):
    xs = np.array(alpha_values, dtype=float)
    means, lo, hi = [], [], []
    for a in alpha_values:
        m = rq2[str(a)]
        means.append(m["mean_tau_per_baseline"])
        l, h = m["ci_95_baseline_mean"]
        lo.append(l)
        hi.append(h)
    return xs, np.array(means), np.array(lo), np.array(hi)


def _plot_rq1_combined(ax, rq1_e1: dict, rq1_e2: dict, alphas: list[float]) -> None:
    """Both experiments on one axis: solid = Exp 1, dashed = Exp 2."""
    specs = [
        (rq1_e1, "-", "Exp 1"),
        (rq1_e2, "--", "Exp 2"),
    ]
    legend_handles: list[Line2D] = []
    for rq1, ls, tag in specs:
        xs, hr1, hlo, hhi = _as_arrays(alphas, rq1, "HR@1")
        _, mrr, mlo, mhi = _as_arrays(alphas, rq1, "MRR")
        ax.plot(
            xs,
            hr1,
            ls,
            color=COLORS["HR@1"],
            linewidth=1.5,
            markersize=4,
            marker="o",
        )
        ax.fill_between(xs, hlo, hhi, color=COLORS["HR@1"], alpha=0.12)
        ax.plot(
            xs,
            mrr,
            ls,
            color=COLORS["MRR"],
            linewidth=1.5,
            markersize=3,
            marker="s",
        )
        ax.fill_between(xs, mlo, mhi, color=COLORS["MRR"], alpha=0.12)
        legend_handles.append(
            Line2D(
                [0],
                [0],
                color=COLORS["HR@1"],
                linestyle=ls,
                linewidth=1.5,
                marker="o",
                markersize=4,
                label=f"HR@1 ({tag})",
            )
        )
        legend_handles.append(
            Line2D(
                [0],
                [0],
                color=COLORS["MRR"],
                linestyle=ls,
                linewidth=1.5,
                marker="s",
                markersize=3,
                label=f"MRR ({tag})",
            )
        )

    ax.set_xticks(np.array(alphas, dtype=float))
    ax.set_ylim(0, 1.05)
    ax.set_xlabel(r"$\alpha$ (avoid weight)", fontsize=8)
    ax.set_ylabel("Mean (95% CI)", fontsize=8)
    ax.set_title("Self-retrieval (HR@1, MRR)", fontsize=8, fontweight="bold", pad=4)
    ax.grid(axis="y", alpha=0.35, linestyle="--", linewidth=0.6)
    ax.legend(
        handles=legend_handles,
        loc="lower left",
        ncol=2,
        fontsize=6.5,
        frameon=True,
        fancybox=False,
        edgecolor="#cccccc",
        handlelength=3.6,
        columnspacing=0.7,
        handletextpad=0.35,
        borderpad=0.35,
    )


def _plot_tau_combined(ax, rq2_e1: dict, rq2_e2: dict, alphas: list[float]) -> None:
    specs = [
        (rq2_e1, "-", "Exp 1"),
        (rq2_e2, "--", "Exp 2"),
    ]
    legend_handles: list[Line2D] = []
    for rq2, ls, tag in specs:
        xs, means, lo, hi = _tau_arrays(alphas, rq2)
        ax.plot(
            xs,
            means,
            ls,
            color=TAU_COLOR,
            linewidth=1.5,
            markersize=4,
            marker="o",
        )
        ax.fill_between(xs, lo, hi, color=TAU_COLOR, alpha=0.1)
        legend_handles.append(
            Line2D(
                [0],
                [0],
                color=TAU_COLOR,
                linestyle=ls,
                linewidth=1.5,
                marker="o",
                markersize=4,
                label=rf"Mean $\tau$ ({tag})",
            )
        )

    ax.axhline(0.7, color="#888888", linestyle=":", linewidth=0.9, alpha=0.75)
    ax.set_xticks(np.array(alphas, dtype=float))
    ax.set_ylim(0.75, 1.02)
    ax.set_xlabel(r"$\alpha$ (avoid weight)", fontsize=8)
    ax.set_ylabel(r"Mean $\tau$", fontsize=8)
    ax.set_title("Stability (mean Kendall's τ)", fontsize=8, fontweight="bold", pad=4)
    ax.grid(axis="y", alpha=0.35, linestyle="--", linewidth=0.6)
    ax.legend(
        handles=legend_handles,
        loc="lower left",
        fontsize=6.5,
        frameon=True,
        fancybox=False,
        edgecolor="#cccccc",
        handlelength=3.6,
        borderpad=0.35,
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with JSON_EXP1.open(encoding="utf-8") as f:
        d1 = json.load(f)
    with JSON_EXP2.open(encoding="utf-8") as f:
        d2 = json.load(f)
    alphas = [float(x) for x in d2["alpha_values"]]

    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Georgia", "DejaVu Serif", "Times New Roman", "Times"],
            "font.size": 9,
            "axes.titlesize": 9,
            "axes.labelsize": 8,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7,
            "legend.fontsize": 6.5,
            "figure.dpi": 100,
            "savefig.dpi": PRINT_DPI,
        }
    )

    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(FIG_W_IN, FIG_H_IN), sharex=True)

    _plot_rq1_combined(ax0, d1["rq1_metrics"], d2["rq1_metrics"], alphas)
    _plot_tau_combined(ax1, d1["rq2_metrics"], d2["rq2_metrics"], alphas)

    fig.subplots_adjust(left=0.09, right=0.99, top=0.90, bottom=0.19, wspace=0.34)

    fig.savefig(OUT_PNG, dpi=PRINT_DPI, facecolor="white", pad_inches=0.06)
    plt.close()

    try:
        from PIL import Image

        with Image.open(OUT_PNG) as im:
            im.save(OUT_PNG, dpi=(PRINT_DPI, PRINT_DPI), optimize=True)
    except ImportError:
        pass

    w_px = int(round(FIG_W_IN * PRINT_DPI))
    h_px = int(round(FIG_H_IN * PRINT_DPI))
    print(f"Wrote {OUT_PNG} ({FIG_W_IN} in x {FIG_H_IN} in @ {PRINT_DPI} dpi ~= {w_px}x{h_px} px)")


if __name__ == "__main__":
    main()
