from __future__ import annotations

import pytest

from book_recommender.catalog_preparation.domain import cleaning


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Hello&nbsp;<b>world</b>", "Hello world"),
        ("FAME AND FORTUNE.LOSING MEANS DEATH", "FAME AND FORTUNE. LOSING MEANS DEATH"),
        ("she was dead.But she lived", "she was dead. But she lived"),
        ("HAVE BEGUN. . . .In the ruins", "HAVE BEGUN. . . . In the ruins"),
        ("wait...Then", "wait... Then"),
        ("Born in the U.S.A. today", "Born in the U.S.A. today"),
        ("  many \n\t spaces  ", "many spaces"),
    ],
)
def test_normalize_text(raw: str, expected: str) -> None:
    assert cleaning.normalize_text(raw) == expected


def test_normalize_text_keeps_case() -> None:
    assert cleaning.normalize_text("Paris Is Burning") == "Paris Is Burning"


def test_description_threshold() -> None:
    assert cleaning.has_enough_description("one two three", 3)
    assert not cleaning.has_enough_description("one two", 3)
    assert not cleaning.has_enough_description(None, 1)


def test_language_code(rules) -> None:
    assert cleaning.language_code("English", rules) == "en"
    assert cleaning.language_code(" French ", rules) == "fr"
    assert cleaning.language_code("Spanish", rules) is None
    assert cleaning.language_code(None, rules) is None


def test_is_fiction(rules) -> None:
    assert cleaning.is_fiction(("Fantasy", "Adventure"), rules)
    assert not cleaning.is_fiction(("History",), rules)
    assert not cleaning.is_fiction(("Fiction", "Nonfiction"), rules)


def test_exclusion_respects_tag_rank(rules) -> None:
    assert cleaning.exclusion_reason(("Poetry", "Fiction"), rules) == "poetry"
    assert cleaning.exclusion_reason(("Fiction", "Romance", "Drama", "Poetry"), rules) is None
    assert cleaning.exclusion_reason(("Fiction", "Romance", "Drama", "Erotica"), rules) == "erotica"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "Charlotte Brontë, Michael Mason (Editor), Barnett Freedman (Illustrator)",
            "Charlotte Brontë",
        ),
        ("Markus Zusak (Goodreads Author)", "Markus Zusak"),
        ("F. Scott Fitzgerald, Francis Scott Fitzgerald", "F. Scott Fitzgerald"),
        ("Lydia Davis (Translator), Gustave Flaubert", "Gustave Flaubert"),
        ("Anonymous (Editor)", "Anonymous"),
    ],
)
def test_primary_author(raw: str, expected: str) -> None:
    assert cleaning.primary_author(raw) == expected


def test_dedup_key_ignores_case_accents_punctuation_and_roles() -> None:
    a = cleaning.dedup_key("Jane Eyre!", "Charlotte Brontë, M. Mason (Editor)")
    b = cleaning.dedup_key("jane  eyre", "Charlotte Bronte")
    assert a == b


@pytest.mark.parametrize(
    ("first", "edition", "expected"),
    [
        ("07/11/60", "May 2006", 1960),
        ("04/10/25", "2004", 1925),
        ("09/01/05", "March 14th 2006", 2005),
        ("10/16/47", "2006", 1947),  # limite connue : Jane Eyre (1847)
        (None, "August 10th 2010", 2010),
        (None, "09/14/08", 2008),
        (None, None, None),
        ("unknown", None, None),
    ],
)
def test_publication_year(first, edition, expected) -> None:
    assert cleaning.publication_year(first, edition, current_year=2026) == expected
