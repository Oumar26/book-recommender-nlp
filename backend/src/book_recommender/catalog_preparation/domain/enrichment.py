"""Enrichissements par règles (P1-07, P1-08) : fonctions pures."""

from __future__ import annotations

from collections.abc import Sequence

from .rules import CatalogRules


def normalized_genres(tags: Sequence[str], rules: CatalogRules) -> tuple[str, ...]:
    """Ids de genres normalisés, dans l'ordre des tags Goodreads (votes décroissants)."""
    found: dict[str, None] = {}
    for tag in tags:
        for genre_id, genre_tags in rules.genre_tags.items():
            if tag in genre_tags:
                found.setdefault(genre_id)
    return tuple(found)


def min_age(tags: Sequence[str], rules: CatalogRules) -> int:
    """Âge minimum du livre ; plusieurs tags d'âge → le plus bas (ex. YA + Adult → 13)."""
    tag_set = set(tags)
    ages = [rule.min_age for rule in rules.age_rules if tag_set & rule.tags]
    return min(ages, default=rules.default_min_age)


def length_category(pages: int | None, rules: CatalogRules) -> str | None:
    if pages is None:
        return None
    for category in rules.length_categories:
        low_ok = category.min_pages is None or pages >= category.min_pages
        high_ok = category.max_pages is None or pages <= category.max_pages
        if low_ok and high_ok:
            return category.id
    return None
