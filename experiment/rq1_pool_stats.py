"""
Descriptive statistics for RQ1 range-filtered candidate set sizes |C|.

Used by run_rq1_experiment and run_rq1_baselines to document pool difficulty
and relate the null (random-ranking) baseline to E[1/|C|] under uniform
top-1 hits (finite population sampling without replacement per query).
"""

from __future__ import annotations

import statistics
from typing import Any


def _percentile(sorted_vals: list[int], p: float) -> int:
    if not sorted_vals:
        raise ValueError("empty sorted_vals")
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    i = int(round((p / 100.0) * (len(sorted_vals) - 1)))
    return sorted_vals[i]


def compute_candidate_pool_summary(n_candidates: list[int]) -> dict[str, Any]:
    """Summary of |C| over the sampled RQ1 queries (descriptive only)."""
    if not n_candidates:
        return {}
    s = sorted(n_candidates)
    inv = [1.0 / float(x) for x in n_candidates]
    n = len(n_candidates)
    return {
        "n_queries": n,
        "n_candidates_min": min(n_candidates),
        "n_candidates_max": max(n_candidates),
        "n_candidates_mean": round(statistics.mean(n_candidates), 4),
        "n_candidates_median": float(statistics.median(n_candidates)),
        "n_candidates_p25": float(_percentile(s, 25)),
        "n_candidates_p75": float(_percentile(s, 75)),
        "fraction_n_candidates_le_5": round(
            sum(1 for x in n_candidates if x <= 5) / n, 6
        ),
        "fraction_n_candidates_le_10": round(
            sum(1 for x in n_candidates if x <= 10) / n, 6
        ),
        "fraction_n_candidates_le_20": round(
            sum(1 for x in n_candidates if x <= 20) / n, 6
        ),
        "mean_inverse_n_candidates": round(statistics.mean(inv), 6),
    }


def stratify_rq1_by_pool_size(
    per_query: list[dict],
    *,
    bins: list[tuple[int | None, int | None, str]],
) -> list[dict[str, Any]]:
    """
    Point estimates of HR@1 for full and null_random over |C| bins.

    ``per_query`` items must include ``n_candidates`` and ``models`` with
    ``full`` and ``null_random`` entries containing ``hit@1``.

    bins: list of (low, high, label) with inclusive bounds; use None for open.
    """
    rows: list[dict[str, Any]] = []
    for lo, hi, label in bins:
        hits_f: list[float] = []
        hits_n: list[float] = []
        nc_sub: list[int] = []
        for rec in per_query:
            nc = int(rec["n_candidates"])
            if lo is not None and nc < lo:
                continue
            if hi is not None and nc > hi:
                continue
            nc_sub.append(nc)
            m = rec.get("models") or {}
            if "full" in m:
                hits_f.append(float(m["full"]["hit@1"]))
            if "null_random" in m:
                hits_n.append(float(m["null_random"]["hit@1"]))
        inv = [1.0 / float(x) for x in nc_sub] if nc_sub else []
        rows.append(
            {
                "bin_label": label,
                "n_queries": len(nc_sub),
                "hr1_full_mean": round(sum(hits_f) / len(hits_f), 6)
                if hits_f
                else None,
                "hr1_null_random_mean": round(sum(hits_n) / len(hits_n), 6)
                if hits_n
                else None,
                "mean_inverse_n_candidates": round(statistics.mean(inv), 6)
                if inv
                else None,
            }
        )
    return rows
