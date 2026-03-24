"""JSON storage and retrieval for tessituragrams and recommendations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

ENSEMBLE_LABELS = {
    1: 'Solo',
    2: 'Duet',
    3: 'Trio',
    4: 'Quartet',
    5: 'Quintet',
    6: 'Sextet',
    7: 'Septet',
    8: 'Octet',
}


def _ensemble_label(n: int) -> str:
    return ENSEMBLE_LABELS.get(n, f'{n}-part ensemble')


# ── Song helpers (all_tessituragrams.json format) ────────────────────────────

def get_voice_part_count(song: dict) -> int:
    """Return how many voice parts a song has in the multi-part format."""
    tess = song.get('tessituragram', [])
    if isinstance(tess, list):
        return len(tess)
    return 1


def discover_ensemble_types(songs: list[dict]) -> dict[int, str]:
    """Scan a song list and return ``{num_parts: label}`` for each count present."""
    counts: set[int] = set()
    for song in songs:
        counts.add(get_voice_part_count(song))
    return {n: _ensemble_label(n) for n in sorted(counts)}


def filter_by_ensemble_type(songs: list[dict], num_parts: int) -> list[dict]:
    """Keep only songs whose voice-part count equals *num_parts*."""
    return [s for s in songs if get_voice_part_count(s) == num_parts]


def flatten_song_part(song: dict, part_index: int = 0) -> dict:
    """Convert one part of a multi-part song into the flat single-part shape.

    The returned dict looks like the old ``tessituragrams.json`` format so
    that existing solo-path code (``filter_by_range``, ``score_songs``) works
    unchanged.
    """
    parts = song['tessituragram']
    part = parts[part_index]
    return {
        'composer': song.get('composer', 'Unknown'),
        'title': song.get('title', ''),
        'filename': song.get('filename', ''),
        'part_id': part.get('part_id', ''),
        'part_name': part.get('part_name', ''),
        'tessituragram': part.get('tessituragram_data', {}),
        'statistics': part.get('statistics', {}),
    }


# ── Generic song I/O (unchanged) ────────────────────────────────────────────

def merge_songs(existing: list[dict], new: list[dict]) -> list[dict]:
    """Merge new songs into existing list, deduplicating by filename."""
    seen = {s['filename'] for s in existing}
    merged = list(existing)
    for song in new:
        if song['filename'] not in seen:
            merged.append(song)
            seen.add(song['filename'])
    return merged


def save_tessituragrams(songs: list[dict], output_path: Path) -> None:
    """Save tessituragrams to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = {'songs': songs}
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_tessituragrams(input_path: Path) -> list[dict]:
    """Load tessituragrams from JSON file."""
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('songs', [])


# ── Recommendations I/O ──────────────────────────────────────────────────────

def save_recommendations(
    ensemble_type: str,
    num_profiles: int,
    profiles: list[dict],
    recommendations: list[dict],
    output_path: Path,
) -> None:
    """Save ranked recommendations to a JSON file.

    Supports both solo (single profile / single ideal vector) and multi-part
    (N profiles, each with their own ideal vector and alpha).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        'ensemble_type': ensemble_type,
        'num_profiles': num_profiles,
        'profiles': profiles,
        'recommendations': recommendations,
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_recommendations(input_path: Path) -> dict:
    """Load recommendations from a JSON file."""
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ── Query helper ─────────────────────────────────────────────────────────────

def query_tessituragrams(
    songs: list[dict],
    composer: Optional[str] = None,
    title: Optional[str] = None,
    min_midi: Optional[int] = None,
    max_midi: Optional[int] = None,
) -> list[dict]:
    """Filter tessituragrams based on criteria."""
    filtered = songs

    if composer:
        filtered = [
            song for song in filtered
            if composer.lower() in song.get('composer', '').lower()
        ]

    if title:
        filtered = [
            song for song in filtered
            if title.lower() in song.get('title', '').lower()
        ]

    if min_midi is not None or max_midi is not None:
        result = []
        for song in filtered:
            pitch_range = song.get('statistics', {}).get('pitch_range', {})
            song_min = pitch_range.get('min_midi')
            song_max = pitch_range.get('max_midi')
            if song_min is None or song_max is None:
                continue
            if min_midi is not None and song_max < min_midi:
                continue
            if max_midi is not None and song_min > max_midi:
                continue
            result.append(song)
        filtered = result

    return filtered
