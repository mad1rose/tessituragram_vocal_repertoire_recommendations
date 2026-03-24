"""Generate a Jupyter notebook visualising ranked song recommendations."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import nbformat

NOTE_NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']


def _midi_to_note_name(midi_num: int) -> str:
    octave = (midi_num // 12) - 1
    return f"{NOTE_NAMES[midi_num % 12]}{octave}"


def _pretty_pitch(midi_num: int) -> str:
    return f"{_midi_to_note_name(midi_num)} ({midi_num})"


def _song_label(rec: dict) -> str:
    filename = rec.get('filename', '')
    m = re.search(r'no(\d+)-(.+)\.mxl$', filename)
    if m:
        no = m.group(1)
        name = m.group(2).replace('-', ' ').title()
        subtitle = f"No. {no} \u2013 {name}"
    else:
        subtitle = filename

    title = rec.get('title', '')
    composer = rec.get('composer', 'Unknown')
    return f"{title}, {subtitle}\\n{composer}"


# ── Plot code generators ─────────────────────────────────────────────────────

def _make_solo_plot_code(
    rec: dict,
    ideal_vector: dict,
    min_midi: int,
    max_midi: int,
) -> str:
    """Plot code for a solo recommendation (one chart)."""
    normed = rec.get('normalized_vector', {})
    if not normed:
        return f"# Song '{rec.get('filename', '?')}' has no vector data."

    all_midis = list(range(min_midi, max_midi + 1))
    labels = [_pretty_pitch(m) for m in all_midis]
    song_values = [normed.get(str(m), 0.0) for m in all_midis]
    ideal_values = [ideal_vector.get(str(m), 0.0) for m in all_midis]
    num_pitches = len(labels)
    fig_width = max(8, num_pitches * 0.75)

    rank = rec.get('rank', '?')
    score = rec.get('final_score', 0)
    label = _song_label(rec)

    return (
        "import matplotlib.pyplot as plt\n"
        "import numpy as np\n"
        "\n"
        f"labels = {labels!r}\n"
        f"song_vals = {song_values!r}\n"
        f"ideal_vals = {ideal_values!r}\n"
        f"num = {num_pitches}\n"
        "\n"
        "x = np.arange(num)\n"
        f"colors = plt.cm.viridis(np.linspace(0.25, 0.85, num))\n"
        "\n"
        f"fig, ax = plt.subplots(figsize=({fig_width:.1f}, 6))\n"
        "ax.bar(x, song_vals, color=colors, edgecolor='white', linewidth=0.5,\n"
        "       label='Song (normalised)', zorder=2)\n"
        "ax.plot(x, ideal_vals, color='red', linewidth=2, marker='o',\n"
        "        markersize=4, alpha=0.7, label='Ideal vector', zorder=3)\n"
        "ax.set_xticks(x)\n"
        "ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=7)\n"
        "ax.set_ylabel('Proportion of singing time')\n"
        "ax.set_xlabel('Pitch — Note Name (MIDI Number)')\n"
        f"ax.set_title('#{rank}  (score {score:.2f})  ' + {label!r},\n"
        "             fontsize=10, fontweight='bold')\n"
        "ax.legend(fontsize=8)\n"
        "fig.tight_layout()\n"
        "plt.show()\n"
    )


def _make_multi_plot_code(
    rec: dict,
    assignment_entry: dict,
    ideal_vector: dict,
    profile_index: int,
    global_min: int,
    global_max: int,
) -> str:
    """Plot code for one profile-to-part assignment within a multi-part song."""
    normed = assignment_entry.get('normalized_vector', {})
    if not normed:
        return "# No vector data for this part."

    all_midis = list(range(global_min, global_max + 1))
    labels = [_pretty_pitch(m) for m in all_midis]
    song_values = [normed.get(str(m), 0.0) for m in all_midis]
    ideal_values = [ideal_vector.get(str(m), 0.0) for m in all_midis]
    num_pitches = len(labels)
    fig_width = max(8, num_pitches * 0.75)

    rank = rec.get('rank', '?')
    part_name = assignment_entry.get('part_name', '') or assignment_entry.get('part_id', '?')
    score = assignment_entry.get('final_score', 0)
    cos_sim = assignment_entry.get('cosine_similarity', 0)
    title = rec.get('title', '')
    composer = rec.get('composer', '')

    chart_title = (
        f"#{rank}  {title} — Profile {profile_index + 1} → {part_name}\\n"
        f"{composer}  |  score {score:.2f}  (cos sim {cos_sim:.2f})"
    )

    return (
        "import matplotlib.pyplot as plt\n"
        "import numpy as np\n"
        "\n"
        f"labels = {labels!r}\n"
        f"song_vals = {song_values!r}\n"
        f"ideal_vals = {ideal_values!r}\n"
        f"num = {num_pitches}\n"
        "\n"
        "x = np.arange(num)\n"
        f"colors = plt.cm.viridis(np.linspace(0.25, 0.85, num))\n"
        "\n"
        f"fig, ax = plt.subplots(figsize=({fig_width:.1f}, 6))\n"
        "ax.bar(x, song_vals, color=colors, edgecolor='white', linewidth=0.5,\n"
        "       label='Part (normalised)', zorder=2)\n"
        "ax.plot(x, ideal_vals, color='red', linewidth=2, marker='o',\n"
        "        markersize=4, alpha=0.7, label=f'Profile {}"
        " ideal vector', zorder=3)\n".format(profile_index + 1) +
        "ax.set_xticks(x)\n"
        "ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=7)\n"
        "ax.set_ylabel('Proportion of singing time')\n"
        "ax.set_xlabel('Pitch — Note Name (MIDI Number)')\n"
        f"ax.set_title({chart_title!r},\n"
        "             fontsize=10, fontweight='bold')\n"
        "ax.legend(fontsize=8)\n"
        "fig.tight_layout()\n"
        "plt.show()\n"
    )


# ── Notebook generation ──────────────────────────────────────────────────────

def generate_notebook(
    json_path: str = 'data/recommendations.json',
    output_path: str = 'recommendations.ipynb',
) -> None:
    """Read recommendation JSON and write a Jupyter notebook with charts
    comparing each song's tessituragram(s) to the ideal vector(s)."""
    src = Path(json_path)
    if not src.exists():
        print(f"Error: {json_path} not found.")
        print("Run  python -m src.run_recommendations  first.")
        sys.exit(1)

    with open(src, 'r', encoding='utf-8') as f:
        data = json.load(f)

    profiles = data.get('profiles', [])
    recs = data.get('recommendations', [])
    ensemble_type = data.get('ensemble_type', 'Solo')
    num_profiles = data.get('num_profiles', 1)

    if not recs:
        print("No recommendations found in data file.")
        sys.exit(1)

    nb = nbformat.v4.new_notebook()
    nb.metadata['kernelspec'] = {
        'display_name': 'Python 3',
        'language': 'python',
        'name': 'python3',
    }

    # ── Title / summary cell ─────────────────────────────────────────────
    summary_lines = [
        "# Recommended Songs — Tessituragram Comparison\n",
        f"**Ensemble type:** {ensemble_type}  ",
        f"**Number of profiles:** {num_profiles}  \n",
    ]
    for idx, prof in enumerate(profiles):
        rng = prof.get('range', {})
        fav_str = ', '.join(prof.get('favorite_notes', [])) or '(none)'
        avoid_str = ', '.join(prof.get('avoid_notes', [])) or '(none)'
        alpha = prof.get('alpha', 0.0)
        summary_lines.append(
            f"**Profile {idx + 1}:** "
            f"{rng.get('low', '?')} – {rng.get('high', '?')}  |  "
            f"Favorites: {fav_str}  |  Avoid: {avoid_str}  |  "
            f"Alpha: {alpha}  "
        )

    summary_lines.append(f"\n**Songs evaluated:** {len(recs)}  \n")
    summary_lines.append(
        "Each chart shows a part's normalised tessituragram (bars) "
        "overlaid with the **matched profile's ideal vector** (red line).  \n"
        "Songs are ordered from best match (#1) to worst.\n\n"
        "Run **Cell → Run All** (or **Ctrl+Shift+Enter**) to render all charts."
    )
    nb.cells.append(nbformat.v4.new_markdown_cell('\n'.join(summary_lines)))

    # ── Charts ───────────────────────────────────────────────────────────
    is_solo = num_profiles == 1

    if is_solo:
        ideal_vector = profiles[0].get('ideal_vector', {}) if profiles else {}
        rng = profiles[0].get('range', {}) if profiles else {}
        min_midi = rng.get('low_midi', 0)
        max_midi = rng.get('high_midi', 127)

        for rec in recs:
            rank = rec.get('rank', '?')
            title = rec.get('title', '')
            composer = rec.get('composer', '')
            explanation = rec.get('explanation', '')

            md = (
                f"### #{rank}  {title}\n"
                f"**{composer}**  \n"
                f"{explanation}"
            )
            nb.cells.append(nbformat.v4.new_markdown_cell(md))
            code = _make_solo_plot_code(rec, ideal_vector, min_midi, max_midi)
            nb.cells.append(nbformat.v4.new_code_cell(code))

    else:
        global_min = min(
            (p.get('range', {}).get('low_midi', 127) for p in profiles),
            default=0,
        )
        global_max = max(
            (p.get('range', {}).get('high_midi', 0) for p in profiles),
            default=127,
        )

        for rec in recs:
            rank = rec.get('rank', '?')
            title = rec.get('title', '')
            composer = rec.get('composer', '')
            avg = rec.get('average_score', 0)

            header_parts = [
                f"### #{rank}  {title}  ({ensemble_type})",
                f"**{composer}**  ",
                f"**Average score:** {avg:.2f}  \n",
            ]

            for a in rec.get('assignment', []):
                pi = a['profile_index']
                pname = a.get('part_name', '') or a.get('part_id', '')
                header_parts.append(
                    f"- Profile {pi + 1} → {pname} "
                    f"(score {a['final_score']:.2f}, "
                    f"cos sim {a['cosine_similarity']:.2f})"
                )

            for i, j in rec.get('interchangeable_profiles', []):
                header_parts.append(
                    f"\n*Profiles {i + 1} and {j + 1} are interchangeable "
                    f"for their assigned parts.*"
                )

            nb.cells.append(nbformat.v4.new_markdown_cell('\n'.join(header_parts)))

            for a in rec.get('assignment', []):
                pi = a['profile_index']
                ideal_vec = {}
                if pi < len(profiles):
                    ideal_vec = profiles[pi].get('ideal_vector', {})

                code = _make_multi_plot_code(
                    rec, a, ideal_vec, pi, global_min, global_max,
                )
                nb.cells.append(nbformat.v4.new_code_cell(code))

    dest = Path(output_path)
    with open(dest, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)

    print(f"Notebook written to {dest.resolve()}")
    print(f"Contains {len(recs)} recommended song(s).")
    print()
    print("To view, run one of:")
    print(f"    jupyter notebook {output_path}")
    print(f"    jupyter lab {output_path}")
    print("Or open the .ipynb file directly in VS Code / Cursor.")


if __name__ == '__main__':
    generate_notebook()
