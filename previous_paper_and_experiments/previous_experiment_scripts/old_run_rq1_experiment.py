"""
Experiment 1 — RQ1 oracle self-retrieval (101-line library, tessituragrams.json).

Outputs to previous_paper_and_experiments/previous_experiment_results/old_RQ1_results.json
Does not use experiment/run_rq1_experiment.py (Experiment 2 uses N_QUERIES=200 and
all_tessituragrams.json).

Bootstrap: i.i.d. resampling of query-level outcomes (Efron & Tibshirani, 1993), appropriate
when each query is one independent line (one vocal line per composition in this library).
After random.seed(42), query selection consumes RNG state; the bootstrap loop uses the
continuation of that global stream (no separate bootstrap seed 43).
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np

from exp1_common import (
    REPO_ROOT,
    setup_sys_path,
    N_QUERIES,
    MIN_CANDIDATES,
    RANDOM_SEED,
    TOP_N_FAV,
    BOTTOM_N_AVOID,
    select_queries,
)

setup_sys_path()

from src.storage import load_tessituragrams  # noqa: E402
from src.recommend import (  # noqa: E402
    filter_by_range,
    build_ideal_vector,
    score_songs,
)
from experiment.rq1_pool_stats import compute_candidate_pool_summary  # noqa: E402

ALPHA = 0.5
BOOTSTRAP_SAMPLES = 10_000

RESULTS_DIR = REPO_ROOT / "previous_paper_and_experiments" / "previous_experiment_results"
LIBRARY_PATH = REPO_ROOT / "data" / "tessituragrams.json"


def run_rq1_experiment(library_path: Path) -> dict:
    random.seed(RANDOM_SEED)
    all_songs = load_tessituragrams(library_path)

    query_list, valid_pool_size = select_queries(all_songs, filter_by_range)
    records: list[dict] = []

    for song, user_min, user_max, fav_midis, avoid_midis in query_list:
        filename = song.get("filename", "")
        filtered = filter_by_range(all_songs, user_min, user_max)
        n_candidates = len(filtered)
        ideal_vec = build_ideal_vector(user_min, user_max, fav_midis, avoid_midis)
        results = score_songs(
            filtered,
            ideal_vec,
            user_min,
            user_max,
            avoid_midis,
            fav_midis,
            alpha=ALPHA,
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
                "composer": song.get("composer"),
                "title": song.get("title"),
                "n_candidates": n_candidates,
                "rank": rank,
                "hit@1": hit1,
                "hit@3": hit3,
                "hit@5": hit5,
                "1/rank": mrr,
            }
        )

    n = len(records)

    hr1 = np.mean([r["hit@1"] for r in records]) if n else 0.0
    hr3 = np.mean([r["hit@3"] for r in records]) if n else 0.0
    hr5 = np.mean([r["hit@5"] for r in records]) if n else 0.0
    mrr = np.mean([r["1/rank"] for r in records]) if n else 0.0

    def bootstrap_mean(
        values: list[float], n_samples: int = BOOTSTRAP_SAMPLES
    ) -> tuple[float, float]:
        boot = np.array(
            [
                float(np.mean(random.choices(values, k=len(values))))
                for _ in range(n_samples)
            ]
        )
        lo, hi = float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))
        return lo, hi

    hr1_ci = bootstrap_mean([r["hit@1"] for r in records]) if n else (0.0, 0.0)
    hr3_ci = bootstrap_mean([r["hit@3"] for r in records]) if n else (0.0, 0.0)
    hr5_ci = bootstrap_mean([r["hit@5"] for r in records]) if n else (0.0, 0.0)
    mrr_ci = bootstrap_mean([r["1/rank"] for r in records]) if n else (0.0, 0.0)

    nc_list = [int(r["n_candidates"]) for r in records]
    pool_summary = compute_candidate_pool_summary(nc_list) if nc_list else {}

    return {
        "experiment": "RQ1_self_retrieval_accuracy",
        "experiment_phase": "Experiment_1_small_library",
        "description": (
            "Synthetic self-retrieval: profile derived from one vocal line; "
            "does the system rank that same line first or in the top 3/5?"
        ),
        "parameters": {
            "alpha": ALPHA,
            "top_n_favorite": TOP_N_FAV,
            "bottom_n_avoid": BOTTOM_N_AVOID,
            "min_candidates": MIN_CANDIDATES,
            "n_queries_max": N_QUERIES,
            "bootstrap_samples": BOOTSTRAP_SAMPLES,
            "random_seed": RANDOM_SEED,
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
        "metrics": {
            "HR@1": {"value": round(hr1, 4), "ci_95": [round(hr1_ci[0], 4), round(hr1_ci[1], 4)]},
            "HR@3": {"value": round(hr3, 4), "ci_95": [round(hr3_ci[0], 4), round(hr3_ci[1], 4)]},
            "HR@5": {"value": round(hr5, 4), "ci_95": [round(hr5_ci[0], 4), round(hr5_ci[1], 4)]},
            "MRR": {"value": round(mrr, 4), "ci_95": [round(mrr_ci[0], 4), round(mrr_ci[1], 4)]},
        },
        "formulas": {
            "HR@1": "fraction of queries where the query line was ranked 1",
            "HR@3": "fraction of queries where the query line was in top 3",
            "HR@5": "fraction of queries where the query line was in top 5",
            "MRR": "mean of 1/rank across queries (1 = best, rewards higher ranks)",
        },
        "per_query": records,
    }


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Experiment 1 — RQ1 oracle self-retrieval (101-line library)")
    print(f"Library: {LIBRARY_PATH}")

    results = run_rq1_experiment(LIBRARY_PATH)

    out_json = RESULTS_DIR / "old_RQ1_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to {out_json}")

    m = results["metrics"]
    print("\n--- Metrics ---")
    print(f"HR@1: {m['HR@1']['value']}  [95% CI: {m['HR@1']['ci_95']}]")
    print(f"HR@3: {m['HR@3']['value']}  [95% CI: {m['HR@3']['ci_95']}]")
    print(f"HR@5: {m['HR@5']['value']}  [95% CI: {m['HR@5']['ci_95']}]")
    print(f"MRR:  {m['MRR']['value']}  [95% CI: {m['MRR']['ci_95']}]")


if __name__ == "__main__":
    main()
