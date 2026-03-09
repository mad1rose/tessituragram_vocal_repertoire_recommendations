"""
Visualizations for alpha sensitivity analysis (RQ1 & RQ2).

Reads experiment_results/alpha_sensitivity_results.json and produces:

- alpha_sensitivity_rq1.png: HR@1 and MRR vs alpha (with 95% CI shading).
- alpha_sensitivity_rq2.png: mean Kendall's tau vs alpha (with 95% CI shading).
- alpha_sensitivity_combined.png: combined figure for paper layout.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
EXP_DIR = ROOT / "experiment_results"
RESULTS_PATH = EXP_DIR / "alpha_sensitivity_results.json"


def load_results() -> dict:
    with RESULTS_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _as_arrays(alpha_values, metrics_dict, key: str):
    xs = np.array(alpha_values, dtype=float)
    ys = []
    lo = []
    hi = []
    for a in alpha_values:
        m = metrics_dict[str(a)][key]
        ys.append(m["value"])
        lo.append(m["ci_95"][0])
        hi.append(m["ci_95"][1])
    ys = np.array(ys, dtype=float)
    lo = np.array(lo, dtype=float)
    hi = np.array(hi, dtype=float)
    return xs, ys, lo, hi


def fig_rq1(results: dict) -> None:
    """Line plots of HR@1 and MRR vs alpha with 95% CI shading."""
    alpha_values = results["alpha_values"]
    rq1_metrics = results["rq1_metrics"]

    xs, hr1, hr1_lo, hr1_hi = _as_arrays(alpha_values, rq1_metrics, "HR@1")
    _, mrr, mrr_lo, mrr_hi = _as_arrays(alpha_values, rq1_metrics, "MRR")

    fig, ax = plt.subplots(figsize=(7, 5))

    ax.plot(xs, hr1, "-o", color="#2e86ab", label="HR@1", linewidth=2)
    ax.fill_between(xs, hr1_lo, hr1_hi, color="#2e86ab", alpha=0.15)

    ax.plot(xs, mrr, "-s", color="#a23b72", label="MRR", linewidth=2)
    ax.fill_between(xs, mrr_lo, mrr_hi, color="#a23b72", alpha=0.15)

    ax.set_xlabel("alpha (avoid-penalty weight)", fontsize=12)
    ax.set_ylabel("Score", fontsize=12)
    ax.set_title("Alpha sensitivity for RQ1: HR@1 and MRR", fontsize=14)
    ax.set_xticks(xs)
    ax.set_ylim(0, 1.1)
    ax.grid(alpha=0.3)
    ax.legend()

    fig.tight_layout()
    out = EXP_DIR / "alpha_sensitivity_rq1.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")


def fig_rq2(results: dict) -> None:
    """Line plot of mean tau per baseline vs alpha with 95% CI shading."""
    alpha_values = results["alpha_values"]
    rq2_metrics = results["rq2_metrics"]

    xs = np.array(alpha_values, dtype=float)
    means = []
    ci_lo = []
    ci_hi = []
    for a in alpha_values:
        m = rq2_metrics[str(a)]
        means.append(m["mean_tau_per_baseline"])
        lo, hi = m["ci_95_baseline_mean"]
        ci_lo.append(lo)
        ci_hi.append(hi)
    means = np.array(means, dtype=float)
    ci_lo = np.array(ci_lo, dtype=float)
    ci_hi = np.array(ci_hi, dtype=float)

    fig, ax = plt.subplots(figsize=(7, 5))

    ax.plot(xs, means, "-o", color="#2e86ab", linewidth=2, label="Mean tau (per baseline)")
    ax.fill_between(xs, ci_lo, ci_hi, color="#2e86ab", alpha=0.15)

    ax.axhline(y=0.7, color="#888", linestyle="--", alpha=0.7, label="tau = 0.7 (strong)")
    ax.axhline(y=0.3, color="#aaa", linestyle=":", alpha=0.6, label="tau = 0.3 (moderate)")

    ax.set_xlabel("alpha (avoid-penalty weight)", fontsize=12)
    ax.set_ylabel(r"Mean Kendall's $\tau$ (per baseline)", fontsize=12)
    ax.set_title("Alpha sensitivity for RQ2: ranking stability", fontsize=14)
    ax.set_xticks(xs)
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.3)
    ax.legend()

    fig.tight_layout()
    out = EXP_DIR / "alpha_sensitivity_rq2.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")


def fig_combined(results: dict) -> None:
    """Combined figure: RQ1 (HR@1 & MRR) and RQ2 (mean tau) vs alpha."""
    alpha_values = results["alpha_values"]
    rq1_metrics = results["rq1_metrics"]
    rq2_metrics = results["rq2_metrics"]

    xs, hr1, hr1_lo, hr1_hi = _as_arrays(alpha_values, rq1_metrics, "HR@1")
    _, mrr, mrr_lo, mrr_hi = _as_arrays(alpha_values, rq1_metrics, "MRR")

    tau_means = []
    tau_lo = []
    tau_hi = []
    for a in alpha_values:
        m = rq2_metrics[str(a)]
        tau_means.append(m["mean_tau_per_baseline"])
        lo, hi = m["ci_95_baseline_mean"]
        tau_lo.append(lo)
        tau_hi.append(hi)
    tau_means = np.array(tau_means, dtype=float)
    tau_lo = np.array(tau_lo, dtype=float)
    tau_hi = np.array(tau_hi, dtype=float)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Left: RQ1
    ax1.plot(xs, hr1, "-o", color="#2e86ab", label="HR@1", linewidth=2)
    ax1.fill_between(xs, hr1_lo, hr1_hi, color="#2e86ab", alpha=0.15)
    ax1.plot(xs, mrr, "-s", color="#a23b72", label="MRR", linewidth=2)
    ax1.fill_between(xs, mrr_lo, mrr_hi, color="#a23b72", alpha=0.15)
    ax1.set_xlabel("alpha", fontsize=12)
    ax1.set_ylabel("Score", fontsize=12)
    ax1.set_title("(a) RQ1: HR@1 & MRR vs alpha")
    ax1.set_xticks(xs)
    ax1.set_ylim(0, 1.1)
    ax1.grid(alpha=0.3)
    ax1.legend(fontsize=9)

    # Right: RQ2
    ax2.plot(xs, tau_means, "-o", color="#2e86ab", linewidth=2, label="Mean tau (per baseline)")
    ax2.fill_between(xs, tau_lo, tau_hi, color="#2e86ab", alpha=0.15)
    ax2.axhline(y=0.7, color="#888", linestyle="--", alpha=0.7, label="tau = 0.7 (strong)")
    ax2.axhline(y=0.3, color="#aaa", linestyle=":", alpha=0.6, label="tau = 0.3 (moderate)")
    ax2.set_xlabel("alpha", fontsize=12)
    ax2.set_ylabel(r"Mean Kendall's $\tau$", fontsize=12)
    ax2.set_title("(b) RQ2: stability vs alpha")
    ax2.set_xticks(xs)
    ax2.set_ylim(0, 1.05)
    ax2.grid(alpha=0.3)
    ax2.legend(fontsize=9)

    fig.suptitle("Alpha sensitivity: effect of avoid-penalty weight", fontsize=14, y=1.03)
    fig.tight_layout()
    out = EXP_DIR / "alpha_sensitivity_combined.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")


def main() -> None:
    print("Loading alpha sensitivity results...")
    results = load_results()
    print("Generating alpha sensitivity visualizations...")
    fig_rq1(results)
    fig_rq2(results)
    fig_combined(results)
    print("Done.")


if __name__ == "__main__":
    main()

