"""
Visualizations for RQ1/RQ2 baselines: full vs null_random vs cosine_only.

Reads:
  - experiment_results/RQ1_baselines.json
  - experiment_results/RQ2_baselines.json

Produces:
  - experiment_results/RQ1_baselines.png
  - experiment_results/RQ2_baselines.png
  - experiment_results/RQ_baselines_combined.png
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
EXP_DIR = ROOT / "experiment_results"
RQ1_BASELINES_PATH = EXP_DIR / "RQ1_baselines.json"
RQ2_BASELINES_PATH = EXP_DIR / "RQ2_baselines.json"


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def fig_rq1_baselines(results: dict) -> None:
    """
    Bar/line plot comparing HR@1 and MRR across
    full vs null_random vs cosine_only (with 95% CI whiskers).
    """
    metrics = results["metrics"]
    model_order = ["full", "null_random", "cosine_only"]
    x = np.arange(len(model_order))

    hr1_vals = [metrics[m]["HR@1"]["value"] for m in model_order]
    hr1_lo = [metrics[m]["HR@1"]["ci_95"][0] for m in model_order]
    hr1_hi = [metrics[m]["HR@1"]["ci_95"][1] for m in model_order]

    mrr_vals = [metrics[m]["MRR"]["value"] for m in model_order]
    mrr_lo = [metrics[m]["MRR"]["ci_95"][0] for m in model_order]
    mrr_hi = [metrics[m]["MRR"]["ci_95"][1] for m in model_order]

    # Asymmetric error bars
    hr1_yerr = [
        [v - lo for v, lo in zip(hr1_vals, hr1_lo)],
        [hi - v for v, hi in zip(hr1_vals, hr1_hi)],
    ]
    mrr_yerr = [
        [v - lo for v, lo in zip(mrr_vals, mrr_lo)],
        [hi - v for v, hi in zip(mrr_vals, mrr_hi)],
    ]

    width = 0.35
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(
        x - width / 2,
        hr1_vals,
        width,
        label="HR@1",
        color="#2e86ab",
        edgecolor="#1a5276",
        linewidth=1.2,
    )
    ax.errorbar(
        x - width / 2,
        hr1_vals,
        yerr=hr1_yerr,
        fmt="none",
        color="#1a5276",
        capsize=6,
        capthick=1.5,
    )

    ax.bar(
        x + width / 2,
        mrr_vals,
        width,
        label="MRR",
        color="#a23b72",
        edgecolor="#6c274a",
        linewidth=1.2,
    )
    ax.errorbar(
        x + width / 2,
        mrr_vals,
        yerr=mrr_yerr,
        fmt="none",
        color="#6c274a",
        capsize=6,
        capthick=1.5,
    )

    ax.set_xticks(x)
    ax.set_xticklabels(["Full", "Null (random)", "Cosine-only"], rotation=0)
    ax.set_ylabel("Score")
    ax.set_ylim(0.0, 1.15)
    ax.set_title("RQ1 baselines: HR@1 and MRR (95% CI)")
    ax.grid(axis="y", alpha=0.3)
    ax.legend()

    fig.tight_layout()
    out_path = EXP_DIR / "RQ1_baselines.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def fig_rq2_baselines(results: dict) -> None:
    """
    Bar plot comparing mean baseline-level τ across
    full vs null_random vs cosine_only (with 95% CI).
    """
    metrics = results["metrics"]
    model_order = ["full", "null_random", "cosine_only"]
    x = np.arange(len(model_order))

    tau_vals = [metrics[m]["mean_tau_per_baseline"] for m in model_order]
    ci_lo = [metrics[m]["ci_95_baseline_mean"][0] for m in model_order]
    ci_hi = [metrics[m]["ci_95_baseline_mean"][1] for m in model_order]
    yerr = [
        [v - lo for v, lo in zip(tau_vals, ci_lo)],
        [hi - v for v, hi in zip(tau_vals, ci_hi)],
    ]

    fig, ax = plt.subplots(figsize=(7, 5))
    colors = ["#2e86ab", "#f18f01", "#a23b72"]
    labels = ["Full", "Null (random)", "Cosine-only"]

    ax.bar(
        x,
        tau_vals,
        color=colors,
        edgecolor="#333",
        linewidth=1.2,
    )
    ax.errorbar(
        x,
        tau_vals,
        yerr=yerr,
        fmt="none",
        color="#333",
        capsize=8,
        capthick=1.8,
    )

    for i, (v, lo, hi) in enumerate(zip(tau_vals, ci_lo, ci_hi)):
        ax.annotate(
            f"{v:.3f}\n[{lo:.3f}–{hi:.3f}]",
            xy=(i, v + 0.03),
            ha="center",
            va="bottom",
            fontsize=9,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel(r"Mean baseline-level Kendall's $\tau$")
    ax.set_ylim(-0.1, 1.05)
    ax.axhline(y=0.7, color="#888", linestyle="--", alpha=0.7, label=r"$\tau = 0.7$ (strong)")
    ax.axhline(y=0.3, color="#bbb", linestyle=":", alpha=0.7, label=r"$\tau = 0.3$ (moderate)")
    ax.set_title("RQ2 baselines: ranking stability (95% CI)")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(loc="upper left")

    fig.tight_layout()
    out_path = EXP_DIR / "RQ2_baselines.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def fig_combined(rq1_results: dict, rq2_results: dict) -> None:
    """
    Combined 1x2 layout for the paper:
      - Left: RQ1 HR@1 + MRR vs model
      - Right: RQ2 mean tau vs model
    """
    rq1_metrics = rq1_results["metrics"]
    rq2_metrics = rq2_results["metrics"]
    model_order = ["full", "null_random", "cosine_only"]
    labels = ["Full", "Null (random)", "Cosine-only"]
    x = np.arange(len(model_order))

    # Prepare RQ1 data
    hr1 = [rq1_metrics[m]["HR@1"]["value"] for m in model_order]
    hr1_lo = [rq1_metrics[m]["HR@1"]["ci_95"][0] for m in model_order]
    hr1_hi = [rq1_metrics[m]["HR@1"]["ci_95"][1] for m in model_order]
    hr1_yerr = [
        [v - lo for v, lo in zip(hr1, hr1_lo)],
        [hi - v for v, hi in zip(hr1, hr1_hi)],
    ]

    mrr = [rq1_metrics[m]["MRR"]["value"] for m in model_order]
    mrr_lo = [rq1_metrics[m]["MRR"]["ci_95"][0] for m in model_order]
    mrr_hi = [rq1_metrics[m]["MRR"]["ci_95"][1] for m in model_order]
    mrr_yerr = [
        [v - lo for v, lo in zip(mrr, mrr_lo)],
        [hi - v for v, hi in zip(mrr, mrr_hi)],
    ]

    # Prepare RQ2 data
    tau = [rq2_metrics[m]["mean_tau_per_baseline"] for m in model_order]
    tau_lo = [rq2_metrics[m]["ci_95_baseline_mean"][0] for m in model_order]
    tau_hi = [rq2_metrics[m]["ci_95_baseline_mean"][1] for m in model_order]
    tau_yerr = [
        [v - lo for v, lo in zip(tau, tau_lo)],
        [hi - v for v, hi in zip(tau, tau_hi)],
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Left: RQ1
    width = 0.35
    ax1.bar(
        x - width / 2,
        hr1,
        width,
        label="HR@1",
        color="#2e86ab",
        edgecolor="#1a5276",
        linewidth=1.2,
    )
    ax1.errorbar(
        x - width / 2,
        hr1,
        yerr=hr1_yerr,
        fmt="none",
        color="#1a5276",
        capsize=5,
        capthick=1.4,
    )

    ax1.bar(
        x + width / 2,
        mrr,
        width,
        label="MRR",
        color="#a23b72",
        edgecolor="#6c274a",
        linewidth=1.2,
    )
    ax1.errorbar(
        x + width / 2,
        mrr,
        yerr=mrr_yerr,
        fmt="none",
        color="#6c274a",
        capsize=5,
        capthick=1.4,
    )

    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=0)
    ax1.set_ylabel("Score")
    ax1.set_ylim(0.0, 1.15)
    ax1.set_title("RQ1: self-retrieval baselines")
    ax1.grid(axis="y", alpha=0.3)
    ax1.legend()

    # Right: RQ2
    colors = ["#2e86ab", "#f18f01", "#a23b72"]
    ax2.bar(
        x,
        tau,
        color=colors,
        edgecolor="#333",
        linewidth=1.2,
    )
    ax2.errorbar(
        x,
        tau,
        yerr=tau_yerr,
        fmt="none",
        color="#333",
        capsize=6,
        capthick=1.6,
    )
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=0)
    ax2.set_ylabel(r"Mean baseline-level Kendall's $\tau$")
    ax2.set_ylim(-0.1, 1.05)
    ax2.axhline(y=0.7, color="#888", linestyle="--", alpha=0.7)
    ax2.axhline(y=0.3, color="#bbb", linestyle=":", alpha=0.7)
    ax2.set_title("RQ2: stability baselines")
    ax2.grid(axis="y", alpha=0.3)

    fig.suptitle("Baselines: full vs null vs cosine-only (RQ1 & RQ2)", fontsize=14, y=1.03)
    fig.tight_layout()
    out_path = EXP_DIR / "RQ_baselines_combined.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def main() -> None:
    print("Loading baseline results...")
    rq1_results = _load_json(RQ1_BASELINES_PATH)
    rq2_results = _load_json(RQ2_BASELINES_PATH)
    print("Generating baseline comparison figures...")
    fig_rq1_baselines(rq1_results)
    fig_rq2_baselines(rq2_results)
    fig_combined(rq1_results, rq2_results)
    print("Done.")


if __name__ == "__main__":
    main()