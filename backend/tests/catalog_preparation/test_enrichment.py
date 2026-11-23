from __future__ import annotations

import pytest

from book_recommender.catalog_preparation.domain import enrichment


def test_normalized_genres_follow_tag_order_without_duplicates(rules) -> None:
    tags = ("Romance", "Fiction", "Magic", "Fantasy")
    assert enrichment.normalized_genres(tags, rules) == ("romance", "fantasy")


def test_unmapped_tags_give_no_genre(rules) -> None:
    assert enrichment.normalized_genres(("Fiction",), rules) == ()


@pytest.mark.parametrize(
    ("tags", "expected"),
    [
        (("Fiction",), 18),
        (("Young Adult", "Fantasy"), 13),
        (("Young Adult", "Childrens"), 0),
        (("Middle Grade",), 0),
    ],
)
def test_min_age(rules, tags, expected) -> None:
    assert enrichment.min_age(tags, rules) == expected


@pytest.mark.parametrize(
    ("pages", "expected"),
    [(None, None), (1, "short"), (199, "short"), (200, "medium"), (400, "medium"), (401, "long")],
)
def test_length_category(rules, pages, expected) -> None:
    assert enrichment.length_category(pages, rules) == expected


def test_complexity_scale_bounds() -> None:
    assert enrichment.complexity(0.0, 0.0, ()) == 1
    assert enrichment.complexity(1.0, 1.0, ()) == 5
    assert enrichment.complexity(0.5, 0.5, ()) == 3


def test_complexity_uses_available_signal_only() -> None:
    assert enrichment.complexity(None, 1.0, ()) == 5
    assert enrichment.complexity(None, None, ()) is None


def test_complexity_tag_adjustments() -> None:
    assert enrichment.complexity(0.5, 0.5, ("Classics",)) == 4
    assert enrichment.complexity(1.0, 1.0, ("Classics",)) == 5
    assert enrichment.complexity(1.0, 1.0, ("Middle Grade",)) == 2
