"""
Research Question 2: Ranking stability under small preference changes.

- Enforces disjoint favourite/avoid sets for all perturbations.
- Selects baseline profiles at random (with a fixed seed) among all valid songs.
- Treats the baseline as the unit of analysis and bootstraps over baseline means.

Metric: Kendall's τ (tau) between the original ranking R0 and the ranking after
one-note preference changes. τ ∈ [−1, 1]; τ > 0.7 strong, 0.3–0.7 moderate,
< 0.3 weak (Kendall, 1948; evaluation plan).
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import List, Tuple

import numpy as np
from scipy.stats import kendalltau

# Allow running from project root or experiment folder
ROOT = Path(__file__).resolve().parent.parent
_sys_path = list(__import__("sys").path)
if str(ROOT) not in _sys_path:
    __import__("sys").path.insert(0, str(ROOT))

from src.storage import load_flat_library, work_id
from src.recommend import (  # noqa: E402
    filter_by_range,
    build_ideal_vector,
    score_songs,
    midi_to_note_name,
)

ALPHA = 0.5
TOP_N_FAV = 4
BOTTOM_N_AVOID = 2
BOOTSTRAP_SAMPLES = 10_000
RANDOM_SEED = 42
MIN_CANDIDATES = 10  # Candidate set C must have ≥ 10 songs
N_BASELINES = 20  # Number of baseline profiles to sample at random (if available)


def _derive_synthetic_profile(song: dict) -> Tuple[int, int, List[int], List[int]]:
    """
    Same rule as RQ1: derive a synthetic user profile from one song.

    - User range = song's pitch range (min_midi, max_midi).
    - Favourites = top 4 MIDI by duration (L1-normalised); all if < 4 pitches.
    - Avoids = bottom 2 MIDI by duration; none if < 2 pitches.
    - Favourites and avoids are enforced to be disjoint.
    """
    pr = song.get("statistics", {}).get("pitch_range", {})
    user_min = pr.get("min_midi")
    user_max = pr.get("max_midi")
    if user_min is None or user_max is None:
        raise ValueError(f"Song {song.get('filename')} has no pitch range")

    tess = song.get("tessituragram", {})
    if not tess:
        raise ValueError(f"Song {song.get('filename')} has empty tessituragram")

    total = sum(tess.values())
    if total <= 0:
        raise ValueError(f"Song {song.get('filename')} has zero total duration")

    proportions = [(int(midi), dur / total) for midi, dur in tess.items()]
    # Sort by descending duration, then by MIDI for deterministic tie-breaking
    sorted_by_duration = sorted(proportions, key=lambda x: (-x[1], x[0]))
    n_pitches = len(sorted_by_duration)

    favorite_midis = [m for m, _ in sorted_by_duration[: min(TOP_N_FAV, n_pitches)]]
    avoid_candidates = (
        [m for m, _ in sorted_by_duration[-BOTTOM_N_AVOID:]]
        if n_pitches >= BOTTOM_N_AVOID
        else []
    )
    # Ensure favourites and avoids are disjoint
    avoid_midis = [m for m in avoid_candidates if m not in favorite_midis]
    return user_min, user_max, favorite_midis, avoid_midis


def _compute_kendall_tau(ranking_r0: list[dict], ranking_r_new: list[dict]) -> float:
    """
    Compute Kendall's τ between two rankings of the same set of songs.

    Both rankings must contain the same filenames. Returns τ ∈ [−1, 1].
    Raises RuntimeError if scipy.stats.kendalltau returns NaN (should not happen
    if rankings are valid permutations over the same candidate set).
    """
    filenames = [r["filename"] for r in ranking_r0]
    assert set(filenames) == {r["filename"] for r in ranking_r_new}

    rank_r0 = {r["filename"]: r["rank"] for r in ranking_r0}
    rank_r_new = {r["filename"]: r["rank"] for r in ranking_r_new}
    r0_vec = np.array([rank_r0[f] for f in filenames])
    r_new_vec = np.array([rank_r_new[f] for f in filenames])

    tau, _ = kendalltau(r0_vec, r_new_vec)
    if np.isnan(tau):
        raise RuntimeError("Kendall tau returned NaN; check ranking vectors and candidate set.")
    return float(tau)


def _run_one_baseline(
    all_songs: list[dict],
    user_min: int,
    user_max: int,
    fav_midis: List[int],
    avoid_midis: List[int],
) -> tuple[list[float], list[dict]]:
    """
    Run all one-note perturbations for a single baseline profile.

    Returns:
        - list of τ values (one per perturbation)
        - list of per-perturbation records (type, MIDI, note name, τ)
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
        alpha=ALPHA,
    )

    perturbations: list[tuple[str, int, list[int], list[int]]] = []

    # Collect all MIDI notes that actually occur in the candidate set C
    used_midis_in_C: set[int] = set()
    for song in filtered:
        tess = song.get("tessituragram", {}) or {}
        used_midis_in_C.update(int(m) for m in tess.keys())

    # Restrict to notes that are both in the user's range and present in at least
    # one candidate song. This focuses perturbations on musically relevant notes.
    midi_in_range = {m for m in used_midis_in_C if user_min <= m <= user_max}

    # 1. Add one favourite: MIDI in range, not already favourite or avoid
    for m in midi_in_range:
        if m not in fav_midis and m not in avoid_midis:
            perturbations.append(("add_fav", m, fav_midis + [m], avoid_midis))

    # 2. Remove one favourite: each favourite in turn
    for i, m in enumerate(fav_midis):
        new_fav = fav_midis[:i] + fav_midis[i + 1 :]
        perturbations.append(("remove_fav", m, new_fav, avoid_midis))

    # 3. Add one avoid: MIDI in range, not already avoid or favourite
    for m in midi_in_range:
        if m not in avoid_midis and m not in fav_midis:
            perturbations.append(("add_avoid", m, fav_midis, avoid_midis + [m]))

    # 4. Remove one avoid: each avoid in turn
    for i, m in enumerate(avoid_midis):
        new_avoid = avoid_midis[:i] + avoid_midis[i + 1 :]
        perturbations.append(("remove_avoid", m, fav_midis, new_avoid))

    tau_values: list[float] = []
    per_pert: list[dict] = []
    for pert_type, midi_changed, new_fav, new_avoid in perturbations:
        ideal_new = build_ideal_vector(user_min, user_max, new_fav, new_avoid)
        ranking_new = score_songs(
            filtered,
            ideal_new,
            user_min,
            user_max,
            new_avoid,
            new_fav,
            alpha=ALPHA,
        )
        tau = _compute_kendall_tau(ranking_r0, ranking_new)
        tau_values.append(tau)
        per_pert.append(
            {
                "perturbation_type": pert_type,
                "midi_changed": midi_changed,
                "note_changed": midi_to_note_name(midi_changed),
                "tau": round(tau, 4),
            }
        )
    return tau_values, per_pert


def _select_baselines(
    all_songs: list[dict],
) -> list[tuple[dict, int, int, list[int], list[int]]]:
    """
    Collect all songs that can serve as a baseline (candidate set ≥ MIN_CANDIDATES),
    then sample up to N_BASELINES of them at random (RANDOM_SEED ensures
    reproducibility).
    """
    candidate_baselines: list[tuple[dict, int, int, list[int], list[int]]] = []
    for song in all_songs:
        try:
            user_min, user_max, fav_midis, avoid_midis = _derive_synthetic_profile(song)
        except ValueError:
            continue
        cand = filter_by_range(all_songs, user_min, user_max)
        if len(cand) >= MIN_CANDIDATES:
            candidate_baselines.append((song, user_min, user_max, fav_midis, avoid_midis))

    if not candidate_baselines:
        return []

    n_select = min(N_BASELINES, len(candidate_baselines))
    # Random sampling without replacement; RANDOM_SEED is set in the caller.
    return random.sample(candidate_baselines, n_select)


def _cluster_bootstrap_mean_over_baselines(
    baseline_means: list[float],
    baseline_work_ids: list[str],
) -> tuple[float, float]:
    """
    Cluster bootstrap 95% CI for the mean τ across baselines.

    Baselines are grouped by their source work (work_id). The bootstrap
    resamples work-clusters with replacement rather than individual baselines,
    preserving intra-work dependence when two baselines happen to come from
    different vocal lines of the same composition (Cameron et al., 2008).
    """
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


def run_rq2_experiment(library_path: Path) -> dict:
    """
    Run the RQ2 ranking stability experiment.

    - Uses random baseline selection among all valid songs (seeded).
    - Enforces disjoint favourites/avoids for all perturbations.
    - Treats baselines as iid units for CIs (bootstrap over baseline means).
    """
    random.seed(RANDOM_SEED)
    all_songs = load_flat_library(library_path)

    baselines = _select_baselines(all_songs)
    if not baselines:
        return {
            "experiment": "RQ2_ranking_stability",
            "error": f"No song yielded ≥ {MIN_CANDIDATES} candidates. Library too small.",
            "data_summary": {"total_songs": len(all_songs)},
        }

    baseline_tau_lists: list[list[float]] = []
    all_per_perturbation: list[dict] = []
    per_baseline_summary: list[dict] = []

    for song, user_min, user_max, fav_midis, avoid_midis in baselines:
        tau_vals, per_pert = _run_one_baseline(
            all_songs,
            user_min,
            user_max,
            fav_midis,
            avoid_midis,
        )
        baseline_tau_lists.append(tau_vals)

        for p in per_pert:
            p2 = dict(p)
            p2["baseline_source"] = song.get("filename", "")
            all_per_perturbation.append(p2)

        mean_b = float(np.mean(tau_vals)) if tau_vals else 0.0
        per_baseline_summary.append(
            {
                "source_song": song.get("filename", ""),
                "composer": song.get("composer", ""),
                "n_perturbations": len(tau_vals),
                "mean_tau": round(mean_b, 4),
            }
        )

    # Flatten all τ values (useful descriptive statistic, but not the CI unit)
    all_tau_values = [t for lst in baseline_tau_lists for t in lst]
    n_perturbations = len(all_tau_values)

    mean_tau_overall = float(np.mean(all_tau_values)) if n_perturbations else 0.0
    std_tau_overall = (
        float(np.std(all_tau_values, ddof=1)) if n_perturbations > 1 else 0.0
    )

    # Baseline-level aggregation and cluster bootstrap
    baseline_means = [
        float(np.mean(tau_vals)) if tau_vals else 0.0
        for tau_vals in baseline_tau_lists
    ]
    baseline_work_ids = [
        work_id(song.get("filename", ""))
        for song, *_ in baselines
    ]
    mean_tau_per_baseline = float(np.mean(baseline_means)) if baseline_means else 0.0
    std_tau_across_baselines = (
        float(np.std(baseline_means, ddof=1)) if len(baseline_means) > 1 else 0.0
    )
    ci_lo, ci_hi = _cluster_bootstrap_mean_over_baselines(baseline_means, baseline_work_ids)

    return {
        "experiment": "RQ2_ranking_stability",
        "description": (
            "When we change favourites or avoids by one note, how similar is the "
            "new ranking to the original? (Kendall's τ; random baselines, "
            "baseline-level bootstrap, song-aware perturbations)"
        ),
        "parameters": {
            "alpha": ALPHA,
            "top_n_favorite": TOP_N_FAV,
            "bottom_n_avoid": BOTTOM_N_AVOID,
            "min_candidates": MIN_CANDIDATES,
            "n_baselines_target": N_BASELINES,
            "bootstrap_samples": BOOTSTRAP_SAMPLES,
            "random_seed": RANDOM_SEED,
            "library_path": str(Path("data/all_tessituragrams.json")),
        },
        "baseline_profiles": per_baseline_summary,
        "data_summary": {
            "total_flat_lines": len(all_songs),
            "n_unique_works": len({work_id(s["filename"]) for s in all_songs}),
            "n_multi_part_lines": sum(1 for s in all_songs if "__part_" in s.get("filename", "")),
            "n_baselines": len(baselines),
            "n_unique_works_in_baselines": len(set(baseline_work_ids)),
            "total_perturbations": n_perturbations,
            "bootstrap_method": "cluster (work-level)",
        },
        "metrics": {
            # Overall descriptive stats across all perturbations
            "mean_tau_overall": round(mean_tau_overall, 4),
            "std_tau_overall": round(std_tau_overall, 4),
            # Baseline-level aggregation (unit of analysis for CI)
            "mean_tau_per_baseline": round(mean_tau_per_baseline, 4),
            "std_tau_across_baselines": round(std_tau_across_baselines, 4),
            "ci_95_baseline_mean": [round(ci_lo, 4), round(ci_hi, 4)],
        },
        "interpretation": {
            "tau_gt_0.7": "strong agreement (rankings very similar)",
            "tau_0.3_to_0.7": "moderate agreement",
            "tau_lt_0.3": "weak agreement",
        },
        "per_perturbation": all_per_perturbation,
    }


def main() -> None:
    library_path = ROOT / "data" / "all_tessituragrams.json"
    out_dir = ROOT / "experiment_results"
    out_dir.mkdir(exist_ok=True)

    print("Running RQ2 Ranking Stability Experiment...")
    print(f"Library: {library_path}")

    results = run_rq2_experiment(library_path)

    out_json = out_dir / "RQ2_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to {out_json}")

    if "error" in results:
        print(f"\nError: {results['error']}")
        return

    m = results["metrics"]
    ds = results["data_summary"]
    print("\n--- Metrics ---")
    print(
        f"Mean tau (all perturbations): {m['mean_tau_overall']}  "
        f"(std: {m['std_tau_overall']})"
    )
    print(
        "Mean tau per baseline: "
        f"{m['mean_tau_per_baseline']}  "
        f"(std across baselines: {m['std_tau_across_baselines']})"
    )
    print(f"95% CI (baseline-level mean): {m['ci_95_baseline_mean']}")
    print(f"\nBaselines used: {ds.get('n_baselines', 0)}")
    print(f"Total perturbations: {ds.get('total_perturbations', 0)}")


if __name__ == "__main__":
    main()

