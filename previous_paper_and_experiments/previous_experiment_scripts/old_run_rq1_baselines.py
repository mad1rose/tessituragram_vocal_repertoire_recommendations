"""
Experiment 1 — RQ1 baselines (101-line library).

Same query draw as old_run_rq1_experiment.py (global random seed 42, N_QUERIES=50).
Bootstrap CIs use i.i.d. resampling after that same seed; no separate bootstrap seed 43.
Writes previous_paper_and_experiments/previous_experiment_results/old_RQ1_baselines.json.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from exp1_common import (
    REPO_ROOT,
    setup_sys_path,
    N_QUERIES,
    MIN_CANDIDATES,
    RANDOM_SEED,
    select_queries,
)

setup_sys_path()

from src.storage import load_tessituragrams  # noqa: E402
from src.recommend import (  # noqa: E402
    filter_by_range,
    build_ideal_vector,
    score_songs,
)
from experiment.rq1_pool_stats import (  # noqa: E402
    compute_candidate_pool_summary,
    stratify_rq1_by_pool_size,
)

ALPHA_FULL = 0.5
BOOTSTRAP_SAMPLES = 10_000
RANDOM_SEED_NULL_BASELINE = RANDOM_SEED + 10_000

RESULTS_DIR = REPO_ROOT / "previous_paper_and_experiments" / "previous_experiment_results"
LIBRARY_PATH = REPO_ROOT / "data" / "tessituragrams.json"


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


def _run_models_for_query(
    all_songs: List[dict],
    song: dict,
    user_min: int,
    user_max: int,
    fav_midis: List[int],
    avoid_midis: List[int],
    rng_random_rank: random.Random,
) -> Dict[str, Dict[str, float]]:
    filename = song.get("filename", "")
    filtered = filter_by_range(all_songs, user_min, user_max)
    if len(filtered) < 2:
        return {}

    ideal_vec = build_ideal_vector(user_min, user_max, fav_midis, avoid_midis)
    per_model: Dict[str, Dict[str, float]] = {}

    results_full = score_songs(
        filtered,
        ideal_vec,
        user_min,
        user_max,
        avoid_midis,
        fav_midis,
        alpha=ALPHA_FULL,
    )
    rank_full: int | None = None
    for r in results_full:
        if r["filename"] == filename:
            rank_full = int(r["rank"])
            break
    if rank_full is not None:
        per_model["full"] = {
            "rank": float(rank_full),
            "hit@1": 1.0 if rank_full == 1 else 0.0,
            "hit@3": 1.0 if rank_full <= 3 else 0.0,
            "hit@5": 1.0 if rank_full <= 5 else 0.0,
            "1/rank": 1.0 / float(rank_full),
        }

    results_cos = score_songs(
        filtered,
        ideal_vec,
        user_min,
        user_max,
        avoid_midis,
        fav_midis,
        alpha=0.0,
    )
    rank_cos: int | None = None
    for r in results_cos:
        if r["filename"] == filename:
            rank_cos = int(r["rank"])
            break
    if rank_cos is not None:
        per_model["cosine_only"] = {
            "rank": float(rank_cos),
            "hit@1": 1.0 if rank_cos == 1 else 0.0,
            "hit@3": 1.0 if rank_cos <= 3 else 0.0,
            "hit@5": 1.0 if rank_cos <= 5 else 0.0,
            "1/rank": 1.0 / float(rank_cos),
        }

    perm = [s.get("filename", "") for s in filtered]
    rng_random_rank.shuffle(perm)
    try:
        rank_rand = perm.index(filename) + 1
    except ValueError:
        rank_rand = len(perm)
    per_model["null_random"] = {
        "rank": float(rank_rand),
        "hit@1": 1.0 if rank_rand == 1 else 0.0,
        "hit@3": 1.0 if rank_rand <= 3 else 0.0,
        "hit@5": 1.0 if rank_rand <= 5 else 0.0,
        "1/rank": 1.0 / float(rank_rand),
    }

    return per_model


def run_rq1_baselines(library_path: Path) -> dict:
    all_songs = load_tessituragrams(library_path)

    random.seed(RANDOM_SEED)
    query_list, valid_pool_size = select_queries(all_songs, filter_by_range)

    per_query: List[dict] = []
    rng_random_rank = random.Random(RANDOM_SEED_NULL_BASELINE)

    for song, user_min, user_max, fav_midis, avoid_midis in query_list:
        rng_q = random.Random(rng_random_rank.randint(0, 2**31 - 1))
        per_model = _run_models_for_query(
            all_songs,
            song,
            user_min,
            user_max,
            fav_midis,
            avoid_midis,
            rng_q,
        )
        if not per_model:
            continue

        record = {
            "filename": song.get("filename", ""),
            "composer": song.get("composer"),
            "title": song.get("title"),
            "n_candidates": len(filter_by_range(all_songs, user_min, user_max)),
            "models": per_model,
        }
        per_query.append(record)

    n = len(per_query)
    nc_list = [int(rec["n_candidates"]) for rec in per_query]
    pool_summary = compute_candidate_pool_summary(nc_list) if nc_list else {}
    stratification = stratify_rq1_by_pool_size(
        per_query,
        bins=[
            (2, 20, "2 <= |C| <= 20"),
            (21, None, "|C| >= 21"),
        ],
    )

    def _collect(model_name: str, key: str) -> List[float]:
        vals: List[float] = []
        for rec in per_query:
            m = rec["models"].get(model_name)
            if m is not None:
                vals.append(float(m[key]))
        return vals

    models = ["full", "null_random", "cosine_only"]
    metrics: Dict[str, dict] = {}

    for model in models:
        hit1_vals = _collect(model, "hit@1")
        if not hit1_vals:
            metrics[model] = {
                "HR@1": {"value": 0.0, "ci_95": [0.0, 0.0]},
                "HR@3": {"value": 0.0, "ci_95": [0.0, 0.0]},
                "HR@5": {"value": 0.0, "ci_95": [0.0, 0.0]},
                "MRR": {"value": 0.0, "ci_95": [0.0, 0.0]},
            }
            continue

        hit3_vals = _collect(model, "hit@3")
        hit5_vals = _collect(model, "hit@5")
        mrr_vals = _collect(model, "1/rank")

        hr1 = float(np.mean(hit1_vals))
        hr3 = float(np.mean(hit3_vals))
        hr5 = float(np.mean(hit5_vals))
        mrr = float(np.mean(mrr_vals))

        hr1_ci = _bootstrap_ci_mean(hit1_vals)
        hr3_ci = _bootstrap_ci_mean(hit3_vals)
        hr5_ci = _bootstrap_ci_mean(hit5_vals)
        mrr_ci = _bootstrap_ci_mean(mrr_vals)

        def _round_metric(val: float, ci: Tuple[float, float]) -> dict:
            return {
                "value": round(val, 4),
                "ci_95": [round(ci[0], 4), round(ci[1], 4)],
            }

        metrics[model] = {
            "HR@1": _round_metric(hr1, hr1_ci),
            "HR@3": _round_metric(hr3, hr3_ci),
            "HR@5": _round_metric(hr5, hr5_ci),
            "MRR": _round_metric(mrr, mrr_ci),
        }

    diff_hr1: List[float] = []
    diff_hr3: List[float] = []
    diff_hr5: List[float] = []
    diff_mrr: List[float] = []
    for rec in per_query:
        mf = rec["models"].get("full")
        mc = rec["models"].get("cosine_only")
        if mf is None or mc is None:
            continue
        diff_hr1.append(float(mf["hit@1"]) - float(mc["hit@1"]))
        diff_hr3.append(float(mf["hit@3"]) - float(mc["hit@3"]))
        diff_hr5.append(float(mf["hit@5"]) - float(mc["hit@5"]))
        diff_mrr.append(float(mf["1/rank"]) - float(mc["1/rank"]))

    paired: Dict[str, dict] = {}
    if diff_hr1:
        d1, c1 = float(np.mean(diff_hr1)), _bootstrap_ci_mean(diff_hr1)
        d3, c3 = float(np.mean(diff_hr3)), _bootstrap_ci_mean(diff_hr3)
        d5, c5 = float(np.mean(diff_hr5)), _bootstrap_ci_mean(diff_hr5)
        dm, cm = float(np.mean(diff_mrr)), _bootstrap_ci_mean(diff_mrr)
        paired = {
            "description": (
                "Per-query difference (full − cosine_only); same query draw; "
                "i.i.d. bootstrap on differences."
            ),
            "HR@1": {"mean_diff": round(d1, 4), "ci_95": [round(c1[0], 4), round(c1[1], 4)]},
            "HR@3": {"mean_diff": round(d3, 4), "ci_95": [round(c3[0], 4), round(c3[1], 4)]},
            "HR@5": {"mean_diff": round(d5, 4), "ci_95": [round(c5[0], 4), round(c5[1], 4)]},
            "MRR": {"mean_diff": round(dm, 4), "ci_95": [round(cm[0], 4), round(cm[1], 4)]},
        }

    return {
        "experiment": "RQ1_baselines",
        "experiment_phase": "Experiment_1_small_library",
        "description": (
            "Baselines for RQ1 oracle self-retrieval (identifiability): full, cosine-only, null random. "
            "Same query rule as old_run_rq1_experiment.py (seed 42, N=50)."
        ),
        "parameters": {
            "alpha_full": ALPHA_FULL,
            "bootstrap_samples": BOOTSTRAP_SAMPLES,
            "random_seed_queries": RANDOM_SEED,
            "random_seed_null_baseline_stream": RANDOM_SEED_NULL_BASELINE,
            "min_candidates": MIN_CANDIDATES,
            "n_queries_max": N_QUERIES,
            "library_path": "data/tessituragrams.json",
        },
        "data_summary": {
            "total_songs_in_library": len(all_songs),
            "valid_query_pool_size": valid_pool_size,
            "queries_sampled": n,
            "random_sampling": True,
            "bootstrap_method": "i.i.d. (query-level resampling)",
            "candidate_pool_summary": pool_summary,
        },
        "descriptive_stratification_hr1_by_pool_size": {
            "note": (
                "Point estimates only (no CIs). Null P(top-1)=1/|C| per query."
            ),
            "bins": stratification,
        },
        "models": ["full", "null_random", "cosine_only"],
        "model_descriptions": {
            "full": "Range filter + cosine − α×avoid (α = 0.5).",
            "null_random": "Range filter + uniform random ranking.",
            "cosine_only": "Range filter + cosine only (α = 0).",
        },
        "metrics": metrics,
        "paired_full_minus_cosine": paired,
        "per_query": per_query,
    }


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Experiment 1 — RQ1 baselines")
    print(f"Library: {LIBRARY_PATH}")

    results = run_rq1_baselines(LIBRARY_PATH)

    out_json = RESULTS_DIR / "old_RQ1_baselines.json"
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to {out_json}")

    m = results["metrics"]
    for model_name in ["full", "null_random", "cosine_only"]:
        mm = m[model_name]
        print(
            f"{model_name:12s} HR@1 = {mm['HR@1']['value']}  "
            f"CI: {mm['HR@1']['ci_95']}  |  MRR = {mm['MRR']['value']}"
        )


if __name__ == "__main__":
    main()
