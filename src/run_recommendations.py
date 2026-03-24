"""Interactive CLI for generating ranked song recommendations."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from src.storage import (
    load_tessituragrams,
    save_recommendations,
    discover_ensemble_types,
    filter_by_ensemble_type,
    flatten_song_part,
)
from src.recommend import (
    note_name_to_midi,
    midi_to_note_name,
    filter_by_range,
    build_ideal_vector,
    score_songs,
    score_songs_multi,
)


# ── Input helpers ────────────────────────────────────────────────────────────

_RANGE_SEP_RE = re.compile(r'(?<=\d)-')


def _parse_note_or_range(token: str) -> list[int]:
    """Parse a token as a single note or a range (D4-E4)."""
    token = token.strip()
    if not token:
        return []
    parts = _RANGE_SEP_RE.split(token, maxsplit=1)
    if len(parts) == 2:
        low_str, high_str = parts[0].strip(), parts[1].strip()
        if low_str and high_str:
            try:
                low_midi = note_name_to_midi(low_str)
                high_midi = note_name_to_midi(high_str)
                if low_midi > high_midi:
                    low_midi, high_midi = high_midi, low_midi
                return list(range(low_midi, high_midi + 1))
            except ValueError:
                pass
    return [note_name_to_midi(token)]


def _prompt_note(prompt_text: str) -> int:
    """Repeatedly prompt until the user enters a valid note name."""
    while True:
        raw = input(prompt_text).strip()
        if not raw:
            continue
        try:
            midi = note_name_to_midi(raw)
            print(f"  → {midi_to_note_name(midi)} (MIDI {midi})")
            return midi
        except ValueError as e:
            print(f"  Invalid note: {e}")
            print("  Please try again.  Examples: C4, F#4, Bb3, Eb5\n")


def _prompt_note_list(prompt_text: str) -> list[int]:
    """Prompt for a comma-separated list of notes and/or ranges."""
    while True:
        raw = input(prompt_text).strip()
        if not raw:
            return []
        midis: list[int] = []
        bad = False
        for token in raw.split(','):
            token = token.strip()
            if not token:
                continue
            try:
                parsed = _parse_note_or_range(token)
                midis.extend(parsed)
            except ValueError as e:
                print(f"  Invalid note or range '{token}': {e}")
                bad = True
        if bad:
            print("  Please re-enter.  Examples: A4, D5  or  D4-E4  or  A4, C4-E4\n")
            continue
        if midis:
            midis = list(dict.fromkeys(midis))
            midis.sort()
            names = ', '.join(f"{midi_to_note_name(m)} (MIDI {m})" for m in midis)
            print(f"  → {names}")
        return midis


def _prompt_int(prompt_text: str, valid: set[int]) -> int:
    """Prompt until the user enters an integer that is in *valid*."""
    while True:
        raw = input(prompt_text).strip()
        try:
            val = int(raw)
            if val in valid:
                return val
        except ValueError:
            pass
        print(f"  Please enter one of: {', '.join(str(v) for v in sorted(valid))}\n")


# ── Profile collection ───────────────────────────────────────────────────────

def _collect_profile(label: str) -> dict:
    """Prompt for one vocal profile (range, favorites, avoid) and return it
    as a dict ready for the recommendation engine."""
    print(f"\n{'─' * 64}")
    print(f"\n  {label}\n")

    print("  Enter your vocal range\n")
    user_min = _prompt_note("    Lowest note: ")
    user_max = _prompt_note("    Highest note: ")
    if user_min > user_max:
        print("\n    (Swapping — lowest was higher than highest.)")
        user_min, user_max = user_max, user_min
    print(f"\n    Range: {midi_to_note_name(user_min)} – "
          f"{midi_to_note_name(user_max)}  (MIDI {user_min}–{user_max})")

    print(f"\n  Favorite notes (optional)")
    print("    Notes you especially enjoy singing.  Songs that emphasise")
    print("    these notes will rank higher.")
    print("    Single notes (A4, D5) or ranges (D4-E4).  Mix both: A4, D4-E4, F5\n")
    favorite_midis = _prompt_note_list(
        "    Favorite notes (comma-separated; Enter to skip): "
    )
    out = [m for m in favorite_midis if m < user_min or m > user_max]
    if out:
        names = ', '.join(midi_to_note_name(m) for m in out)
        print(f"\n    Note: {names} fall outside your range and will be ignored.")
        favorite_midis = [m for m in favorite_midis if user_min <= m <= user_max]

    print(f"\n  Notes to avoid (optional)")
    print("    Songs that spend time on these notes will be penalised.\n")
    avoid_midis = _prompt_note_list(
        "    Notes to avoid (comma-separated; Enter to skip): "
    )
    out = [m for m in avoid_midis if m < user_min or m > user_max]
    if out:
        names = ', '.join(midi_to_note_name(m) for m in out)
        print(f"\n    Note: {names} fall outside your range and will be ignored.")
        avoid_midis = [m for m in avoid_midis if user_min <= m <= user_max]

    alpha = 0.0

    ideal_vec = build_ideal_vector(user_min, user_max, favorite_midis, avoid_midis)

    return {
        'min_midi': user_min,
        'max_midi': user_max,
        'favorite_midis': favorite_midis,
        'avoid_midis': avoid_midis,
        'alpha': alpha,
        'ideal_vec': ideal_vec,
    }


def _profile_to_serialisable(profile: dict) -> dict:
    """Convert a profile dict to a JSON-safe version (strip numpy arrays)."""
    vec = profile['ideal_vec']
    min_m = profile['min_midi']
    return {
        'range': {
            'low': midi_to_note_name(profile['min_midi']),
            'low_midi': profile['min_midi'],
            'high': midi_to_note_name(profile['max_midi']),
            'high_midi': profile['max_midi'],
        },
        'favorite_notes': [midi_to_note_name(m) for m in profile['favorite_midis']],
        'favorite_midis': profile['favorite_midis'],
        'avoid_notes': [midi_to_note_name(m) for m in profile['avoid_midis']],
        'avoid_midis': profile['avoid_midis'],
        'alpha': profile['alpha'],
        'ideal_vector': {
            str(min_m + i): round(float(v), 6)
            for i, v in enumerate(vec)
        },
    }


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    library_path = Path('data/all_tessituragrams.json')
    output_path = Path('data/recommendations.json')

    # ── Banner ───────────────────────────────────────────────────────────
    print()
    print("=" * 64)
    print("   Tessituragram Repertoire Recommender")
    print("=" * 64)
    print()
    print("This tool recommends songs from your library that best match")
    print("one or more singers' vocal profiles.")
    print()
    print("Enter notes as a note name + octave number.")
    print("  Single notes:  C4, F#4, Bb3, Eb5")
    print("  Ranges: D4-E4 = D4, E4, and all notes in between")
    print("  Mix both:  A4, D4-E4, F5  (comma-separated)")
    print()

    # ── 0. Load library ──────────────────────────────────────────────────
    print("-" * 64)
    print("\nLoading song library...")
    if not library_path.exists():
        print(f"\nError: Library not found at {library_path}")
        print("Run  python -m src.main  first to generate tessituragrams.")
        sys.exit(1)

    all_songs = load_tessituragrams(library_path)
    print(f"  {len(all_songs)} song(s) in library.\n")

    # ── 1. Ensemble type selection ───────────────────────────────────────
    types = discover_ensemble_types(all_songs)
    if not types:
        print("Error: no ensemble types found in library.")
        sys.exit(1)

    print("-" * 64)
    print("\nSTEP 1: What type of song are you looking for?\n")
    for num, label in sorted(types.items()):
        count = len(filter_by_ensemble_type(all_songs, num))
        parts_word = "voice part" if num == 1 else "voice parts"
        print(f"  {num}) {label}  ({num} {parts_word}) — {count} song(s)")
    print()

    num_parts = _prompt_int(
        "  Enter the number for your choice: ", set(types.keys()),
    )
    ensemble_label = types[num_parts]
    songs = filter_by_ensemble_type(all_songs, num_parts)
    print(f"\n  → {ensemble_label} selected.  {len(songs)} song(s) to evaluate.\n")

    if not songs:
        print("No songs of that type in the library.")
        sys.exit(0)

    # ── 2. Collect voice profiles ────────────────────────────────────────
    print("=" * 64)
    if num_parts == 1:
        print("\n  Enter your vocal profile.\n")
    else:
        print(f"\n  You selected {ensemble_label} ({num_parts} voice parts).")
        print(f"  Please enter {num_parts} vocal profile(s), one per singer.")
        print("  The order you enter them does not matter — the system will")
        print("  find the best assignment of singers to parts automatically.\n")

    profiles: list[dict] = []
    for i in range(num_parts):
        label = (
            "Voice Profile"
            if num_parts == 1
            else f"Voice Profile {i + 1} of {num_parts}"
        )
        profiles.append(_collect_profile(label))

    # ── 3. Compute global pitch space bounds ─────────────────────────────
    global_min = min(p['min_midi'] for p in profiles)
    global_max = max(p['max_midi'] for p in profiles)

    # ── 4. Score ─────────────────────────────────────────────────────────
    print(f"\n{'─' * 64}")
    print("\nScoring songs...\n")

    if num_parts == 1:
        prof = profiles[0]
        flat = [flatten_song_part(s, 0) for s in songs]
        filtered = filter_by_range(flat, prof['min_midi'], prof['max_midi'])
        excluded = len(flat) - len(filtered)
        print(f"  {len(filtered)} song(s) fit within your range.")
        print(f"  {excluded} song(s) excluded.\n")

        if not filtered:
            print("No songs match your range. Try widening it.")
            sys.exit(0)

        results = score_songs(
            filtered,
            prof['ideal_vec'],
            prof['min_midi'],
            prof['max_midi'],
            prof['avoid_midis'],
            prof['favorite_midis'],
            prof['alpha'],
        )
    else:
        results = score_songs_multi(songs, profiles, global_min, global_max)
        if not results:
            print("No songs have a valid assignment for all voice profiles.")
            print("Try widening one or more singers' ranges.")
            sys.exit(0)
        excluded = len(songs) - len(results)
        print(f"  {len(results)} song(s) have valid assignments.")
        print(f"  {excluded} song(s) excluded (not all parts coverable).\n")

    # ── 5. Print results ─────────────────────────────────────────────────
    print()
    print("=" * 64)
    print("   RANKED RECOMMENDATIONS (best fit → worst fit)")
    print("=" * 64)
    print()

    if num_parts == 1:
        for r in results:
            pname = r.get('part_name', '')
            part_str = f"  ({pname})" if pname else ''
            print(f"  #{r['rank']}  {r['title']}{part_str}")
            print(f"      Composer: {r['composer']}")
            print(f"      File:     {r['filename']}")
            print(f"      {r['explanation']}")
            print()
    else:
        for r in results:
            print(f"  #{r['rank']}  {r['title']}  ({ensemble_label})")
            print(f"      Composer: {r['composer']}")
            print(f"      File:     {r['filename']}")
            print(f"      Average score: {r['average_score']:.2f}")
            print()
            for a in r['assignment']:
                pi = a['profile_index']
                pname = a['part_name'] or a['part_id']
                print(f"      Profile {pi + 1} → {pname}")
                print(f"        Cosine similarity: {a['cosine_similarity']:.2f}  |  "
                      f"Avoid penalty: {a['avoid_penalty']:.2f}  |  "
                      f"Fav overlap: {a['favorite_overlap']:.0%}")
            for i, j in r.get('interchangeable_profiles', []):
                print(f"      Note: Profiles {i + 1} and {j + 1} are interchangeable"
                      " for their assigned parts.")
            print()

    # ── 6. Save ──────────────────────────────────────────────────────────
    serialisable_profiles = [_profile_to_serialisable(p) for p in profiles]

    save_recommendations(
        ensemble_type=ensemble_label,
        num_profiles=num_parts,
        profiles=serialisable_profiles,
        recommendations=results,
        output_path=output_path,
    )
    print(f"Results saved to {output_path}")
    print()
    print("To visualise the recommended songs' tessituragrams, run:")
    print("    python -m src.visualize_recommendations")
    print()


if __name__ == '__main__':
    main()
