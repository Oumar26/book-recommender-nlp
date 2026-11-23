"""Cas d'usage PrepareCatalog (P1-04 à P1-08, P1-11, P1-13).

Nettoyage + enrichissements par règles.

Étape CPU. Les enrichissements NLP (zero-shot, KeyBERT) viennent ensuite, sur GPU.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace

from ..domain import cleaning, enrichment
from ..domain.books import CatalogBook, RawBook
from ..domain.rules import CatalogRules
from .ports import CatalogWriter, RawBookSource, ReadabilityMeter


@dataclass(frozen=True)
class PrepareCatalogRequest:
    current_year: int


@dataclass(frozen=True)
class StepCount:
    step: str
    removed: int
    remaining: int


@dataclass
class PreparationReport:
    input_count: int
    steps: list[StepCount] = field(default_factory=list)
    without_genre: int = 0
    without_pages: int = 0

    @property
    def output_count(self) -> int:
        return self.steps[-1].remaining if self.steps else self.input_count


class PrepareCatalog:
    def __init__(
        self,
        source: RawBookSource,
        writer: CatalogWriter,
        rules: CatalogRules,
        readability: ReadabilityMeter | None = None,
    ) -> None:
        self._source = source
        self._writer = writer
        self._rules = rules
        self._readability = readability

    def __call__(self, request: PrepareCatalogRequest) -> PreparationReport:
        books = list(self._source.read())
        report = PreparationReport(input_count=len(books))
        rules = self._rules

        def step(name: str, keep: Callable[[RawBook], bool]) -> None:
            nonlocal books
            before = len(books)
            books = [b for b in books if keep(b)]
            report.steps.append(StepCount(name, before - len(books), len(books)))

        seen_ids: set[str] = set()

        def first_occurrence(book: RawBook) -> bool:
            if book.book_id in seen_ids:
                return False
            seen_ids.add(book.book_id)
            return True

        step("identifiant en double", first_occurrence)
        step(
            "langue absente ou hors en/fr",
            lambda b: cleaning.language_code(b.language, rules) is not None,
        )
        step("pas de la fiction", lambda b: cleaning.is_fiction(b.genre_tags, rules))
        step(
            "format exclu (BD, poésie, erotica)",
            lambda b: cleaning.exclusion_reason(b.genre_tags, rules) is None,
        )

        books = [
            replace(b, description=cleaning.normalize_text(b.description or "")) for b in books
        ]
        step(
            f"description < {rules.min_description_words} mots",
            lambda b: cleaning.has_enough_description(b.description, rules.min_description_words),
        )

        best: dict[str, RawBook] = {}
        for book in books:
            key = cleaning.dedup_key(book.title, book.author)
            if key not in best or book.num_ratings > best[key].num_ratings:
                best[key] = book
        kept_ids = {b.book_id for b in best.values()}
        step("doublon titre + auteur", lambda b: b.book_id in kept_ids)

        catalog = self._enrich(books, request.current_year)
        report.without_genre = sum(1 for b in catalog if not b.genres)
        report.without_pages = sum(1 for b in catalog if b.pages is None)
        self._writer.write(catalog)
        return report

    def _enrich(self, books: Sequence[RawBook], current_year: int) -> list[CatalogBook]:
        rules = self._rules
        grades = [
            self._readability.grade(b.description or "") if self._readability else None
            for b in books
        ]
        pages_pct = _percentiles([b.pages for b in books])
        grade_pct = _percentiles(grades)
        catalog = []
        for book, grade, p_pct, g_pct in zip(books, grades, pages_pct, grade_pct, strict=True):
            catalog.append(
                CatalogBook(
                    book_id=book.book_id,
                    title=cleaning.normalize_text(book.title),
                    author=cleaning.primary_author(book.author),
                    description=book.description or "",
                    language=cleaning.language_code(book.language, rules) or "",
                    genre_tags=book.genre_tags,
                    genres=enrichment.normalized_genres(book.genre_tags, rules),
                    min_age=enrichment.min_age(book.genre_tags, rules),
                    pages=book.pages,
                    length_category=enrichment.length_category(book.pages, rules),
                    year=cleaning.publication_year(
                        book.first_publish_date, book.publish_date, current_year
                    ),
                    series=book.series,
                    cover_url=book.cover_url,
                    rating=book.rating,
                    num_ratings=book.num_ratings,
                    readability_grade=grade,
                    complexity=enrichment.complexity(p_pct, g_pct, book.genre_tags),
                )
            )
        return catalog


def _percentiles(values: Sequence[float | None]) -> list[float | None]:
    """Rang centile (0-1) de chaque valeur parmi les valeurs connues ; ex aequo → rang moyen."""
    known = sorted(v for v in values if v is not None)
    if len(known) < 2:
        return [0.5 if v is not None else None for v in values]
    first: dict[float, int] = {}
    last: dict[float, int] = {}
    for i, v in enumerate(known):
        first.setdefault(v, i)
        last[v] = i
    n = len(known) - 1
    return [None if v is None else (first[v] + last[v]) / 2 / n for v in values]
