"""
Alpha sensitivity analysis for RQ1 and RQ2.

We sweep alpha in {0.0, 0.25, 0.5, 0.75, 1.0} and, for each value:

- RQ1: compute HR@1, HR@3, HR@5, MRR with 95% bootstrap CIs using the
  same query pool and sampling rule as run_rq1_experiment.py.
- RQ2: compute mean Kendall's tau across perturbations, baseline-level
  mean tau, and 95% bootstrap CI using the same baseline selection rule
  as run_rq2_experiment.py.

This script does not modify the main RQ1/RQ2 experiment scripts; it
reuses their helper functions for selecting queries and baselines, and
uses src.recommend.score_songs with different alpha values.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

# Allow running from project root or experiment folder
ROOT = Path(__file__).resolve().parent.parent
_sys_path = list(__import__("sys").path)
if str(ROOT) not in _sys_path:
    __import__("sys").path.insert(0, str(ROOT))

from src.storage import load_flat_library, work_id  # noqa: E402
from src.recommend import (  # noqa: E402
    filter_by_range,
    build_ideal_vector,
    score_songs,
)
from experiment.run_rq1_experiment import (  # noqa: E402
    _select_queries as rq1_select_queries,
    RANDOM_SEED as RQ1_RANDOM_SEED,
    N_QUERIES as RQ1_N_QUERIES,
    MIN_CANDIDATES as RQ1_MIN_CANDIDATES,
)
from experiment.run_rq2_experiment import (  # noqa: E402
    _select_baselines as rq2_select_baselines,
    _compute_kendall_tau,
    RANDOM_SEED as RQ2_RANDOM_SEED,
    N_BASELINES as RQ2_N_BASELINES,
    MIN_CANDIDATES as RQ2_MIN_CANDIDATES,
)


ALPHA_VALUES: List[float] = [0.0, 0.25, 0.5, 0.75, 1.0]
BOOTSTRAP_SAMPLES = 10_000


def _cluster_bootstrap_ci_mean(
    values: List[float],
    cluster_ids: List[str],
) -> Tuple[float, float]:
    """Cluster bootstrap 95% CI for the mean (Cameron et al., 2008)."""
    if not values:
        return 0.0, 0.0
    clusters: dict[str, list[int]] = {}
    for i, cid in enumerate(cluster_ids):
        clusters.setdefault(cid, []).append(i)
    cluster_keys = list(clusters.keys())
    n_clusters = len(cluster_keys)
    if n_clusters <= 1:
        m = float(np.mean(values))
        return m, m
    values_arr = np.array(values, dtype=float)
    boot = np.empty(BOOTSTRAP_SAMPLES)
    for b in range(BOOTSTRAP_SAMPLES):
        sampled = random.choices(cluster_keys, k=n_clusters)
        indices = [idx for key in sampled for idx in clusters[key]]
        boot[b] = np.mean(values_arr[indices])
    lo, hi = float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))
    return lo, hi


def _cluster_bootstrap_ci_mean_over_baselines(
    baseline_means: List[float],
    baseline_work_ids: List[str],
) -> Tuple[float, float]:
    """Cluster bootstrap 95% CI for the mean tau across baselines."""
    if not baseline_means:
        return 0.0, 0.0
    clusters: dict[str, list[int]] = {}
    for i, wid in enumerate(baseline_work_ids):
        clusters.setdefault(wid, []).append(i)
    cluster_keys = list(clusters.keys())
    n_clusters = len(cluster_keys)
    if n_clusters <= 1:
        m = float(np.mean(baseline_means))
        return m, m
    values_arr = np.array(baseline_means, dtype=float)
    boot = np.empty(BOOTSTRAP_SAMPLES)
    for b in range(BOOTSTRAP_SAMPLES):
        sampled = random.choices(cluster_keys, k=n_clusters)
        indices = [idx for key in sampled for idx in clusters[key]]
        boot[b] = np.mean(values_arr[indices])
    lo, hi = float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))
    return lo, hi


def _compute_rq1_metrics_for_alpha(
    all_songs: List[dict],
    query_list: List[Tuple[dict, int, int, List[int], List[int]]],
    alpha: float,
) -> Dict[str, dict]:
    """
    Reuse the RQ1 pipeline over a fixed query_list for a given alpha.

    Returns a dict with HR@1, HR@3, HR@5, MRR, each containing value and ci_95.
    """
    from experiment.run_rq1_experiment import filter_by_range as rq1_filter_by_range  # type: ignore
    from experiment.run_rq1_experiment import build_ideal_vector as rq1_build_ideal_vector  # type: ignore

    records: List[dict] = []
    for song, user_min, user_max, fav_midis, avoid_midis in query_list:
        filename = song.get("filename", "")
        filtered = rq1_filter_by_range(all_songs, user_min, user_max)
        ideal_vec = rq1_build_ideal_vector(user_min, user_max, fav_midis, avoid_midis)
        results = score_songs(
            filtered,
            ideal_vec,
            user_min,
            user_max,
            avoid_midis,
            fav_midis,
            alpha=alpha,
        )

        rank = None
        for r in results:
            if r["filename"] == filename:
                rank = r["rank"]
                break
        if rank is None:
            continue

        hit1 = 1 if rank == 1 else 0
        hit3 = 1 if rank <= 3 else 0
        hit5 = 1 if rank <= 5 else 0
        mrr = 1.0 / rank

        records.append(
            {
                "filename": filename,
                "rank": rank,
                "hit@1": hit1,
                "hit@3": hit3,
                "hit@5": hit5,
                "1/rank": mrr,
            }
        )

    n = len(records)
    if n == 0:
        return {
            "HR@1": {"value": 0.0, "ci_95": [0.0, 0.0]},
            "HR@3": {"value": 0.0, "ci_95": [0.0, 0.0]},
            "HR@5": {"value": 0.0, "ci_95": [0.0, 0.0]},
            "MRR": {"value": 0.0, "ci_95": [0.0, 0.0]},
        }

    hr1_vals = [r["hit@1"] for r in records]
    hr3_vals = [r["hit@3"] for r in records]
    hr5_vals = [r["hit@5"] for r in records]
    mrr_vals = [r["1/rank"] for r in records]

    hr1 = float(np.mean(hr1_vals))
    hr3 = float(np.mean(hr3_vals))
    hr5 = float(np.mean(hr5_vals))
    mrr = float(np.mean(mrr_vals))

    wids = [work_id(r["filename"]) for r in records]
    hr1_ci = _cluster_bootstrap_ci_mean(hr1_vals, wids)
    hr3_ci = _cluster_bootstrap_ci_mean(hr3_vals, wids)
    hr5_ci = _cluster_bootstrap_ci_mean(hr5_vals, wids)
    mrr_ci = _cluster_bootstrap_ci_mean(mrr_vals, wids)

    def _round_metric(val: float, ci: Tuple[float, float]) -> dict:
        return {
            "value": round(val, 4),
            "ci_95": [round(ci[0], 4), round(ci[1], 4)],
        }

    return {
        "HR@1": _round_metric(hr1, hr1_ci),
        "HR@3": _round_metric(hr3, hr3_ci),
        "HR@5": _round_metric(hr5, hr5_ci),
        "MRR": _round_metric(mrr, mrr_ci),
    }


def _run_one_baseline_for_alpha(
    all_songs: List[dict],
    user_min: int,
    user_max: int,
    fav_midis: List[int],
    avoid_midis: List[int],
    alpha: float,
) -> List[float]:
    """
    RQ2 baseline run for a given alpha.

    This mirrors _run_one_baseline from run_rq2_experiment.py but takes alpha
    as a parameter and returns only the list of tau values for that baseline.
    """
    filtered = filter_by_range(all_songs, user_min, user_max)
    ideal_vec = build_ideal_vector(user_min, user_max, fav_midis, avoid_midis)
    ranking_r0 = score_songs(
        filtered,
        ideal_vec,
        user_min,
        user_max,
        avoid_midis,
        fav_midis,
        alpha=alpha,
    )

    perturbations: List[Tuple[str, int, List[int], List[int]]] = []

    # Collect all MIDI notes that actually occur in the candidate set C
    used_midis_in_C: set[int] = set()
    for song in filtered:
        tess = song.get("tessituragram", {}) or {}
        used_midis_in_C.update(int(m) for m in tess.keys())

    midi_in_range = {m for m in used_midis_in_C if user_min <= m <= user_max}

    # 1. Add one favourite: MIDI in range, not already favourite or avoid
    for m in midi_in_range:
        if m not in fav_midis and m not in avoid_midis:
            perturbations.append(("add_fav", m, fav_midis + [m], avoid_midis))

    # 2. Remove one favourite: each favourite in turn
    for i, m in enumerate(fav_midis):
        new_fav = fav_midis[: i] + fav_midis[i + 1 :]
        perturbations.append(("remove_fav", m, new_fav, avoid_midis))

    # 3. Add one avoid: MIDI in range, not already avoid or favourite
    for m in midi_in_range:
        if m not in avoid_midis and m not in fav_midis:
            perturbations.append(("add_avoid", m, fav_midis, avoid_midis + [m]))

    # 4. Remove one avoid: each avoid in turn
    for i, m in enumerate(avoid_midis):
        new_avoid = avoid_midis[: i] + avoid_midis[i + 1 :]
        perturbations.append(("remove_avoid", m, fav_midis, new_avoid))

    tau_values: List[float] = []
    for pert_type, midi_changed, new_fav, new_avoid in perturbations:
        _ = pert_type  # unused label here; kept for parity with original function
        _ = midi_changed
        ideal_new = build_ideal_vector(user_min, user_max, new_fav, new_avoid)
        ranking_new = score_songs(
            filtered,
            ideal_new,
            user_min,
            user_max,
            new_avoid,
            new_fav,
            alpha=alpha,
        )
        tau = _compute_kendall_tau(ranking_r0, ranking_new)
        tau_values.append(tau)

    return tau_values


def _compute_rq2_metrics_for_alpha(
    all_songs: List[dict],
    baselines: List[Tuple[dict, int, int, List[int], List[int]]],
    alpha: float,
) -> Dict[str, float]:
    """
    Reuse the RQ2 pipeline over a fixed baseline set for a given alpha.

    Returns a dict mirroring the main RQ2 metrics section: mean_tau_overall,
    std_tau_overall, mean_tau_per_baseline, std_tau_across_baselines,
    ci_95_baseline_mean.
    """
    baseline_tau_lists: List[List[float]] = []
    baseline_work_ids: List[str] = []
    for song, user_min, user_max, fav_midis, avoid_midis in baselines:
        baseline_work_ids.append(work_id(song.get("filename", "")))
        tau_vals = _run_one_baseline_for_alpha(
            all_songs,
            user_min,
            user_max,
            fav_midis,
            avoid_midis,
            alpha=alpha,
        )
        baseline_tau_lists.append(tau_vals)

    all_tau_values = [t for lst in baseline_tau_lists for t in lst]
    n_perturbations = len(all_tau_values)

    if n_perturbations == 0:
        return {
            "mean_tau_overall": 0.0,
            "std_tau_overall": 0.0,
            "mean_tau_per_baseline": 0.0,
            "std_tau_across_baselines": 0.0,
            "ci_95_baseline_mean": [0.0, 0.0],
            "n_perturbations": 0,
            "n_baselines": len(baselines),
        }

    mean_tau_overall = float(np.mean(all_tau_values))
    std_tau_overall = (
        float(np.std(all_tau_values, ddof=1)) if n_perturbations > 1 else 0.0
    )

    baseline_means = [
        float(np.mean(tau_vals)) if tau_vals else 0.0
        for tau_vals in baseline_tau_lists
    ]
    mean_tau_per_baseline = float(np.mean(baseline_means)) if baseline_means else 0.0
    std_tau_across_baselines = (
        float(np.std(baseline_means, ddof=1)) if len(baseline_means) > 1 else 0.0
    )
    ci_lo, ci_hi = _cluster_bootstrap_ci_mean_over_baselines(baseline_means, baseline_work_ids)

    return {
        "mean_tau_overall": round(mean_tau_overall, 4),
        "std_tau_overall": round(std_tau_overall, 4),
        "mean_tau_per_baseline": round(mean_tau_per_baseline, 4),
        "std_tau_across_baselines": round(std_tau_across_baselines, 4),
        "ci_95_baseline_mean": [round(ci_lo, 4), round(ci_hi, 4)],
        "n_perturbations": n_perturbations,
        "n_baselines": len(baselines),
    }


def run_alpha_sensitivity(library_path: Path) -> dict:
    """
    Run alpha sensitivity analysis for RQ1 and RQ2.

    Reuses the same selection rules (and seeds) as the main RQ1/RQ2
    experiments to ensure the only changing variable is alpha.
    """
    all_songs = load_flat_library(library_path)

    # RQ1: build query list once using the same seed and selection rule.
    random.seed(RQ1_RANDOM_SEED)
    rq1_query_list, rq1_valid_pool_size = rq1_select_queries(all_songs)

    # RQ2: build baseline list once using the same seed and selection rule.
    random.seed(RQ2_RANDOM_SEED)
    rq2_baselines = rq2_select_baselines(all_songs)

    rq1_results: Dict[str, dict] = {}
    rq2_results: Dict[str, dict] = {}

    for alpha in ALPHA_VALUES:
        # RQ1 metrics for this alpha
        rq1_metrics_alpha = _compute_rq1_metrics_for_alpha(
            all_songs,
            rq1_query_list,
            alpha=alpha,
        )
        rq1_results[str(alpha)] = rq1_metrics_alpha

        # RQ2 metrics for this alpha
        rq2_metrics_alpha = _compute_rq2_metrics_for_alpha(
            all_songs,
            rq2_baselines,
            alpha=alpha,
        )
        rq2_results[str(alpha)] = rq2_metrics_alpha

    return {
        "experiment": "alpha_sensitivity",
        "description": (
            "Sensitivity of RQ1 and RQ2 metrics to the avoid-penalty weight alpha. "
            "For each alpha in {0.0, 0.25, 0.5, 0.75, 1.0}, we recompute HR@1, "
            "HR@3, HR@5, MRR (RQ1) and Kendall's tau (RQ2) using the same query "
            "and baseline selection rules as the main experiments."
        ),
        "alpha_values": ALPHA_VALUES,
        "parameters": {
            "alpha_values": ALPHA_VALUES,
            "bootstrap_samples": BOOTSTRAP_SAMPLES,
            "rq1_random_seed": RQ1_RANDOM_SEED,
            "rq1_n_queries_max": RQ1_N_QUERIES,
            "rq1_min_candidates": RQ1_MIN_CANDIDATES,
            "rq2_random_seed": RQ2_RANDOM_SEED,
            "rq2_n_baselines_target": RQ2_N_BASELINES,
            "rq2_min_candidates": RQ2_MIN_CANDIDATES,
            "library_path": str(Path("data/all_tessituragrams.json")),
        },
        "data_summary": {
            "total_flat_lines": len(all_songs),
            "n_unique_works": len({work_id(s["filename"]) for s in all_songs}),
            "n_multi_part_lines": sum(1 for s in all_songs if "__part_" in s.get("filename", "")),
            "bootstrap_method": "cluster (work-level)",
        },
        "rq1_setup": {
            "valid_query_pool_size": rq1_valid_pool_size,
            "queries_sampled": len(rq1_query_list),
            "n_unique_works_in_queries": len({work_id(q[0].get("filename", "")) for q in rq1_query_list}),
        },
        "rq2_setup": {
            "n_baselines": len(rq2_baselines),
            "n_unique_works_in_baselines": len({work_id(b[0].get("filename", "")) for b in rq2_baselines}),
        },
        "rq1_metrics": rq1_results,
        "rq2_metrics": rq2_results,
    }


def main() -> None:
    library_path = ROOT / "data" / "all_tessituragrams.json"
    out_dir = ROOT / "experiment_results"
    out_dir.mkdir(exist_ok=True)

    print("Running alpha sensitivity analysis for RQ1 and RQ2...")
    print(f"Library: {library_path}")

    results = run_alpha_sensitivity(library_path)

    out_json = out_dir / "alpha_sensitivity_results.json"
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to {out_json}")


if __name__ == "__main__":
    main()

