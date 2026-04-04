"""
Research Question 1: Oracle self-retrieval / identifiability (Experiment 2).

When we build a synthetic user profile from one vocal line (using that line's
most- and least-used pitches as favourites and avoids), does the system
rank that same line at position 1, or within the top 3 or top 5?

Queries are randomly sampled from eligible vocal lines (candidate set >= 2);
up to N_QUERIES are used (seeded for reproducibility; 200 with the full library).
Metrics: HR@1, MRR, HR@3, HR@5 with 95% bootstrap CIs (work-level cluster
bootstrap; query seed 42, bootstrap seed 43).
"""

from __future__ import annotations

import json
import random
import warnings
from pathlib import Path

import numpy as np

# Allow running from project root or from experiment folder
ROOT = Path(__file__).resolve().parent.parent
sys_path = list(__import__('sys').path)
if str(ROOT) not in sys_path:
    __import__('sys').path.insert(0, str(ROOT))

from src.storage import load_flat_library, work_id
from src.recommend import (
    filter_by_range,
    build_ideal_vector,
    score_songs,
)
from experiment.rq1_pool_stats import compute_candidate_pool_summary

ALPHA = 0.5
TOP_N_FAV = 4
BOTTOM_N_AVOID = 2
BOOTSTRAP_SAMPLES = 10_000
# Separate streams: query draw vs bootstrap so partial reruns and tooling stay reproducible.
RANDOM_SEED_QUERIES = 42
RANDOM_SEED_BOOTSTRAP = 43
RANDOM_SEED = RANDOM_SEED_QUERIES  # Alias for imports expecting a single seed (baselines, alpha sweep)
MIN_CANDIDATES = 2  # At least 2 songs in candidate set (so there is a real ranking)
N_QUERIES = 200  # Max number of queries to sample at random; use all valid if fewer


def _derive_synthetic_profile(song: dict) -> tuple[int, int, list[int], list[int]]:
    """
    Derive synthetic user profile from a song.

    - User range = song's pitch range (min_midi, max_midi).
    - Favorites = top 4 MIDI by duration (L1-normalised); use all if < 4 pitches.
    - Avoids = bottom 2 MIDI by duration; use none if < 2 pitches.

    Returns (user_min, user_max, favorite_midis, avoid_midis).
    """
    pr = song.get('statistics', {}).get('pitch_range', {})
    user_min = pr.get('min_midi')
    user_max = pr.get('max_midi')
    if user_min is None or user_max is None:
        raise ValueError(f"Song {song.get('filename')} has no pitch range")

    tess = song.get('tessituragram', {})
    if not tess:
        raise ValueError(f"Song {song.get('filename')} has empty tessituragram")

    # L1-normalise: proportion of singing time per pitch
    total = sum(tess.values())
    if total <= 0:
        raise ValueError(f"Song {song.get('filename')} has zero total duration")
    proportions = [(int(midi), dur / total) for midi, dur in tess.items()]

    # Top by duration = favorites; bottom = avoids. Secondary sort by MIDI for
    # deterministic tie-breaking when durations are equal (reproducibility).
    sorted_by_duration = sorted(proportions, key=lambda x: (-x[1], x[0]))
    n_pitches = len(sorted_by_duration)

    favorite_midis = [m for m, _ in sorted_by_duration[: min(TOP_N_FAV, n_pitches)]]
    avoid_candidates = (
        [m for m, _ in sorted_by_duration[-BOTTOM_N_AVOID:]]
        if n_pitches >= BOTTOM_N_AVOID
        else []
    )
    # Ensure favorites and avoids are disjoint (avoid penalising a pitch we boost)
    avoid_midis = [m for m in avoid_candidates if m not in favorite_midis]

    return user_min, user_max, favorite_midis, avoid_midis


def _select_queries(
    all_songs: list[dict],
    rng: random.Random,
) -> tuple[list[tuple[dict, int, int, list[int], list[int]]], int]:
    """
    Collect all songs that are valid queries (candidate set >= MIN_CANDIDATES),
    then sample up to N_QUERIES at random using ``rng``.
    Returns (sampled_query_list, total_valid_pool_size).
    """
    candidates: list[tuple[dict, int, int, list[int], list[int]]] = []
    for song in all_songs:
        try:
            user_min, user_max, fav_midis, avoid_midis = _derive_synthetic_profile(song)
        except ValueError:
            continue
        filtered = filter_by_range(all_songs, user_min, user_max)
        if len(filtered) < MIN_CANDIDATES:
            continue
        candidates.append((song, user_min, user_max, fav_midis, avoid_midis))
    pool_size = len(candidates)
    if not candidates:
        return [], 0
    n_select = min(N_QUERIES, pool_size)
    return rng.sample(candidates, n_select), pool_size


def run_rq1_experiment(library_path: Path) -> dict:
    """Run the RQ1 oracle self-retrieval experiment (Experiment 2). Returns full results dict."""
    rng_queries = random.Random(RANDOM_SEED_QUERIES)
    rng_bootstrap = random.Random(RANDOM_SEED_BOOTSTRAP)
    all_songs = load_flat_library(library_path)

    query_list, valid_pool_size = _select_queries(all_songs, rng_queries)
    records: list[dict] = []

    for song, user_min, user_max, fav_midis, avoid_midis in query_list:
        filename = song.get('filename', '')
        filtered = filter_by_range(all_songs, user_min, user_max)
        n_candidates = len(filtered)
        ideal_vec = build_ideal_vector(user_min, user_max, fav_midis, avoid_midis)
        results = score_songs(
            filtered, ideal_vec, user_min, user_max,
            avoid_midis, fav_midis, alpha=ALPHA,
        )

        rank = None
        for r in results:
            if r['filename'] == filename:
                rank = r['rank']
                break

        if rank is None:
            continue  # should not happen if query song is in filtered set

        hit1 = 1 if rank == 1 else 0
        hit3 = 1 if rank <= 3 else 0
        hit5 = 1 if rank <= 5 else 0
        mrr = 1.0 / rank

        records.append({
            'filename': filename,
            'composer': song.get('composer'),
            'title': song.get('title'),
            'n_candidates': n_candidates,
            'rank': rank,
            'hit@1': hit1,
            'hit@3': hit3,
            'hit@5': hit5,
            '1/rank': mrr,
        })

    n = len(records)

    # Aggregate metrics
    hr1 = np.mean([r['hit@1'] for r in records]) if n else 0.0
    hr3 = np.mean([r['hit@3'] for r in records]) if n else 0.0
    hr5 = np.mean([r['hit@5'] for r in records]) if n else 0.0
    mrr = np.mean([r['1/rank'] for r in records]) if n else 0.0

    # Cluster bootstrap 95% CI (percentile method).
    # Lines from the same work (identified by work_id) are not independent;
    # resampling clusters (works) rather than individual observations accounts
    # for intra-work correlation (Cameron, Gelbach & Miller, 2008; Field & Welsh, 2007).
    def cluster_bootstrap_mean(
        values: list[float],
        cluster_ids: list[str],
        n_samples: int = BOOTSTRAP_SAMPLES,
    ) -> tuple[float, float]:
        if not values:
            return 0.0, 0.0
        clusters: dict[str, list[int]] = {}
        for i, cid in enumerate(cluster_ids):
            clusters.setdefault(cid, []).append(i)
        cluster_keys = list(clusters.keys())
        n_clusters = len(cluster_keys)
        if n_clusters <= 1:
            warnings.warn(
                "cluster_bootstrap_mean: only one cluster; CI equals point estimate",
                UserWarning,
                stacklevel=2,
            )
            m = float(np.mean(values))
            return m, m
        values_arr = np.array(values, dtype=float)
        boot = np.empty(n_samples)
        for b in range(n_samples):
            sampled = rng_bootstrap.choices(cluster_keys, k=n_clusters)
            indices = [idx for key in sampled for idx in clusters[key]]
            boot[b] = np.mean(values_arr[indices])
        return float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))

    nc_list = [int(r['n_candidates']) for r in records]
    pool_summary = compute_candidate_pool_summary(nc_list) if nc_list else {}

    work_ids = [work_id(r['filename']) for r in records]
    hr1_ci = cluster_bootstrap_mean([r['hit@1'] for r in records], work_ids) if n else (0.0, 0.0)
    hr3_ci = cluster_bootstrap_mean([r['hit@3'] for r in records], work_ids) if n else (0.0, 0.0)
    hr5_ci = cluster_bootstrap_mean([r['hit@5'] for r in records], work_ids) if n else (0.0, 0.0)
    mrr_ci = cluster_bootstrap_mean([r['1/rank'] for r in records], work_ids) if n else (0.0, 0.0)

    return {
        'experiment': 'RQ1_self_retrieval_accuracy',
        'description': (
            'Synthetic self-retrieval: when the profile is derived from one vocal line, '
            'does the system rank that same line first or in the top 3/5?'
        ),
        'parameters': {
            'alpha': ALPHA,
            'top_n_favorite': TOP_N_FAV,
            'bottom_n_avoid': BOTTOM_N_AVOID,
            'min_candidates': MIN_CANDIDATES,
            'n_queries_max': N_QUERIES,
            'bootstrap_samples': BOOTSTRAP_SAMPLES,
            'random_seed_queries': RANDOM_SEED_QUERIES,
            'random_seed_bootstrap': RANDOM_SEED_BOOTSTRAP,
            'random_seed': RANDOM_SEED_QUERIES,
            'library_path': str(Path('data/all_tessituragrams.json')),
        },
        'data_summary': {
            'total_flat_lines': len(all_songs),
            'n_unique_works': len({work_id(s['filename']) for s in all_songs}),
            'n_multi_part_lines': sum(1 for s in all_songs if '__part_' in s.get('filename', '')),
            'valid_query_pool_size': valid_pool_size,
            'queries_sampled': n,
            'n_unique_works_in_queries': len({work_id(r['filename']) for r in records}),
            'random_sampling': True,
            'bootstrap_method': 'cluster (work-level)',
            'candidate_pool_summary': pool_summary,
        },
        'metrics': {
            'HR@1': {'value': round(hr1, 4), 'ci_95': [round(hr1_ci[0], 4), round(hr1_ci[1], 4)]},
            'HR@3': {'value': round(hr3, 4), 'ci_95': [round(hr3_ci[0], 4), round(hr3_ci[1], 4)]},
            'HR@5': {'value': round(hr5, 4), 'ci_95': [round(hr5_ci[0], 4), round(hr5_ci[1], 4)]},
            'MRR': {'value': round(mrr, 4), 'ci_95': [round(mrr_ci[0], 4), round(mrr_ci[1], 4)]},
        },
        'formulas': {
            'HR@1': 'fraction of queries where the query line was ranked 1',
            'HR@3': 'fraction of queries where the query line was in top 3',
            'HR@5': 'fraction of queries where the query line was in top 5',
            'MRR': 'mean of 1/rank across queries (1 = best, rewards higher ranks)',
        },
        'per_query': records,
    }


def main() -> None:
    library_path = ROOT / 'data' / 'all_tessituragrams.json'
    out_dir = ROOT / 'experiment_results'
    out_dir.mkdir(exist_ok=True)

    print("Running RQ1 oracle self-retrieval experiment (Experiment 2)...")
    print(f"Library: {library_path}")

    results = run_rq1_experiment(library_path)

    out_json = out_dir / 'RQ1_results.json'
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to {out_json}")

    # Summary
    m = results['metrics']
    print("\n--- Metrics ---")
    print(f"HR@1: {m['HR@1']['value']}  [95% CI: {m['HR@1']['ci_95']}]")
    print(f"HR@3: {m['HR@3']['value']}  [95% CI: {m['HR@3']['ci_95']}]")
    print(f"HR@5: {m['HR@5']['value']}  [95% CI: {m['HR@5']['ci_95']}]")
    print(f"MRR:  {m['MRR']['value']}  [95% CI: {m['MRR']['ci_95']}]")
    ds = results['data_summary']
    print(
        f"\nValid query pool: {ds['valid_query_pool_size']}; sampled: "
        f"{ds['queries_sampled']} (random, query_seed={RANDOM_SEED_QUERIES})"
    )


if __name__ == '__main__':
    main()
