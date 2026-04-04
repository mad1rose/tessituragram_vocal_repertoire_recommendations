"""
Baselines for Research Question 1: Oracle self-retrieval / identifiability (Experiment 2).

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
import warnings
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

# Allow running from project root or from experiment folder
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
    RANDOM_SEED_BOOTSTRAP as RQ1_RANDOM_SEED_BOOTSTRAP,
    MIN_CANDIDATES as RQ1_MIN_CANDIDATES,
    N_QUERIES as RQ1_N_QUERIES,
)
from experiment.rq1_pool_stats import (  # noqa: E402
    compute_candidate_pool_summary,
    stratify_rq1_by_pool_size,
)


ALPHA_FULL = 0.5
BOOTSTRAP_SAMPLES = 10_000
# Dedicated stream for null-model shuffles (independent of query and bootstrap RNG).
RANDOM_SEED_NULL_BASELINE = RQ1_RANDOM_SEED + 10_000


def _cluster_bootstrap_ci_mean(
    values: List[float],
    cluster_ids: List[str],
    rng: random.Random,
) -> Tuple[float, float]:
    """Cluster bootstrap 95% CI for the mean.

    Resamples work-level clusters rather than individual observations to
    preserve intra-work correlation (Cameron et al., 2008).
    """
    if not values:
        return 0.0, 0.0
    if len(values) != len(cluster_ids):
        raise ValueError(
            f"cluster bootstrap: len(values)={len(values)} != len(cluster_ids)={len(cluster_ids)}"
        )
    clusters: dict[str, list[int]] = {}
    for i, cid in enumerate(cluster_ids):
        clusters.setdefault(cid, []).append(i)
    cluster_keys = list(clusters.keys())
    n_clusters = len(cluster_keys)
    if n_clusters <= 1:
        warnings.warn(
            "cluster_bootstrap: only one cluster; CI equals point estimate",
            UserWarning,
            stacklevel=2,
        )
        m = float(np.mean(values))
        return m, m
    values_arr = np.array(values, dtype=float)
    boot = np.empty(BOOTSTRAP_SAMPLES)
    for b in range(BOOTSTRAP_SAMPLES):
        sampled = rng.choices(cluster_keys, k=n_clusters)
        indices = [idx for key in sampled for idx in clusters[key]]
        boot[b] = np.mean(values_arr[indices])
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
    all_songs = load_flat_library(library_path)

    rng_queries = random.Random(RQ1_RANDOM_SEED)
    rng_bootstrap = random.Random(RQ1_RANDOM_SEED_BOOTSTRAP)
    query_list, valid_pool_size = rq1_select_queries(all_songs, rng_queries)

    per_query: List[dict] = []

    # Separate RNG for the random-ranking baseline so it is reproducible and
    # independent of query-draw and bootstrap streams.
    rng_random_rank = random.Random(RANDOM_SEED_NULL_BASELINE)

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

        wids = [work_id(rec["filename"]) for rec in per_query if model in rec["models"]]
        assert len(hit1_vals) == len(wids)
        assert len(hit3_vals) == len(wids)
        assert len(hit5_vals) == len(wids)
        assert len(mrr_vals) == len(wids)
        hr1_ci = _cluster_bootstrap_ci_mean(hit1_vals, wids, rng_bootstrap)
        hr3_ci = _cluster_bootstrap_ci_mean(hit3_vals, wids, rng_bootstrap)
        hr5_ci = _cluster_bootstrap_ci_mean(hit5_vals, wids, rng_bootstrap)
        mrr_ci = _cluster_bootstrap_ci_mean(mrr_vals, wids, rng_bootstrap)

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

    # Paired full − cosine: same queries; cluster bootstrap on per-query differences.
    diff_hr1: List[float] = []
    diff_hr3: List[float] = []
    diff_hr5: List[float] = []
    diff_mrr: List[float] = []
    wids_paired: List[str] = []
    for rec in per_query:
        mf = rec["models"].get("full")
        mc = rec["models"].get("cosine_only")
        if mf is None or mc is None:
            continue
        diff_hr1.append(float(mf["hit@1"]) - float(mc["hit@1"]))
        diff_hr3.append(float(mf["hit@3"]) - float(mc["hit@3"]))
        diff_hr5.append(float(mf["hit@5"]) - float(mc["hit@5"]))
        diff_mrr.append(float(mf["1/rank"]) - float(mc["1/rank"]))
        wids_paired.append(work_id(rec["filename"]))
    assert len(diff_hr1) == len(wids_paired)
    paired: Dict[str, dict] = {}
    if diff_hr1:
        d1, c1 = float(np.mean(diff_hr1)), _cluster_bootstrap_ci_mean(
            diff_hr1, wids_paired, rng_bootstrap
        )
        d3, c3 = float(np.mean(diff_hr3)), _cluster_bootstrap_ci_mean(
            diff_hr3, wids_paired, rng_bootstrap
        )
        d5, c5 = float(np.mean(diff_hr5)), _cluster_bootstrap_ci_mean(
            diff_hr5, wids_paired, rng_bootstrap
        )
        dm, cm = float(np.mean(diff_mrr)), _cluster_bootstrap_ci_mean(
            diff_mrr, wids_paired, rng_bootstrap
        )
        paired = {
            "description": "Per-query difference (full − cosine_only); same query draw; work-level cluster bootstrap on differences.",
            "HR@1": {"mean_diff": round(d1, 4), "ci_95": [round(c1[0], 4), round(c1[1], 4)]},
            "HR@3": {"mean_diff": round(d3, 4), "ci_95": [round(c3[0], 4), round(c3[1], 4)]},
            "HR@5": {"mean_diff": round(d5, 4), "ci_95": [round(c5[0], 4), round(c5[1], 4)]},
            "MRR": {"mean_diff": round(dm, 4), "ci_95": [round(cm[0], 4), round(cm[1], 4)]},
        }

    return {
        "experiment": "RQ1_baselines",
        "description": (
            "Baselines for RQ1 oracle self-retrieval (identifiability): full model "
            "(range + cosine − α×avoid), cosine-only (α = 0), and "
            "range-only + random ranking (null). Uses the same random "
            "query pool definition and sampling rule as run_rq1_experiment.py."
        ),
        "parameters": {
            "alpha_full": ALPHA_FULL,
            "bootstrap_samples": BOOTSTRAP_SAMPLES,
            "random_seed_queries": RQ1_RANDOM_SEED,
            "random_seed_bootstrap": RQ1_RANDOM_SEED_BOOTSTRAP,
            "random_seed_null_baseline_stream": RANDOM_SEED_NULL_BASELINE,
            "min_candidates": RQ1_MIN_CANDIDATES,
            "n_queries_max": RQ1_N_QUERIES,
            "library_path": str(Path("data/all_tessituragrams.json")),
        },
        "data_summary": {
            "total_flat_lines": len(all_songs),
            "n_unique_works": len({work_id(s["filename"]) for s in all_songs}),
            "n_multi_part_lines": sum(1 for s in all_songs if "__part_" in s.get("filename", "")),
            "valid_query_pool_size": valid_pool_size,
            "queries_sampled": n,
            "n_unique_works_in_queries": len({work_id(rec["filename"]) for rec in per_query}),
            "random_sampling": True,
            "bootstrap_method": "cluster (work-level)",
            "candidate_pool_summary": pool_summary,
        },
        "descriptive_stratification_hr1_by_pool_size": {
            "note": (
                "Point estimates only (no CIs). Under uniform random ranking, "
                "P(top-1 hit) = 1/|C| for that query; mean 1/|C| over a bin approximates "
                "expected null HR@1 if |C| were held fixed."
            ),
            "bins": stratification,
        },
        "models": ["full", "null_random", "cosine_only"],
        "model_descriptions": {
            "full": "Range filter + cosine similarity − α×avoid_penalty (α = 0.5).",
            "null_random": "Range filter only, then a completely random ranking over the candidate set (null model).",
            "cosine_only": "Range filter + cosine similarity only (α = 0.0; avoid list ignored in scoring).",
        },
        "metrics": metrics,
        "paired_full_minus_cosine": paired,
        "per_query": per_query,
    }


def main() -> None:
    library_path = ROOT / "data" / "all_tessituragrams.json"
    out_dir = ROOT / "experiment_results"
    out_dir.mkdir(exist_ok=True)

    print("Running RQ1 oracle self-retrieval baselines (full vs cosine-only vs random)...")
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
    paired = results.get("paired_full_minus_cosine") or {}
    if paired:
        print("\n--- Paired full minus cosine (mean diff, 95% CI) ---")
        for key in ["HR@1", "MRR"]:
            block = paired.get(key, {})
            print(
                f"{key}: mean_diff = {block.get('mean_diff')}  CI: {block.get('ci_95')}"
            )


if __name__ == "__main__":
    main()

