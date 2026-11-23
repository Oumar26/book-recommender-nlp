from __future__ import annotations

from collections.abc import Sequence

from book_recommender.catalog_preparation.application.prepare_catalog import (
    PrepareCatalog,
    PrepareCatalogRequest,
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


def run(books: Sequence[RawBook], rules):
    writer = InMemoryWriter()
    report = PrepareCatalog(InMemorySource(books), writer, rules)(
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
