"""Paramètres des règles de préparation, issus de options.json (lu par un adapter)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExclusionRule:
    reason: str
    tags: frozenset[str]
    within_first_tags: int | None  # None : le tag compte où qu'il soit


@dataclass(frozen=True)
class AgeRule:
    tags: frozenset[str]
    min_age: int


@dataclass(frozen=True)
class LengthCategory:
    id: str
    min_pages: int | None
    max_pages: int | None


@dataclass(frozen=True)
class CatalogRules:
    languages: dict[str, str]  # libellé du dataset → code ISO
    fiction_tags: frozenset[str]
    nonfiction_tags: frozenset[str]
    min_description_words: int
    exclusions: tuple[ExclusionRule, ...]
    genre_tags: dict[str, tuple[str, ...]]  # id de genre normalisé → tags Goodreads
    age_rules: tuple[AgeRule, ...]
    default_min_age: int
    length_categories: tuple[LengthCategory, ...]  # sans la catégorie « indifférent »
