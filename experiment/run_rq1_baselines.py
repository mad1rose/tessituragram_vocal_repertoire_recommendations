"""
Baselines for Research Question 1: Self-retrieval accuracy.

We compare three models, using the same random query sampling rule as
`run_rq1_experiment.py`:

- full:        range filter + cosine similarity − α × avoid_penalty (α = 0.5)
- null_random: range filter only, then a completely random ranking (null model)
- cosine_only: range filter + cosine similarity only (α = 0.0; no avoid penalty)

For each model we compute HR@1, HR@3, HR@5, and MRR with 95% bootstrap
confidence intervals over the sampled queries. This helps contextualise the
main RQ1 result: how much better is the full model than trivial or ablated
alternatives.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

# Allow running from project root or from experiment folder
ROOT = Path(__file__).resolve().parent.parent
_sys_path = list(__import__("sys").path)
if str(ROOT) not in _sys_path:
    __import__("sys").path.insert(0, str(ROOT))

from src.storage import load_tessituragrams  # noqa: E402
from src.recommend import (  # noqa: E402
    filter_by_range,
    build_ideal_vector,
    score_songs,
)
from experiment.run_rq1_experiment import (  # noqa: E402
    _select_queries as rq1_select_queries,
    RANDOM_SEED as RQ1_RANDOM_SEED,
    MIN_CANDIDATES as RQ1_MIN_CANDIDATES,
    N_QUERIES as RQ1_N_QUERIES,
)


ALPHA_FULL = 0.5
BOOTSTRAP_SAMPLES = 10_000


def _bootstrap_ci_mean(values: List[float]) -> Tuple[float, float]:
    """Bootstrap 95% CI for the mean of a list of values."""
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
    """
    For a single query song, run all three models and return per-model metrics.

    Returns a dict mapping model_name -> per-query metrics:
        {
            "full":        {"rank": ..., "hit@1": ..., "hit@3": ..., "hit@5": ..., "1/rank": ...},
            "null_random": {...},
            "cosine_only": {...},
        }
    """
    filename = song.get("filename", "")
    filtered = filter_by_range(all_songs, user_min, user_max)
    if len(filtered) < 2:
        # Not a valid query under the RQ1 rule; caller should not pass these,
        # but be defensive.
        return {}

    # Ideal vector from favourites/avoids (same rule as main RQ1 experiment)
    ideal_vec = build_ideal_vector(user_min, user_max, fav_midis, avoid_midis)

    per_model: Dict[str, Dict[str, float]] = {}

    # 1) Full model (α = 0.5)
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

    # 2) Cosine-only model (α = 0.0)
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

    # 3) Range-only + random ranking (null model)
    filenames = [s.get("filename", "") for s in filtered]
    # Generate a reproducible random permutation using the provided RNG
    perm = filenames[:]
    rng_random_rank.shuffle(perm)
    try:
        rank_rand = perm.index(filename) + 1
    except ValueError:
        # Should not happen if the query song is in the filtered set
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
    """
    Run RQ1 baselines over the same random query-sampling rule as
    `run_rq1_experiment.py`.

    Returns a results dict with per-model summary metrics and per-query detail.
    """
    all_songs = load_tessituragrams(library_path)

    # Build query list once, using the same seed and selection rule as RQ1.
    random.seed(RQ1_RANDOM_SEED)
    query_list, valid_pool_size = rq1_select_queries(all_songs)

    per_query: List[dict] = []

    # Separate RNG for the random-ranking baseline so it is reproducible and
    # independent of any bootstrap resampling calls.
    rng_random_rank = random.Random(RQ1_RANDOM_SEED + 10_000)

    for idx, (song, user_min, user_max, fav_midis, avoid_midis) in enumerate(
        query_list
    ):
        # Derive a per-query RNG state for the random baseline so that results
        # are reproducible but independent across queries.
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
        ranks = _collect(model, "rank")
        if not ranks:
            metrics[model] = {
                "HR@1": {"value": 0.0, "ci_95": [0.0, 0.0]},
                "HR@3": {"value": 0.0, "ci_95": [0.0, 0.0]},
                "HR@5": {"value": 0.0, "ci_95": [0.0, 0.0]},
                "MRR": {"value": 0.0, "ci_95": [0.0, 0.0]},
            }
            continue

        hit1_vals = _collect(model, "hit@1")
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

    return {
        "experiment": "RQ1_baselines",
        "description": (
            "Baselines for RQ1 self-retrieval accuracy: full model "
            "(range + cosine − α×avoid), cosine-only (α = 0), and "
            "range-only + random ranking (null). Uses the same random "
            "query pool definition and sampling rule as run_rq1_experiment.py."
        ),
        "parameters": {
            "alpha_full": ALPHA_FULL,
            "bootstrap_samples": BOOTSTRAP_SAMPLES,
            "random_seed_queries": RQ1_RANDOM_SEED,
            "min_candidates": RQ1_MIN_CANDIDATES,
            "n_queries_max": RQ1_N_QUERIES,
            "library_path": str(Path("data/tessituragrams.json")),
        },
        "data_summary": {
            "total_songs_in_library": len(all_songs),
            "valid_query_pool_size": valid_pool_size,
            "queries_sampled": n,
            "random_sampling": True,
        },
        "models": ["full", "null_random", "cosine_only"],
        "model_descriptions": {
            "full": "Range filter + cosine similarity − α×avoid_penalty (α = 0.5).",
            "null_random": "Range filter only, then a completely random ranking over the candidate set (null model).",
            "cosine_only": "Range filter + cosine similarity only (α = 0.0; avoid list ignored in scoring).",
        },
        "metrics": metrics,
        "per_query": per_query,
    }


def main() -> None:
    library_path = ROOT / "data" / "tessituragrams.json"
    out_dir = ROOT / "experiment_results"
    out_dir.mkdir(exist_ok=True)

    print("Running RQ1 Self-Retrieval Baselines (full vs cosine-only vs random)...")
    print(f"Library: {library_path}")

    results = run_rq1_baselines(library_path)

    out_json = out_dir / "RQ1_baselines.json"
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to {out_json}")

    m = results["metrics"]
    print("\n--- Summary (HR@1 / MRR) ---")
    for model_name in ["full", "null_random", "cosine_only"]:
        mm = m[model_name]
        print(
            f"{model_name:12s} "
            f"HR@1 = {mm['HR@1']['value']}  CI: {mm['HR@1']['ci_95']}  |  "
            f"MRR = {mm['MRR']['value']}  CI: {mm['MRR']['ci_95']}"
        )


if __name__ == "__main__":
    main()

