from __future__ import annotations

import pytest

from book_recommender.catalog_preparation.domain.books import RawBook
from book_recommender.catalog_preparation.domain.rules import (
    AgeRule,
    CatalogRules,
    ExclusionRule,
    LengthCategory,
)


@pytest.fixture
def rules() -> CatalogRules:
    return CatalogRules(
        languages={"English": "en", "French": "fr"},
        fiction_tags=frozenset({"Fiction", "Fantasy", "Romance"}),
        nonfiction_tags=frozenset({"Nonfiction"}),
        min_description_words=5,
        exclusions=(
            ExclusionRule("poetry", frozenset({"Poetry"}), 3),
            ExclusionRule("erotica", frozenset({"Erotica"}), None),
        ),
        genre_tags={"fantasy": ("Fantasy", "Magic"), "romance": ("Romance",)},
        age_rules=(
            AgeRule(frozenset({"Childrens", "Middle Grade"}), 0),
            AgeRule(frozenset({"Young Adult"}), 13),
        ),
        default_min_age=18,
        length_categories=(
            LengthCategory("short", None, 199),
            LengthCategory("medium", 200, 400),
            LengthCategory("long", 401, None),
        ),
    )


def make_raw(book_id: str = "1", **overrides: object) -> RawBook:
    values: dict[str, object] = {
        "book_id": book_id,
        "title": f"Title {book_id}",
        "author": "Jane Doe",
        "description": "A long enough description of a story.",
        "language": "English",
        "genre_tags": ("Fiction", "Fantasy"),
        "pages": 300,
        "num_ratings": 10,
    }
    values.update(overrides)
    return RawBook(**values)  # type: ignore[arg-type]
