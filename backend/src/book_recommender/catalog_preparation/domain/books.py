"""Livres avant et après préparation du catalogue."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RawBook:
    """Ligne brute de Best Books Ever, déjà décodée (listes Python, nombres)."""

    book_id: str
    title: str
    author: str
    description: str | None
    language: str | None
    genre_tags: tuple[str, ...]
    pages: int | None = None
    series: str | None = None
    first_publish_date: str | None = None
    publish_date: str | None = None
    cover_url: str | None = None
    rating: float | None = None
    num_ratings: int = 0


@dataclass(frozen=True)
class CatalogBook:
    """Livre nettoyé et enrichi, tel qu'écrit dans books.parquet."""

    book_id: str
    title: str
    author: str
    description: str
    language: str  # code ISO : "en", "fr"
    genre_tags: tuple[str, ...]  # tags Goodreads d'origine, par votes décroissants
    genres: tuple[str, ...]  # ids normalisés (options.json)
    min_age: int
    pages: int | None
    length_category: str | None  # "short" | "medium" | "long" | None si pages inconnues
    year: int | None
    series: str | None
    cover_url: str | None
    rating: float | None
    num_ratings: int
    readability_grade: float | None = None
    complexity: int | None = None  # 1-5
    # Colonnes NLP (zero-shot, KeyBERT), remplies par l'étape d'enrichissement sur GPU.
    themes: tuple[str, ...] = field(default=())
    atmospheres: tuple[str, ...] = field(default=())
    narrative_styles: tuple[str, ...] = field(default=())
    period: str | None = None
    keywords: tuple[str, ...] = field(default=())
