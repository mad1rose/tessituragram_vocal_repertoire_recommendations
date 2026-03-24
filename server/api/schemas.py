"""Pydantic models for API request / response shapes."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    min_note: str = Field(..., description="Lowest note, e.g. 'E3'")
    max_note: str = Field(..., description="Highest note, e.g. 'A5'")
    favorite_notes: list[str] = Field(default_factory=list)
    avoid_notes: list[str] = Field(default_factory=list)
    alpha: float = Field(default=0.0, ge=0.0, le=1.0)


class SongSummary(BaseModel):
    rank: int
    filename: str
    composer: str
    title: str
    final_score: float
    cosine_similarity: float
    avoid_penalty: float
    favorite_overlap: float
    explanation: str


class SongDetail(BaseModel):
    rank: int
    filename: str
    composer: str
    title: str
    final_score: float
    cosine_similarity: float
    avoid_penalty: float
    favorite_overlap: float
    explanation: str
    tessituragram: dict[str, float]
    normalized_vector: dict[str, float]
    statistics: dict
    ideal_vector: dict[str, float]
    user_min_midi: int
    user_max_midi: int


class RecommendResponse(BaseModel):
    total: int
    results: list[SongSummary]
    user_min_midi: int
    user_max_midi: int


class LibraryInfo(BaseModel):
    total_songs: int
    composers: list[str]
