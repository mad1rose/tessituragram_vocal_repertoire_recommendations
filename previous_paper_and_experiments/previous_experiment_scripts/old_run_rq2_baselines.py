"""
Baselines for Research Question 2: Ranking stability under small preference changes.

We compare three systems, using the same baseline-selection rule as
`run_rq2_experiment.py`:

- full:        range filter + cosine similarity − α × avoid_penalty (α = 0.5)
- null_random: range filter only, then completely random rankings (null model)
- cosine_only: range filter + cosine similarity only (α = 0.0; no avoid penalty)

For each system we reuse the RQ2 procedure (one-note add/remove of favourites
or avoids) and compute:

- mean Kendall's τ across all perturbations,
- standard deviation of τ across perturbations,
- mean τ per baseline profile,
- standard deviation of baseline means,
- a 95% bootstrap CI for the baseline-level mean τ.

The random baseline ignores user preferences entirely. For each baseline we
draw a single random reference ranking R0 over the candidate set, and for each
“perturbation” sample we draw a new random ranking R_new and compute τ(R0, R_new),
yielding a null distribution centred near zero.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from scipy.stats import kendalltau

# Allow running from project root or experiment folder
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
from experiment.run_rq2_experiment import (  # noqa: E402
    _derive_synthetic_profile,
    _select_baselines as rq2_select_baselines,
    RANDOM_SEED as RQ2_RANDOM_SEED,
    MIN_CANDIDATES as RQ2_MIN_CANDIDATES,
    N_BASELINES as RQ2_N_BASELINES,
)


ALPHA_FULL = 0.5
BOOTSTRAP_SAMPLES = 10_000


def _bootstrap_ci_mean_over_baselines(baseline_means: List[float]) -> Tuple[float, float]:
    """
    Bootstrap a 95% CI for the mean τ, treating baselines as the unit of analysis.
    """
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


def _enumerate_perturbations(
    all_songs: List[dict],
    user_min: int,
    user_max: int,
    fav_midis: List[int],
    avoid_midis: List[int],
) -> List[Tuple[str, int, List[int], List[int]]]:
    """
    Recreate the one-note perturbations used in RQ2:

    - add_fav:   add a new favourite (MIDI in-range, present in at least one
                 candidate song, not already fav/avoid)
    - remove_fav: remove each favourite in turn
    - add_avoid: add a new avoid note (same constraints as add_fav)
    - remove_avoid: remove each avoid note in turn
    """
    filtered = filter_by_range(all_songs, user_min, user_max)

    used_midis_in_C: set[int] = set()
    for song in filtered:
        tess = song.get("tessituragram", {}) or {}
        used_midis_in_C.update(int(m) for m in tess.keys())
    midi_in_range = {m for m in used_midis_in_C if user_min <= m <= user_max}

    perturbations: List[Tuple[str, int, List[int], List[int]]] = []

    # 1. Add one favourite
    for m in midi_in_range:
        if m not in fav_midis and m not in avoid_midis:
            perturbations.append(("add_fav", m, fav_midis + [m], avoid_midis))

    # 2. Remove one favourite
    for i, m in enumerate(fav_midis):
        new_fav = fav_midis[:i] + fav_midis[i + 1 :]
        perturbations.append(("remove_fav", m, new_fav, avoid_midis))

    # 3. Add one avoid
    for m in midi_in_range:
        if m not in avoid_midis and m not in fav_midis:
            perturbations.append(("add_avoid", m, fav_midis, avoid_midis + [m]))

    # 4. Remove one avoid
    for i, m in enumerate(avoid_midis):
        new_avoid = avoid_midis[:i] + avoid_midis[i + 1 :]
        perturbations.append(("remove_avoid", m, fav_midis, new_avoid))

    return perturbations


def _run_one_baseline_for_alpha(
    all_songs: List[dict],
    user_min: int,
    user_max: int,
    fav_midis: List[int],
    avoid_midis: List[int],
    alpha: float,
) -> List[float]:
    """
    RQ2-style baseline run for a given alpha.

    Mirrors the logic in `run_rq2_experiment.py` but parameterises alpha and
    returns only the list of τ values.
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

    perturbations = _enumerate_perturbations(
        all_songs, user_min, user_max, fav_midis, avoid_midis
    )

    filenames = [r["filename"] for r in ranking_r0]
    rank_r0 = {r["filename"]: r["rank"] for r in ranking_r0}

    tau_values: List[float] = []
    for _, _, new_fav, new_avoid in perturbations:
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
        rank_r_new = {r["filename"]: r["rank"] for r in ranking_new}
        r0_vec = np.array([rank_r0[f] for f in filenames])
        r_new_vec = np.array([rank_r_new[f] for f in filenames])
        tau, _ = kendalltau(r0_vec, r_new_vec)
        if not np.isnan(tau):
            tau_values.append(float(tau))

    return tau_values


def _run_one_baseline_random(
    all_songs: List[dict],
    user_min: int,
    user_max: int,
    fav_midis: List[int],
    avoid_midis: List[int],
    n_samples: int,
    rng: random.Random,
) -> List[float]:
    """
    Null model: range-only filtering + random rankings.

    For each baseline:
      - construct the candidate set C by range filtering,
      - draw a single random reference ranking R0 (permutation of C),
      - for each of `n_samples`, draw a new random ranking R_new and compute
        Kendall's τ between R0 and R_new.

    `fav_midis` and `avoid_midis` are unused here (the model ignores preferences)
    but are kept for interface symmetry.
    """
    _ = fav_midis
    _ = avoid_midis

    filtered = filter_by_range(all_songs, user_min, user_max)
    if len(filtered) < 2:
        return []

    n = len(filtered)
    indices = list(range(n))

    # Fixed random reference ranking R0 for this baseline
    perm0 = indices[:]
    rng.shuffle(perm0)
    r0_vec = np.array(perm0)

    tau_values: List[float] = []
    for _i in range(n_samples):
        perm_new = indices[:]
        rng.shuffle(perm_new)
        r_new_vec = np.array(perm_new)
        tau, _ = kendalltau(r0_vec, r_new_vec)
        if not np.isnan(tau):
            tau_values.append(float(tau))

    return tau_values


def _aggregate_tau_lists(baseline_tau_lists: List[List[float]]) -> Dict[str, object]:
    """Aggregate τ lists across baselines into summary metrics."""
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
            "n_baselines": len(baseline_tau_lists),
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
        "n_baselines": len(baseline_tau_lists),
    }


def run_rq2_baselines(library_path: Path) -> dict:
    """
    Run RQ2 baselines (full, cosine-only, and random) using the same baseline
    selection rule as `run_rq2_experiment.py`.
    """
    random.seed(RQ2_RANDOM_SEED)
    all_songs = load_tessituragrams(library_path)

    baselines = rq2_select_baselines(all_songs)
    if not baselines:
        return {
            "experiment": "RQ2_ranking_stability_baselines",
            "error": (
                f"No song yielded ≥ {RQ2_MIN_CANDIDATES} candidates. "
                "Library too small for baseline analysis."
            ),
            "data_summary": {"total_songs": len(all_songs)},
        }

    # For each baseline, we need τ-lists for each model. For the random model we
    # match the number of samples to the full-model perturbation count so that
    # the sample size is comparable.
    baseline_tau_full: List[List[float]] = []
    baseline_tau_cos: List[List[float]] = []
    baseline_tau_rand: List[List[float]] = []

    rng_random = random.Random(RQ2_RANDOM_SEED + 20_000)

    per_baseline_summary: List[dict] = []

    for song, user_min, user_max, fav_midis, avoid_midis in baselines:
        # Ensure the profile is valid (defensive; already done in _select_baselines)
        try:
            _derive_synthetic_profile(song)
        except ValueError:
            continue

        tau_full = _run_one_baseline_for_alpha(
            all_songs, user_min, user_max, fav_midis, avoid_midis, alpha=ALPHA_FULL
        )
        tau_cos = _run_one_baseline_for_alpha(
            all_songs, user_min, user_max, fav_midis, avoid_midis, alpha=0.0
        )

        n_samples_rand = max(len(tau_full), 1)
        tau_rand = _run_one_baseline_random(
            all_songs,
            user_min,
            user_max,
            fav_midis,
            avoid_midis,
            n_samples=n_samples_rand,
            rng=rng_random,
        )

        baseline_tau_full.append(tau_full)
        baseline_tau_cos.append(tau_cos)
        baseline_tau_rand.append(tau_rand)

        per_baseline_summary.append(
            {
                "source_song": song.get("filename", ""),
                "composer": song.get("composer", ""),
                "n_perturbations_full": len(tau_full),
                "n_perturbations_cosine_only": len(tau_cos),
                "n_samples_random": len(tau_rand),
            }
        )

    metrics_full = _aggregate_tau_lists(baseline_tau_full)
    metrics_cos = _aggregate_tau_lists(baseline_tau_cos)
    metrics_rand = _aggregate_tau_lists(baseline_tau_rand)

    return {
        "experiment": "RQ2_baselines",
        "description": (
            "Baselines for RQ2 ranking stability: full model (range + cosine − α×avoid), "
            "cosine-only (α = 0), and range-only + random rankings (null). Uses the "
            "same random baseline selection rule as run_rq2_experiment.py."
        ),
        "parameters": {
            "alpha_full": ALPHA_FULL,
            "bootstrap_samples": BOOTSTRAP_SAMPLES,
            "random_seed_baselines": RQ2_RANDOM_SEED,
            "min_candidates": RQ2_MIN_CANDIDATES,
            "n_baselines_target": RQ2_N_BASELINES,
            "library_path": str(Path("data/tessituragrams.json")),
        },
        "data_summary": {
            "total_songs_in_library": len(all_songs),
            "n_baselines": len(baselines),
        },
        "models": ["full", "null_random", "cosine_only"],
        "model_descriptions": {
            "full": "Range filter + cosine similarity − α×avoid_penalty (α = 0.5).",
            "null_random": "Range filter only, then random rankings compared against a random reference ordering (null τ distribution).",
            "cosine_only": "Range filter + cosine similarity only (α = 0.0; avoid list ignored in scoring).",
        },
        "metrics": {
            "full": metrics_full,
            "cosine_only": metrics_cos,
            "null_random": metrics_rand,
        },
        "baseline_profiles": per_baseline_summary,
    }


def main() -> None:
    library_path = ROOT / "data" / "tessituragrams.json"
    out_dir = ROOT / "experiment_results"
    out_dir.mkdir(exist_ok=True)

    print("Running RQ2 Ranking Stability Baselines (full vs cosine-only vs random)...")
    print(f"Library: {library_path}")

    results = run_rq2_baselines(library_path)

    out_json = out_dir / "RQ2_baselines.json"
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to {out_json}")

    if "error" in results:
        print(f"\nError: {results['error']}")
        return

    m = results["metrics"]
    print("\n--- Summary (mean tau per baseline with 95% CI) ---")
    for model_name in ["full", "null_random", "cosine_only"]:
        mm = m[model_name]
        print(
            f"{model_name:12s} "
            f"mean tau (per baseline) = {mm['mean_tau_per_baseline']}  "
            f"CI: {mm['ci_95_baseline_mean']}"
        )


if __name__ == "__main__":
    main()