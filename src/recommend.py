"""Core recommendation engine: filtering, vectorisation, scoring, ranking."""

from __future__ import annotations

import numpy as np
from music21 import pitch as m21pitch
from scipy.optimize import linear_sum_assignment

# ── Helpers: note-name / MIDI conversion ────────────────────────────────────

NOTE_NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']


def midi_to_note_name(midi: int) -> str:
    """Convert a MIDI number to a readable note name, e.g. 60 → 'C4'."""
    octave = (midi // 12) - 1
    return f"{NOTE_NAMES[midi % 12]}{octave}"


def note_name_to_midi(name: str) -> int:
    """Convert a human-readable note name to a MIDI number.

    Accepts any format music21 understands:
        C4, F#4, Bb3, Eb5, G#5, D-4 (flat via '-'), …

    Raises ValueError on unparseable input.
    """
    name = name.strip()
    try:
        p = m21pitch.Pitch(name)
        return p.midi
    except Exception as exc:
        raise ValueError(
            f"'{name}' is not a valid note name.  "
            f"Examples: C4, F#4, Bb3, Eb5"
        ) from exc


# ── Filtering (solo path, backward-compatible) ──────────────────────────────

def filter_by_range(
    songs: list[dict],
    user_min_midi: int,
    user_max_midi: int,
) -> list[dict]:
    """Hard-filter for flattened single-part songs (solo path).

    Keeps songs whose entire range fits inside the user's specified range.
    """
    filtered: list[dict] = []
    for song in songs:
        pr = song.get('statistics', {}).get('pitch_range', {})
        song_min = pr.get('min_midi')
        song_max = pr.get('max_midi')
        if song_min is None or song_max is None:
            continue
        if song_min >= user_min_midi and song_max <= user_max_midi:
            filtered.append(song)
    return filtered


# ── Vectorisation ────────────────────────────────────────────────────────────

def build_dense_vector(
    tessituragram: dict[str, float],
    min_midi: int,
    max_midi: int,
) -> np.ndarray:
    """Convert a sparse tessituragram dict into a dense numpy array
    over the pitch space [min_midi … max_midi]."""
    length = max_midi - min_midi + 1
    vec = np.zeros(length, dtype=np.float64)
    for midi_str, duration in tessituragram.items():
        idx = int(midi_str) - min_midi
        if 0 <= idx < length:
            vec[idx] = duration
    return vec


def normalize_l1(vec: np.ndarray) -> np.ndarray:
    """L1-normalise so the vector sums to 1 (proportion of singing time)."""
    total = vec.sum()
    if total == 0:
        return vec.copy()
    return vec / total


def normalize_l2(vec: np.ndarray) -> np.ndarray:
    """L2-normalise to a unit-length direction vector (for cosine similarity)."""
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec.copy()
    return vec / norm


# ── Ideal vector ─────────────────────────────────────────────────────────────

def build_ideal_vector(
    min_midi: int,
    max_midi: int,
    favorite_midis: list[int],
    avoid_midis: list[int],
    base: float = 0.2,
    fav_boost: float = 1.0,
    avoid_pen: float = -1.0,
) -> np.ndarray:
    """Construct and L2-normalise an ideal tessituragram vector.

    Peaks at favourite notes, low at avoid notes, baseline everywhere else.
    """
    length = max_midi - min_midi + 1
    vec = np.full(length, base, dtype=np.float64)

    for midi in favorite_midis:
        idx = midi - min_midi
        if 0 <= idx < length:
            vec[idx] += fav_boost

    for midi in avoid_midis:
        idx = midi - min_midi
        if 0 <= idx < length:
            vec[idx] += avoid_pen

    np.clip(vec, 0, None, out=vec)
    return normalize_l2(vec)


# ── Similarity ───────────────────────────────────────────────────────────────

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors.  Returns 0 if either is zero."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


# ═════════════════════════════════════════════════════════════════════════════
# Solo scoring (backward-compatible — works on flattened single-part songs)
# ═════════════════════════════════════════════════════════════════════════════

def score_songs(
    filtered_songs: list[dict],
    ideal_vec: np.ndarray,
    min_midi: int,
    max_midi: int,
    avoid_midis: list[int],
    favorite_midis: list[int],
    alpha: float = 0.0,
) -> list[dict]:
    """Score every (flat, single-part) song against one ideal vector.

    Returns results sorted best-to-worst by final_score.
    """
    avoid_indices = [m - min_midi for m in avoid_midis if min_midi <= m <= max_midi]
    fav_indices = [m - min_midi for m in favorite_midis if min_midi <= m <= max_midi]

    results: list[dict] = []
    for song in filtered_songs:
        tess = song.get('tessituragram', {})
        dense = build_dense_vector(tess, min_midi, max_midi)
        normed = normalize_l1(dense)

        cos_sim = cosine_similarity(normed, ideal_vec)
        avoid_penalty = float(sum(normed[i] for i in avoid_indices)) if avoid_indices else 0.0
        final_score = cos_sim - alpha * avoid_penalty
        fav_overlap = float(sum(normed[i] for i in fav_indices)) if fav_indices else 0.0

        results.append({
            'filename': song.get('filename', ''),
            'composer': song.get('composer', 'Unknown'),
            'title': song.get('title', ''),
            'part_id': song.get('part_id', ''),
            'part_name': song.get('part_name', ''),
            'final_score': round(final_score, 4),
            'cosine_similarity': round(cos_sim, 4),
            'avoid_penalty': round(avoid_penalty, 4),
            'favorite_overlap': round(fav_overlap, 4),
            'tessituragram': tess,
            'normalized_vector': {
                str(min_midi + i): round(float(v), 6)
                for i, v in enumerate(normed)
            },
            'statistics': song.get('statistics', {}),
        })

    results.sort(key=lambda r: (-r['final_score'], r['filename']))

    for rank, result in enumerate(results, 1):
        result['rank'] = rank
        result['explanation'] = _explain_solo(
            result, favorite_midis, avoid_midis,
        )

    return results


# ═════════════════════════════════════════════════════════════════════════════
# Multi-part scoring (optimal profile-to-part assignment)
# ═════════════════════════════════════════════════════════════════════════════

def _part_range(part: dict) -> tuple[int | None, int | None]:
    """Extract (min_midi, max_midi) from a part dict in multi-part format."""
    stats = part.get('statistics', {})
    pr = stats.get('pitch_range', {})
    return pr.get('min_midi'), pr.get('max_midi')


def _profile_can_sing_part(profile: dict, part: dict) -> bool:
    """True if the part's full range fits inside the profile's range."""
    pmin, pmax = _part_range(part)
    if pmin is None or pmax is None:
        return False
    return pmin >= profile['min_midi'] and pmax <= profile['max_midi']


def build_feasibility_matrix(
    parts: list[dict],
    profiles: list[dict],
) -> np.ndarray:
    """Return an N×N boolean matrix.  ``mat[i][j]`` is True when profile *i*
    can sing part *j* (the part's range fits within the profile's range).
    """
    n = len(profiles)
    mat = np.zeros((n, n), dtype=bool)
    for i, prof in enumerate(profiles):
        for j, part in enumerate(parts):
            mat[i, j] = _profile_can_sing_part(prof, part)
    return mat


def has_valid_assignment(feasibility: np.ndarray) -> bool:
    """Check whether a perfect 1-to-1 matching exists using the Hungarian
    algorithm on the feasibility matrix.  Infeasible cells get infinite cost.
    """
    cost = np.where(feasibility, 0, 1_000_000)
    row_ind, col_ind = linear_sum_assignment(cost)
    return int(cost[row_ind, col_ind].sum()) == 0


def score_profile_vs_part(
    part: dict,
    profile: dict,
    global_min: int,
    global_max: int,
) -> dict:
    """Score one profile against one song part.

    Uses the profile's pre-built ideal vector and per-profile alpha.
    Returns a detail dict with cosine_similarity, avoid_penalty, etc.
    """
    tess = part.get('tessituragram_data', {})
    ideal_vec = profile['ideal_vec']
    min_midi = profile['min_midi']
    max_midi = profile['max_midi']
    alpha = profile.get('alpha', 0.0)
    avoid_midis = profile.get('avoid_midis', [])
    favorite_midis = profile.get('favorite_midis', [])

    dense = build_dense_vector(tess, global_min, global_max)
    normed = normalize_l1(dense)

    cos_sim = cosine_similarity(normed, ideal_vec)

    avoid_indices = [m - global_min for m in avoid_midis if global_min <= m <= global_max]
    fav_indices = [m - global_min for m in favorite_midis if global_min <= m <= global_max]

    avoid_penalty = float(sum(normed[i] for i in avoid_indices)) if avoid_indices else 0.0
    fav_overlap = float(sum(normed[i] for i in fav_indices)) if fav_indices else 0.0
    final_score = cos_sim - alpha * avoid_penalty

    return {
        'cosine_similarity': round(cos_sim, 4),
        'avoid_penalty': round(avoid_penalty, 4),
        'favorite_overlap': round(fav_overlap, 4),
        'final_score': round(final_score, 4),
        'normalized_vector': {
            str(global_min + i): round(float(v), 6)
            for i, v in enumerate(normed)
        },
    }


def _detect_interchangeable(
    profiles: list[dict],
    assignment_details: list[dict],
    score_matrix: np.ndarray,
) -> list[tuple[int, int]]:
    """Return pairs of profile indices that are interchangeable.

    Two profiles are interchangeable when they have identical ideal vectors
    and alphas, and swapping their assigned parts produces the same total.
    """
    n = len(profiles)
    pairs: list[tuple[int, int]] = []
    for i in range(n):
        for j in range(i + 1, n):
            pi, pj = profiles[i], profiles[j]
            if pi.get('alpha', 0.0) != pj.get('alpha', 0.0):
                continue
            if not np.array_equal(pi['ideal_vec'], pj['ideal_vec']):
                continue
            ci = assignment_details[i]['part_index']
            cj = assignment_details[j]['part_index']
            current = score_matrix[i, ci] + score_matrix[j, cj]
            swapped = score_matrix[i, cj] + score_matrix[j, ci]
            if abs(current - swapped) < 1e-9:
                pairs.append((i, j))
    return pairs


def find_optimal_assignment(
    song: dict,
    profiles: list[dict],
    global_min: int,
    global_max: int,
) -> dict | None:
    """Find the best 1-to-1 assignment of profiles to song parts.

    Returns None if no valid assignment exists (some part cannot be covered,
    or a single profile would need to cover two parts).

    The returned dict contains ``average_score``, ``assignment`` details,
    and ``interchangeable_profiles``.
    """
    parts = song.get('tessituragram', [])
    n = len(parts)

    feasibility = build_feasibility_matrix(parts, profiles)
    if not has_valid_assignment(feasibility):
        return None

    # Build N×N score matrix (final_score per profile×part pair)
    score_mat = np.full((n, n), -np.inf)
    detail_cache: dict[tuple[int, int], dict] = {}
    for i, prof in enumerate(profiles):
        for j, part in enumerate(parts):
            if feasibility[i, j]:
                detail = score_profile_vs_part(part, prof, global_min, global_max)
                score_mat[i, j] = detail['final_score']
                detail_cache[(i, j)] = detail

    # Hungarian algorithm (minimises, so negate scores)
    cost = np.where(np.isfinite(score_mat), -score_mat, 1_000_000)
    row_ind, col_ind = linear_sum_assignment(cost)

    assignment: list[dict] = []
    total_score = 0.0
    for pi, pj in zip(row_ind, col_ind):
        if not feasibility[pi, pj]:
            return None  # shouldn't happen, but safety check
        detail = detail_cache[(pi, pj)]
        total_score += detail['final_score']
        part = parts[pj]
        assignment.append({
            'profile_index': int(pi),
            'part_index': int(pj),
            'part_id': part.get('part_id', ''),
            'part_name': part.get('part_name', ''),
            'final_score': detail['final_score'],
            'cosine_similarity': detail['cosine_similarity'],
            'avoid_penalty': detail['avoid_penalty'],
            'favorite_overlap': detail['favorite_overlap'],
            'normalized_vector': detail['normalized_vector'],
            'tessituragram': part.get('tessituragram_data', {}),
            'statistics': part.get('statistics', {}),
        })

    assignment.sort(key=lambda a: a['profile_index'])
    average_score = round(total_score / n, 4)

    interchangeable = _detect_interchangeable(
        profiles, assignment, score_mat,
    )

    return {
        'average_score': average_score,
        'assignment': assignment,
        'interchangeable_profiles': interchangeable,
    }


def score_songs_multi(
    songs: list[dict],
    profiles: list[dict],
    global_min: int,
    global_max: int,
) -> list[dict]:
    """Score all multi-part songs against N profiles.

    Returns ranked results (best average_score first).
    """
    results: list[dict] = []

    for song in songs:
        opt = find_optimal_assignment(song, profiles, global_min, global_max)
        if opt is None:
            continue

        results.append({
            'filename': song.get('filename', ''),
            'composer': song.get('composer', 'Unknown'),
            'title': song.get('title', ''),
            'average_score': opt['average_score'],
            'assignment': opt['assignment'],
            'interchangeable_profiles': opt['interchangeable_profiles'],
        })

    results.sort(key=lambda r: (-r['average_score'], r['filename']))

    for rank, result in enumerate(results, 1):
        result['rank'] = rank
        result['explanation'] = _explain_multi(result, profiles)

    return results


# ═════════════════════════════════════════════════════════════════════════════
# Explanation generators
# ═════════════════════════════════════════════════════════════════════════════

def _explain_solo(
    result: dict,
    favorite_midis: list[int],
    avoid_midis: list[int],
) -> str:
    """Human-readable explanation for a solo recommendation."""
    parts: list[str] = []
    score = result['final_score']
    cos = result['cosine_similarity']
    avoid_pen = result['avoid_penalty']
    fav_over = result.get('favorite_overlap', 0.0)

    parts.append(f"Final score: {score:.2f} (cosine similarity {cos:.2f})")

    if favorite_midis:
        fav_names = ', '.join(midi_to_note_name(m) for m in favorite_midis)
        pct = fav_over * 100
        if pct >= 30:
            parts.append(f"Strong overlap with favorite notes ({fav_names}): {pct:.0f}%.")
        elif pct >= 10:
            parts.append(f"Moderate overlap with favorite notes ({fav_names}): {pct:.0f}%.")
        else:
            parts.append(f"Low overlap with favorite notes ({fav_names}): only {pct:.0f}%.")

    if avoid_midis:
        avoid_names = ', '.join(midi_to_note_name(m) for m in avoid_midis)
        pct = avoid_pen * 100
        if pct <= 2:
            parts.append(f"Minimal avoid-note presence ({avoid_names}): {pct:.1f}%.")
        elif pct <= 10:
            parts.append(f"Some avoid-note presence ({avoid_names}): {pct:.1f}%.")
        else:
            parts.append(f"Notable avoid-note presence ({avoid_names}): {pct:.1f}% — lowered score.")

    return '  '.join(parts)


# kept for backward compat (old callers pass positional min_midi)
def generate_explanation(
    result: dict,
    min_midi: int,
    favorite_midis: list[int],
    avoid_midis: list[int],
) -> str:
    return _explain_solo(result, favorite_midis, avoid_midis)


def _explain_multi(result: dict, profiles: list[dict]) -> str:
    """Human-readable explanation for a multi-part recommendation."""
    lines: list[str] = []
    avg = result['average_score']
    lines.append(f"Average score: {avg:.2f}")

    for a in result['assignment']:
        pi = a['profile_index']
        pname = a['part_name'] or a['part_id']
        fs = a['final_score']
        cs = a['cosine_similarity']
        ap = a['avoid_penalty']
        fo = a['favorite_overlap']
        lines.append(
            f"  Profile {pi + 1} → {pname}: "
            f"score {fs:.2f} (cos sim {cs:.2f}, avoid pen {ap:.2f}, fav overlap {fo:.0%})"
        )

    for i, j in result.get('interchangeable_profiles', []):
        lines.append(f"  Note: Profiles {i + 1} and {j + 1} are interchangeable for their assigned parts.")

    return '\n'.join(lines)
