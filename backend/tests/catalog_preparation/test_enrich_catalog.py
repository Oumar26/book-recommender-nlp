from __future__ import annotations

from collections.abc import Mapping, Sequence

import pytest

from book_recommender.catalog_preparation.application.enrich_catalog import (
    EnrichCatalog,
    EnrichCatalogRequest,
)
from book_recommender.catalog_preparation.domain.books import CatalogBook
from book_recommender.catalog_preparation.domain.labels import LabelSet

THEMES = LabelSet("themes", ("love", "war"), ("about love", "about war"), 0.5, 2)
PERIODS = LabelSet("periods", ("past", "future"), ("in the past", "in the future"), 0.5, 1)


def book(book_id: str, description: str) -> CatalogBook:
    return CatalogBook(
        book_id=book_id,
        title=book_id,
        author="A",
        description=description,
        language="en",
        genre_tags=(),
        genres=(),
        min_age=18,
        pages=None,
        length_category=None,
        year=None,
        series=None,
        cover_url=None,
        rating=None,
        num_ratings=0,
    )


class KeywordClassifier:
    """Fake : probabilité 0,9 si le mot-clé de l'hypothèse apparaît dans le texte, sinon 0,1."""

    def __init__(self) -> None:
        self.texts_seen: list[str] = []

    def scores(self, texts: Sequence[str], hypotheses: Sequence[str]) -> list[list[float]]:
        self.texts_seen.extend(texts)
        return [[0.9 if h.split()[-1] in t else 0.1 for h in hypotheses] for t in texts]


class FirstWords:
    def extract(self, texts: Sequence[str], top_n: int) -> list[list[str]]:
        return [t.split()[:top_n] for t in texts]


class MemoryCache:
    def __init__(self) -> None:
        self.data: dict[str, dict[str, list]] = {}

    def load(self, stage: str) -> dict[str, list]:
        return dict(self.data.get(stage, {}))

    def append(self, stage: str, results: Mapping[str, list]) -> None:
        self.data.setdefault(stage, {}).update(results)


class MemoryIO:
    def __init__(self, books: list[CatalogBook]) -> None:
        self.books = books
        self.written: list[CatalogBook] = []

    def read(self) -> list[CatalogBook]:
        return list(self.books)

    def write(self, books: Sequence[CatalogBook]) -> None:
        self.written = list(books)


BOOKS = [
    book("1", "love in the future"),
    book("2", "war in the past"),
    book("3", "a quiet story"),
]


def make(io, classifier, cache, keywords=None, keyword_cache=None, progress=None):
    return EnrichCatalog(
        io, io, classifier, cache, (THEMES, PERIODS), keywords, keyword_cache, progress
    )


def test_labels_scores_and_keywords_are_written() -> None:
    io = MemoryIO(BOOKS)
    response = make(io, KeywordClassifier(), MemoryCache(), FirstWords())(
        EnrichCatalogRequest(batch_size=2, keywords_top_n=2)
    )
    by_id = {b.book_id: b for b in io.written}

    assert by_id["1"].themes == ("love",)
    assert by_id["1"].theme_scores == (0.9, 0.1)
    assert by_id["1"].period == "future"
    assert by_id["2"].themes == ("war",) and by_id["2"].period == "past"
    assert by_id["3"].themes == () and by_id["3"].period is None
    assert by_id["1"].keywords == ("love", "in")
    assert response.label_counts["themes"] == {"love": 1, "war": 1}
    assert response.without_labels == {"themes": 1, "periods": 1}
    assert response.computed == {"themes": 3, "periods": 3, "keywords": 3}


def test_resumes_from_cache_after_interruption() -> None:
    cache = MemoryCache()

    class FailsOnSecondBatch(KeywordClassifier):
        def scores(self, texts, hypotheses):
            if len(self.texts_seen) >= 2:
                raise RuntimeError("session Colab coupée")
            return super().scores(texts, hypotheses)

    with pytest.raises(RuntimeError):
        make(MemoryIO(BOOKS), FailsOnSecondBatch(), cache)(EnrichCatalogRequest(batch_size=2))
    assert len(next(iter(cache.data.values()))) == 2  # premier lot conservé

    classifier = KeywordClassifier()
    io = MemoryIO(BOOKS)
    response = make(io, classifier, cache)(EnrichCatalogRequest(batch_size=2))

    assert response.computed["themes"] == 1  # seul le livre manquant est recalculé
    assert response.computed["periods"] == 3
    assert len(io.written) == 3


def test_second_run_recomputes_nothing() -> None:
    cache = MemoryCache()
    make(MemoryIO(BOOKS), KeywordClassifier(), cache)(EnrichCatalogRequest())
    classifier = KeywordClassifier()
    response = make(MemoryIO(BOOKS), classifier, cache)(EnrichCatalogRequest())
    assert classifier.texts_seen == []
    assert set(response.computed.values()) == {0}


def test_keywords_use_their_own_cache() -> None:
    label_cache, keyword_cache = MemoryCache(), MemoryCache()
    make(MemoryIO(BOOKS), KeywordClassifier(), label_cache, FirstWords(), keyword_cache)(
        EnrichCatalogRequest(keywords_top_n=3)
    )
    assert list(keyword_cache.data) == ["keywords-top3"]
    assert not any(stage.startswith("keywords") for stage in label_cache.data)


def test_limit_and_progress() -> None:
    events: list[tuple[str, int, int]] = []
    io = MemoryIO(BOOKS)
    make(io, KeywordClassifier(), MemoryCache(), progress=lambda *e: events.append(e))(
        EnrichCatalogRequest(limit=2, with_keywords=False)
    )
    assert len(io.written) == 2
    assert events[-1][1:] == (2, 2)
