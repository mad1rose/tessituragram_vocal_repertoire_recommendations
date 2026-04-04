"""
Experiment 1 — Alpha sensitivity (101-line library, tessituragrams.json).

Sweeps α ∈ {0.0, 0.25, 0.5, 0.75, 1.0} for RQ1 (same 50-query draw as
old_run_rq1_experiment.py) and RQ2 (same five baselines as old_RQ2_results.json / Table 3).

Output: previous_paper_and_experiments/previous_experiment_results/old_alpha_sensitivity_results.json

Does not import experiment/run_rq1_experiment.py or experiment/run_rq2_experiment.py.
"""

from __future__ import annotations

import importlib.util
import json
import random
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[2]
_sys_path = list(__import__("sys").path)
if str(REPO_ROOT) not in _sys_path:
    __import__("sys").path.insert(0, str(REPO_ROOT))

from src.storage import load_tessituragrams  # noqa: E402
from src.recommend import (  # noqa: E402
    filter_by_range,
    build_ideal_vector,
    score_songs,
)

from exp1_common import (  # noqa: E402
    RANDOM_SEED as RQ1_RANDOM_SEED,
    N_QUERIES as RQ1_N_QUERIES_MAX,
    MIN_CANDIDATES as RQ1_MIN_CANDIDATES,
    select_queries,
)

_exp1_rq2_spec = importlib.util.spec_from_file_location(
    "_exp1_rq2_alpha",
    SCRIPT_DIR / "old_run_rq2_experiment.py",
)
assert _exp1_rq2_spec and _exp1_rq2_spec.loader
_exp1_rq2 = importlib.util.module_from_spec(_exp1_rq2_spec)
_exp1_rq2_spec.loader.exec_module(_exp1_rq2)

_compute_kendall_tau = _exp1_rq2._compute_kendall_tau
_derive_synthetic_profile = _exp1_rq2._derive_synthetic_profile

ALPHA_VALUES: List[float] = [0.0, 0.25, 0.5, 0.75, 1.0]
BOOTSTRAP_SAMPLES = 10_000

RESULTS_DIR = REPO_ROOT / "previous_paper_and_experiments" / "previous_experiment_results"
LIBRARY_PATH = REPO_ROOT / "data" / "tessituragrams.json"
# Canonical RQ2 run (Table 3): load the same five baselines so α-sensitivity τ uses
# the same 130 perturbations as old_run_rq2_experiment / old_RQ2_results.json.
CANONICAL_RQ2_JSON = RESULTS_DIR / "old_RQ2_results.json"


def _load_rq2_baselines_from_canonical_rq2_json(
    all_songs: List[dict],
    canonical_path: Path,
) -> Tuple[List[Tuple[dict, int, int, List[int], List[int]]], List[str]]:
    """Rebuild baseline tuples from archived RQ2 output (order-preserving)."""
    with canonical_path.open(encoding="utf-8") as f:
        data = json.load(f)
    by_filename = {s.get("filename"): s for s in all_songs}
    out: List[Tuple[dict, int, int, List[int], List[int]]] = []
    order: List[str] = []
    for bp in data.get("baseline_profiles", []):
        fn = bp.get("source_song")
        if not fn:
            continue
        order.append(fn)
        song = by_filename.get(fn)
        if song is None:
            raise KeyError(
                f"Baseline {fn!r} from {canonical_path} not found in {LIBRARY_PATH}"
            )
        umin, umax, fav, avoid = _derive_synthetic_profile(song)
        out.append((song, umin, umax, fav, avoid))
    if not out:
        raise ValueError(f"No baseline_profiles in {canonical_path}")
    return out, order


def _bootstrap_ci_mean(values: List[float]) -> Tuple[float, float]:
    if not values:
        return 0.0, 0.0
    arr = np.array(values, dtype=float)
    if len(arr) == 1:
        m = float(arr[0])
        return m, m
    boot = np.array(
        [
            float(np.mean(random.choices(arr, k=len(arr))))
            for _ in range(BOOTSTRAP_SAMPLES)
        ]
    )
    lo, hi = float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))
    return lo, hi


def _bootstrap_ci_mean_over_baselines(baseline_means: List[float]) -> Tuple[float, float]:
    if not baseline_means:
        return 0.0, 0.0
    if len(baseline_means) == 1:
        m = float(baseline_means[0])
        return m, m
    arr = np.array(baseline_means, dtype=float)
    boot = np.array(
        [
            float(np.mean(random.choices(arr, k=len(arr))))
            for _ in range(BOOTSTRAP_SAMPLES)
        ]
    )
    lo, hi = float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))
    return lo, hi


def _compute_rq1_metrics_for_alpha(
    all_songs: List[dict],
    query_list: List[Tuple[dict, int, int, List[int], List[int]]],
    alpha: float,
) -> Dict[str, dict]:
    records: List[dict] = []
    for song, user_min, user_max, fav_midis, avoid_midis in query_list:
        filename = song.get("filename", "")
        filtered = filter_by_range(all_songs, user_min, user_max)
        ideal_vec = build_ideal_vector(user_min, user_max, fav_midis, avoid_midis)
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

    hr1_ci = _bootstrap_ci_mean(hr1_vals)
    hr3_ci = _bootstrap_ci_mean(hr3_vals)
    hr5_ci = _bootstrap_ci_mean(hr5_vals)
    mrr_ci = _bootstrap_ci_mean(mrr_vals)

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

    used_midis_in_C: set[int] = set()
    for song in filtered:
        tess = song.get("tessituragram", {}) or {}
        used_midis_in_C.update(int(m) for m in tess.keys())

    midi_in_range = {m for m in used_midis_in_C if user_min <= m <= user_max}

    for m in midi_in_range:
        if m not in fav_midis and m not in avoid_midis:
            perturbations.append(("add_fav", m, fav_midis + [m], avoid_midis))

    for i, m in enumerate(fav_midis):
        new_fav = fav_midis[:i] + fav_midis[i + 1 :]
        perturbations.append(("remove_fav", m, new_fav, avoid_midis))

    for m in midi_in_range:
        if m not in avoid_midis and m not in fav_midis:
            perturbations.append(("add_avoid", m, fav_midis, avoid_midis + [m]))

    for i, m in enumerate(avoid_midis):
        new_avoid = avoid_midis[:i] + avoid_midis[i + 1 :]
        perturbations.append(("remove_avoid", m, fav_midis, new_avoid))

    tau_values: List[float] = []
    for pert_type, midi_changed, new_fav, new_avoid in perturbations:
        _ = pert_type
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
    baseline_tau_lists: List[List[float]] = []
    for song, user_min, user_max, fav_midis, avoid_midis in baselines:
        _ = song
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
    ci_lo, ci_hi = _bootstrap_ci_mean_over_baselines(baseline_means)

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
    all_songs = load_tessituragrams(library_path)

    random.seed(RQ1_RANDOM_SEED)
    rq1_query_list, rq1_valid_pool_size = select_queries(all_songs, filter_by_range)

    rq2_baselines, rq2_baseline_filenames = _load_rq2_baselines_from_canonical_rq2_json(
        all_songs, CANONICAL_RQ2_JSON
    )

    rq1_results: Dict[str, dict] = {}
    rq2_results: Dict[str, dict] = {}

    for alpha in ALPHA_VALUES:
        rq1_results[str(alpha)] = _compute_rq1_metrics_for_alpha(
            all_songs, rq1_query_list, alpha=alpha
        )
        rq2_results[str(alpha)] = _compute_rq2_metrics_for_alpha(
            all_songs, rq2_baselines, alpha=alpha
        )

    return {
        "experiment": "alpha_sensitivity",
        "experiment_phase": "Experiment_1_small_library",
        "description": (
            "Sensitivity of RQ1 and RQ2 metrics to α on the 101-line library. "
            "RQ1: same 50-query draw as old_run_rq1_experiment (seed 42). "
            "RQ2: same five baseline profiles as old_RQ2_results.json (Table 3), "
            "not a fresh random.sample — ensures 130 perturbations match the main RQ2 run."
        ),
        "alpha_values": ALPHA_VALUES,
        "parameters": {
            "alpha_values": ALPHA_VALUES,
            "bootstrap_samples": BOOTSTRAP_SAMPLES,
            "rq1_random_seed": RQ1_RANDOM_SEED,
            "rq1_n_queries_max": RQ1_N_QUERIES_MAX,
            "rq1_min_candidates": RQ1_MIN_CANDIDATES,
            "rq2_baselines_source": "old_RQ2_results.json (baseline_profiles.source_song)",
            "rq2_n_baselines_target": _exp1_rq2.N_BASELINES,
            "rq2_min_candidates": _exp1_rq2.MIN_CANDIDATES,
            "library_path": "data/tessituragrams.json",
            "bootstrap_method": "i.i.d. (query-level / baseline-level resampling)",
        },
        "rq1_setup": {
            "valid_query_pool_size": rq1_valid_pool_size,
            "queries_sampled": len(rq1_query_list),
        },
        "rq2_setup": {
            "n_baselines": len(rq2_baselines),
            "baseline_source_filenames_in_order": rq2_baseline_filenames,
        },
        "rq1_metrics": rq1_results,
        "rq2_metrics": rq2_results,
    }


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Experiment 1 — Alpha sensitivity")
    print(f"Library: {LIBRARY_PATH}")

    results = run_alpha_sensitivity(LIBRARY_PATH)

    out_json = RESULTS_DIR / "old_alpha_sensitivity_results.json"
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to {out_json}")


if __name__ == "__main__":
    main()
