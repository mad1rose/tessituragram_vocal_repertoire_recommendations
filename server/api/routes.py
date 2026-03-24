"""API routes for the recommendation engine."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

# Add project root to path so we can import src.*
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.storage import load_tessituragrams
from src.recommend import (
    note_name_to_midi,
    midi_to_note_name,
    filter_by_range,
    build_ideal_vector,
    score_songs,
)

from .schemas import (
    RecommendRequest,
    RecommendResponse,
    SongSummary,
    SongDetail,
    LibraryInfo,
)

router = APIRouter(prefix="/api")

LIBRARY_PATH = PROJECT_ROOT / "data" / "tessituragrams.json"

_cached_songs: list[dict] | None = None


def _get_songs() -> list[dict]:
    global _cached_songs
    if _cached_songs is None:
        if not LIBRARY_PATH.exists():
            raise HTTPException(
                status_code=500,
                detail="tessituragrams.json not found. Run  python -m src.main  first.",
            )
        _cached_songs = load_tessituragrams(LIBRARY_PATH)
    return _cached_songs


_last_results: list[dict] = []
_last_ideal: dict[str, float] = {}
_last_min_midi: int = 0
_last_max_midi: int = 0


@router.get("/library", response_model=LibraryInfo)
def get_library_info():
    songs = _get_songs()
    composers = sorted({s.get("composer", "Unknown") for s in songs})
    return LibraryInfo(total_songs=len(songs), composers=composers)


@router.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    global _last_results, _last_ideal, _last_min_midi, _last_max_midi

    try:
        user_min = note_name_to_midi(req.min_note)
        user_max = note_name_to_midi(req.max_note)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if user_min > user_max:
        user_min, user_max = user_max, user_min

    fav_midis: list[int] = []
    for n in req.favorite_notes:
        try:
            m = note_name_to_midi(n)
            if user_min <= m <= user_max:
                fav_midis.append(m)
        except ValueError:
            pass

    avoid_midis: list[int] = []
    for n in req.avoid_notes:
        try:
            m = note_name_to_midi(n)
            if user_min <= m <= user_max:
                avoid_midis.append(m)
        except ValueError:
            pass

    songs = _get_songs()
    filtered = filter_by_range(songs, user_min, user_max)

    if not filtered:
        return RecommendResponse(
            total=0, results=[], user_min_midi=user_min, user_max_midi=user_max
        )

    ideal_vec = build_ideal_vector(user_min, user_max, fav_midis, avoid_midis)
    results = score_songs(filtered, ideal_vec, user_min, user_max, avoid_midis, fav_midis, req.alpha)

    ideal_dict = {
        str(user_min + i): round(float(v), 6) for i, v in enumerate(ideal_vec)
    }

    _last_results = results
    _last_ideal = ideal_dict
    _last_min_midi = user_min
    _last_max_midi = user_max

    summaries = [
        SongSummary(
            rank=r["rank"],
            filename=r["filename"],
            composer=r["composer"],
            title=r["title"],
            final_score=r["final_score"],
            cosine_similarity=r["cosine_similarity"],
            avoid_penalty=r["avoid_penalty"],
            favorite_overlap=r["favorite_overlap"],
            explanation=r["explanation"],
        )
        for r in results
    ]

    return RecommendResponse(
        total=len(summaries),
        results=summaries,
        user_min_midi=user_min,
        user_max_midi=user_max,
    )


@router.get("/song/{filename}", response_model=SongDetail)
def get_song_detail(filename: str):
    for r in _last_results:
        if r["filename"] == filename:
            return SongDetail(
                rank=r["rank"],
                filename=r["filename"],
                composer=r["composer"],
                title=r["title"],
                final_score=r["final_score"],
                cosine_similarity=r["cosine_similarity"],
                avoid_penalty=r["avoid_penalty"],
                favorite_overlap=r["favorite_overlap"],
                explanation=r["explanation"],
                tessituragram=r["tessituragram"],
                normalized_vector=r["normalized_vector"],
                statistics=r["statistics"],
                ideal_vector=_last_ideal,
                user_min_midi=_last_min_midi,
                user_max_midi=_last_max_midi,
            )
    raise HTTPException(status_code=404, detail="Song not found in last results")
