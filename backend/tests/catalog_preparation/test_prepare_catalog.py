from __future__ import annotations

from collections.abc import Sequence

from book_recommender.catalog_preparation.application.prepare_catalog import (
    PrepareCatalog,
    PrepareCatalogRequest,
    _percentiles,
)
from book_recommender.catalog_preparation.domain.books import CatalogBook, RawBook

from .conftest import make_raw


class InMemorySource:
    def __init__(self, books: Sequence[RawBook]) -> None:
        self._books = books

    def read(self):
        return iter(self._books)


class InMemoryWriter:
    def __init__(self) -> None:
        self.books: list[CatalogBook] = []

    def write(self, books: Sequence[CatalogBook]) -> None:
        self.books = list(books)


class LengthReadability:
    def grade(self, text: str) -> float:
        return float(len(text))


def run(books: Sequence[RawBook], rules, readability=None):
    writer = InMemoryWriter()
    report = PrepareCatalog(InMemorySource(books), writer, rules, readability)(
        PrepareCatalogRequest(current_year=2026)
    )
    return report, writer.books


def test_each_filter_removes_and_logs_its_rows(rules) -> None:
    books = [
        make_raw("ok"),
        make_raw("ok"),  # identifiant en double
        make_raw("es", language="Spanish"),
        make_raw("none", language=None),
        make_raw("essay", genre_tags=("History",)),
        make_raw("poem", genre_tags=("Poetry", "Fiction")),
        make_raw("short", description="Too short."),
        make_raw("dup", title="TITLE ok!", num_ratings=1),  # doublon titre + auteur, moins noté
    ]
    report, catalog = run(books, rules)

    assert [b.book_id for b in catalog] == ["ok"]
    assert report.input_count == 8
    assert [s.removed for s in report.steps] == [1, 2, 1, 1, 1, 1]
    assert report.output_count == 1


def test_duplicate_keeps_most_rated_edition(rules) -> None:
    books = [
        make_raw("a", title="Dune", num_ratings=5),
        make_raw("b", title="dune", num_ratings=50),
    ]
    _, catalog = run(books, rules)
    assert [b.book_id for b in catalog] == ["b"]


def test_books_are_normalized_and_enriched(rules) -> None:
    raw = make_raw(
        "1",
        title="Le  Petit Prince",
        author="Antoine de Saint-Exupéry, Someone (Translator)",
        description="A pilot meets a little prince.The prince comes from far away.",
        language="French",
        genre_tags=("Fiction", "Childrens", "Fantasy", "Magic"),
        pages=96,
        first_publish_date="04/06/43",
        publish_date="2000",
    )
    report, [book] = run([raw], rules)

    assert book.title == "Le Petit Prince"
    assert book.author == "Antoine de Saint-Exupéry"
    assert "prince. The prince" in book.description
    assert book.language == "fr"
    assert book.genres == ("fantasy",)
    assert book.min_age == 0
    assert book.length_category == "short"
    assert book.year == 1943
    assert report.without_genre == 0


def test_complexity_uses_readability_when_available(rules) -> None:
    books = [
        make_raw("easy", pages=100, description="one two three four five"),
        make_raw("hard", pages=900, description="extraordinarily sophisticated vocabulary " * 5),
    ]
    _, catalog = run(books, rules, LengthReadability())
    by_id = {b.book_id: b for b in catalog}
    assert by_id["easy"].complexity == 1
    assert by_id["hard"].complexity == 5
    assert by_id["hard"].readability_grade is not None


def test_without_readability_complexity_comes_from_pages(rules) -> None:
    _, catalog = run([make_raw("a", pages=100), make_raw("b", pages=500)], rules)
    assert {b.book_id: b.complexity for b in catalog} == {"a": 1, "b": 5}
    assert all(b.readability_grade is None for b in catalog)


def test_percentiles_handle_ties_and_missing_values() -> None:
    assert _percentiles([10, None, 30, 20]) == [0.0, None, 1.0, 0.5]
    assert _percentiles([5, 5, 10]) == [0.25, 0.25, 1.0]
    assert _percentiles([7, None]) == [0.5, None]
