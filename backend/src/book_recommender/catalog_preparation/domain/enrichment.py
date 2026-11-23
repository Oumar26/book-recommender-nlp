"""Enrichissements par règles (P1-07, P1-08, P1-11) : fonctions pures."""

from __future__ import annotations

from collections.abc import Sequence

from .rules import CatalogRules

_CHILDREN_TAGS = frozenset({"Childrens", "Middle Grade", "Juvenile"})
_DEMANDING_TAGS = frozenset({"Classics", "Literary Fiction", "Literature"})


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


def complexity(
    pages_percentile: float | None,
    readability_percentile: float | None,
    tags: Sequence[str],
) -> int | None:
    """Complexité 1-5 (P1-11) : heuristique, à valider sur l'échantillon annoté.

    Moyenne des rangs centiles (0-1) du nombre de pages et de la difficulté de lecture
    de la description, ramenée sur 1-5, puis ajustée par les tags : littérature
    jeunesse plafonnée à 2, classiques / littérature +1.
    """
    parts = [p for p in (pages_percentile, readability_percentile) if p is not None]
    if not parts:
        return None
    level = 1 + round(4 * sum(parts) / len(parts))
    tag_set = set(tags)
    if tag_set & _DEMANDING_TAGS:
        level += 1
    if tag_set & _CHILDREN_TAGS:
        level = min(level, 2)
    return max(1, min(5, level))
