"""
Shared settings for **Experiment 1** (101-line library, data/tessituragrams.json).

This module is self-contained: it does not import from experiment/run_rq1_experiment.py
(the Experiment 2 pipeline). Callers must seed the global ``random`` module before
``select_queries`` if they need reproducibility (same pattern as the original CADSCOM
submission scripts).
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import List, Tuple

# Repository root (parent of previous_paper_and_experiments/)
REPO_ROOT: Path = Path(__file__).resolve().parents[2]
SCRIPTS_DIR: Path = Path(__file__).resolve().parent

N_QUERIES: int = 50
MIN_CANDIDATES: int = 2
RANDOM_SEED: int = 42
TOP_N_FAV: int = 4
BOTTOM_N_AVOID: int = 2


def setup_sys_path() -> None:
    """Ensure repo root is on sys.path so ``src`` imports work."""
    import sys

    root = str(REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


def _derive_synthetic_profile(
    song: dict,
) -> Tuple[int, int, List[int], List[int]]:
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

    sorted_by_duration = sorted(proportions, key=lambda x: (-x[1], x[0]))
    n_pitches = len(sorted_by_duration)

    favorite_midis = [m for m, _ in sorted_by_duration[: min(TOP_N_FAV, n_pitches)]]
    avoid_candidates = (
        [m for m, _ in sorted_by_duration[-BOTTOM_N_AVOID:]]
        if n_pitches >= BOTTOM_N_AVOID
        else []
    )
    avoid_midis = [m for m in avoid_candidates if m not in favorite_midis]

    return user_min, user_max, favorite_midis, avoid_midis


def select_queries(
    all_songs: list[dict],
    filter_by_range_fn,
) -> tuple[
    list[tuple[dict, int, int, list[int], list[int]]],
    int,
]:
    """
    Valid pool: lines with |C| >= MIN_CANDIDATES. Sample up to N_QUERIES
    without replacement using the **global** ``random`` module (seed before calling).
    """
    candidates: list[tuple[dict, int, int, list[int], list[int]]] = []
    for song in all_songs:
        try:
            user_min, user_max, fav_midis, avoid_midis = _derive_synthetic_profile(song)
        except ValueError:
            continue
        filtered = filter_by_range_fn(all_songs, user_min, user_max)
        if len(filtered) < MIN_CANDIDATES:
            continue
        candidates.append((song, user_min, user_max, fav_midis, avoid_midis))
    pool_size = len(candidates)
    if not candidates:
        return [], 0
    n_select = min(N_QUERIES, pool_size)
    return random.sample(candidates, n_select), pool_size
