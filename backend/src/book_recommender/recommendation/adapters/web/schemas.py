"""Contrat de l'API (P0-06) : schémas Pydantic des requêtes et réponses.

Pydantic reste dans adapters/web : les controllers convertissent ces schémas en
dataclasses de l'application (Request / Response) et inversement.

Les identifiants d'options (genres, thèmes…) sont ceux de data/options.json ;
leur existence est vérifiée par le controller, pas ici, pour ne pas dupliquer
la liste de référence.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

DESCRIPTION_MIN_WORDS = 20
MAX_RECOMMENDATIONS = 3

Likert = Annotated[int, Field(ge=1, le=5)]
Score = Annotated[float, Field(ge=0.0, le=1.0)]


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


# --- GET /api/options ---------------------------------------------------------


class Option(_Schema):
    id: str
    label: str


class OptionsResponse(_Schema):
    genres: list[Option]
    themes: list[Option]
    atmospheres: list[Option]
    narrative_styles: list[Option]
    periods: list[Option]
    avoid_quick_options: list[Option]
    length_categories: list[Option]
    description_min_words: int = DESCRIPTION_MIN_WORDS


# --- POST /api/recommend : requête --------------------------------------------


class RecommendRequest(_Schema):
    """Les 13 champs du questionnaire (SPEC, section 3), plus le filtre « pas de série »."""

    description: str = Field(
        description=f"Ce que le lecteur aime, au moins {DESCRIPTION_MIN_WORDS} mots."
    )
    liked_book_id: str | None = Field(
        default=None, description="Identifiant issu de /api/books/search."
    )
    genres: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    other_themes: str = Field(default="", max_length=300, description="Champ « autre » des thèmes.")
    atmospheres: list[str] = Field(default_factory=list)
    period: str = "any"
    narrative_styles: list[str] = Field(default_factory=list)
    importance_themes: Likert = 3
    importance_style: Likert = 3
    importance_atmosphere: Likert = 3
    avoid_text: str = Field(
        default="",
        max_length=500,
        description="Sans négation : « violence », pas « pas de violence ».",
    )
    avoid_options: list[str] = Field(default_factory=list)
    age: int = Field(gt=0, le=120)
    length: str = "any"
    no_series: bool = False

    @field_validator("description")
    @classmethod
    def _long_enough(cls, value: str) -> str:
        value = value.strip()
        if len(value.split()) < DESCRIPTION_MIN_WORDS:
            raise ValueError(f"la description doit compter au moins {DESCRIPTION_MIN_WORDS} mots")
        return value

    @field_validator("genres", "themes", "atmospheres", "narrative_styles", "avoid_options")
    @classmethod
    def _no_duplicates(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(value))


# --- POST /api/recommend : réponse --------------------------------------------


class Criterion(StrEnum):
    """Termes de la formule de score (SPEC, section 6)."""

    DESCRIPTION = "description"  # w1
    THEMES = "themes"  # w2
    ATMOSPHERE = "atmosphere"  # w3
    STYLE = "style"  # w4
    GENRE = "genre"  # w5
    LIKED_BOOK = "liked_book"  # w6
    AVOID = "avoid"  # w7 (pénalité)


class SoftFilter(StrEnum):
    LENGTH = "length"
    PERIOD = "period"


class BookSummary(_Schema):
    id: str
    title: str
    author: str
    cover_url: str | None = None
    pages: int | None = None
    year: int | None = None
    genres: list[str] = Field(
        default_factory=list, description="Genres normalisés (ids d'options)."
    )


class CriterionScore(_Schema):
    criterion: Criterion
    similarity: Score = Field(description="Valeur du critère, entre 0 et 1.")
    weight: float = Field(ge=0.0, description="Poids effectif (après modulation Likert).")
    contribution: float = Field(description="weight × similarity ; négative pour la pénalité.")
    matched_terms: list[str] = Field(default_factory=list, description="Ex. thèmes communs.")


class SoftFilterEffect(_Schema):
    filter: SoftFilter
    matched: bool
    factor: float = Field(gt=0.0, le=1.0, description="1 si le filtre est respecté ou indifférent.")


class Recommendation(_Schema):
    rank: Annotated[int, Field(ge=1, le=MAX_RECOMMENDATIONS)]
    book: BookSummary
    score: float = Field(description="Score global après filtres souples.")
    criteria: list[CriterionScore]
    soft_filters: list[SoftFilterEffect] = Field(default_factory=list)
    shared_keywords: list[str] = Field(default_factory=list)
    explanation: str


class AffinityValue(_Schema):
    key: str = Field(description="Critère ou id de genre.")
    label: str
    value: Score


class CategoryAffinity(_Schema):
    criteria: list[AffinityValue] = Field(
        description="Radar : affinité moyenne du top par critère."
    )
    genres: list[AffinityValue] = Field(description="Barres : affinité par genre.")


class MapCoordinates(_Schema):
    x: float
    y: float


class RecommendResponse(_Schema):
    recommendations: list[Recommendation] = Field(max_length=MAX_RECOMMENDATIONS)
    category_affinity: CategoryAffinity
    user_map_point: MapCoordinates | None = None
    warning: str | None = Field(
        default=None, description="Renseigné si moins de 3 livres passent le seuil."
    )


# --- GET /api/books/search?q= -------------------------------------------------


class BookSearchResult(_Schema):
    id: str
    title: str
    author: str
    year: int | None = None
    cover_url: str | None = None


class BookSearchResponse(_Schema):
    results: list[BookSearchResult]


# --- GET /api/map -------------------------------------------------------------


class MapPoint(_Schema):
    book_id: str
    title: str
    x: float
    y: float
    genre: str | None = Field(default=None, description="Genre principal, pour la couleur.")
    cluster: int | None = None


class MapResponse(_Schema):
    points: list[MapPoint]
