"""Flask web application for the Tessituragram Repertoire Recommender."""

from __future__ import annotations

import uuid
from pathlib import Path

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from src.recommend import (
    build_ideal_vector,
    filter_by_range,
    midi_to_note_name,
    score_songs,
    score_songs_multi,
)
from src.storage import (
    discover_ensemble_types,
    filter_by_ensemble_type,
    flatten_song_part,
    load_tessituragrams,
)

app = Flask(__name__)
app.secret_key = 'tessituragram-dev-key-change-in-production'

LIBRARY_PATH = Path('data/all_tessituragrams.json')

_results_store: dict[str, list[dict]] = {}
_charts_store: dict[str, list[dict]] = {}


def _load_library() -> list[dict]:
    return load_tessituragrams(LIBRARY_PATH)


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    songs = _load_library()
    types = discover_ensemble_types(songs)
    type_info = {}
    for num, label in sorted(types.items()):
        count = len(filter_by_ensemble_type(songs, num))
        type_info[num] = {'label': label, 'count': count}
    return render_template('index.html', types=type_info)


@app.route('/select-ensemble', methods=['POST'])
def select_ensemble():
    num_parts = int(request.form['num_parts'])
    ensemble_label = request.form['ensemble_label']
    session['num_parts'] = num_parts
    session['ensemble_label'] = ensemble_label
    session['profiles'] = [None] * num_parts
    session['singer_names'] = [None] * num_parts
    return redirect(url_for('names'))


@app.route('/names')
def names():
    num_parts = session.get('num_parts', 1)
    ensemble_label = session.get('ensemble_label', 'Solo')
    existing_names = session.get('singer_names', [None] * num_parts)
    return render_template(
        'names.html',
        num_parts=num_parts,
        ensemble_label=ensemble_label,
        existing_names=existing_names,
    )


@app.route('/save-names', methods=['POST'])
def save_names():
    num_parts = session.get('num_parts', 1)
    names_list = []
    for i in range(num_parts):
        name = request.form.get(f'name_{i}', '').strip()
        if not name:
            name = f'Singer {i + 1}'
        names_list.append(name)
    session['singer_names'] = names_list
    return redirect(url_for('profile', index=0))


@app.route('/profile/<int:index>')
def profile(index):
    num_parts = session.get('num_parts', 1)
    names_list = session.get('singer_names', [])
    profiles = session.get('profiles', [None] * num_parts)

    if index >= num_parts:
        return redirect(url_for('summary'))

    name = names_list[index] if index < len(names_list) else f'Singer {index + 1}'
    existing = profiles[index] if index < len(profiles) and profiles[index] else {}

    prev_name = names_list[index - 1] if index > 0 and index - 1 < len(names_list) else None
    next_label = None
    if index < num_parts - 1 and index + 1 < len(names_list):
        next_label = names_list[index + 1]

    return render_template(
        'profile.html',
        index=index,
        num_parts=num_parts,
        name=name,
        existing=existing,
        prev_name=prev_name,
        next_label=next_label,
        is_last=(index == num_parts - 1),
    )


@app.route('/api/save-profile/<int:index>', methods=['POST'])
def save_profile_api(index):
    data = request.get_json()
    profiles = session.get('profiles', [])

    while len(profiles) <= index:
        profiles.append(None)

    profiles[index] = {
        'min_midi': data['min_midi'],
        'max_midi': data['max_midi'],
        'favorite_midis': data.get('favorite_midis', []),
        'avoid_midis': data.get('avoid_midis', []),
        'alpha': data.get('alpha', 0.0),
    }
    session['profiles'] = profiles
    session.modified = True
    return jsonify({'ok': True})


@app.route('/summary')
def summary():
    num_parts = session.get('num_parts', 1)
    names_list = session.get('singer_names', [])
    profiles = session.get('profiles', [None] * num_parts)
    ensemble_label = session.get('ensemble_label', 'Solo')

    profile_cards = []
    for i in range(num_parts):
        name = names_list[i] if i < len(names_list) else f'Singer {i + 1}'
        p = profiles[i] if i < len(profiles) and profiles[i] else None
        if p:
            profile_cards.append({
                'index': i,
                'name': name,
                'range_low': midi_to_note_name(p['min_midi']),
                'range_high': midi_to_note_name(p['max_midi']),
                'favorites': [midi_to_note_name(m) for m in p.get('favorite_midis', [])],
                'avoids': [midi_to_note_name(m) for m in p.get('avoid_midis', [])],
                'alpha': p.get('alpha', 0.0),
                'complete': True,
            })
        else:
            profile_cards.append({
                'index': i,
                'name': name,
                'complete': False,
            })

    all_complete = all(c['complete'] for c in profile_cards)

    return render_template(
        'summary.html',
        profiles=profile_cards,
        ensemble_label=ensemble_label,
        all_complete=all_complete,
    )


@app.route('/find-recommendations', methods=['POST'])
def find_recommendations():
    num_parts = session.get('num_parts', 1)
    profiles_data = session.get('profiles', [])
    names_list = session.get('singer_names', [])

    songs = _load_library()
    filtered = filter_by_ensemble_type(songs, num_parts)

    if num_parts == 1:
        p = profiles_data[0]
        ideal_vec = build_ideal_vector(
            p['min_midi'], p['max_midi'],
            p.get('favorite_midis', []),
            p.get('avoid_midis', []),
        )
        flat = [flatten_song_part(s, 0) for s in filtered]
        range_filtered = filter_by_range(flat, p['min_midi'], p['max_midi'])

        results = score_songs(
            range_filtered, ideal_vec,
            p['min_midi'], p['max_midi'],
            p.get('avoid_midis', []),
            p.get('favorite_midis', []),
            p.get('alpha', 0.0),
        )

        profiles_for_charts = [{
            'name': names_list[0] if names_list else 'You',
            'min_midi': p['min_midi'],
            'max_midi': p['max_midi'],
            'ideal_vector': {
                str(p['min_midi'] + j): round(float(v), 6)
                for j, v in enumerate(ideal_vec)
            },
        }]
    else:
        engine_profiles = []
        profiles_for_charts = []
        for i, p in enumerate(profiles_data):
            ideal_vec = build_ideal_vector(
                p['min_midi'], p['max_midi'],
                p.get('favorite_midis', []),
                p.get('avoid_midis', []),
            )
            engine_profiles.append({
                'min_midi': p['min_midi'],
                'max_midi': p['max_midi'],
                'favorite_midis': p.get('favorite_midis', []),
                'avoid_midis': p.get('avoid_midis', []),
                'alpha': p.get('alpha', 0.0),
                'ideal_vec': ideal_vec,
            })
            name = names_list[i] if i < len(names_list) else f'Singer {i + 1}'
            profiles_for_charts.append({
                'name': name,
                'min_midi': p['min_midi'],
                'max_midi': p['max_midi'],
                'ideal_vector': {
                    str(p['min_midi'] + j): round(float(v), 6)
                    for j, v in enumerate(ideal_vec)
                },
            })

        global_min = min(ep['min_midi'] for ep in engine_profiles)
        global_max = max(ep['max_midi'] for ep in engine_profiles)
        results = score_songs_multi(filtered, engine_profiles, global_min, global_max)

    result_id = str(uuid.uuid4())
    _results_store[result_id] = results
    _charts_store[result_id] = profiles_for_charts
    session['result_id'] = result_id
    session['total_songs'] = len(filtered)
    session['matched_songs'] = len(results)

    return redirect(url_for('results'))


@app.route('/results')
def results():
    result_id = session.get('result_id')
    all_results = _results_store.get(result_id, [])
    profiles_for_charts = _charts_store.get(result_id, [])
    names_list = session.get('singer_names', [])
    ensemble_label = session.get('ensemble_label', 'Solo')
    num_parts = session.get('num_parts', 1)
    total_songs = session.get('total_songs', 0)
    matched_songs = session.get('matched_songs', 0)

    page = request.args.get('page', 1, type=int)
    per_page = 10
    total_pages = max(1, -(-len(all_results) // per_page))
    page = max(1, min(page, total_pages))

    start = (page - 1) * per_page
    page_results = all_results[start:start + per_page]

    return render_template(
        'results.html',
        results=page_results,
        names=names_list,
        ensemble_label=ensemble_label,
        num_parts=num_parts,
        page=page,
        total_pages=total_pages,
        total_results=len(all_results),
        total_songs=total_songs,
        matched_songs=matched_songs,
        profiles=profiles_for_charts,
    )


if __name__ == '__main__':
    import os

    # PORT / FLASK_HOST: override if 5000 is taken or you need LAN access (e.g. FLASK_HOST=0.0.0.0).
    port = int(os.environ.get("PORT", "5000"))
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    # Debug reloader spawns a second process; on Windows + synced folders it often breaks binding.
    open_url = "127.0.0.1" if host in ("0.0.0.0", "::") else host
    print(f"\n  Tessituragram UI - open: http://{open_url}:{port}/\n", flush=True)
    app.run(
        debug=True,
        host=host,
        port=port,
        use_reloader=False,
        load_dotenv=False,
    )
