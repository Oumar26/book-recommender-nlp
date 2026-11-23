"""Cas d'usage EnrichCatalog (P1-09, P1-10, P1-12) : enrichissements NLP, prévus pour un GPU.

1. Scores zero-shot NLI de chaque liste d'étiquettes, puis mots-clés KeyBERT : calculés par
   lots, chaque lot est mis en cache aussitôt (reprise possible après une coupure).
2. Sélection des étiquettes à partir des scores (seuil, nombre maximum) : instantanée, donc
   les seuils se recalibrent sans recalculer.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace

from ..domain.books import CatalogBook
from ..domain.labels import LabelSet, select_labels
from .ports import CatalogReader, CatalogWriter, KeywordExtractor, LabelClassifier, ResultCache

KEYWORDS_STAGE = "keywords"
ProgressCallback = Callable[[str, int, int], None]  # étape, livres faits, total


@dataclass(frozen=True)
class EnrichCatalogRequest:
    batch_size: int = 256  # livres par lot mis en cache
    keywords_top_n: int = 8
    limit: int | None = None  # pour un essai sur les premiers livres
    with_keywords: bool = True


@dataclass(frozen=True)
class EnrichCatalogResponse:
    book_count: int
    computed: dict[str, int]  # livres calculés à ce passage, par étape (hors cache)
    label_counts: dict[str, dict[str, int]]  # étape → étiquette → nombre de livres
    without_labels: dict[str, int]  # étape → livres sans aucune étiquette retenue


class EnrichCatalog:
    def __init__(
        self,
        reader: CatalogReader,
        writer: CatalogWriter,
        classifier: LabelClassifier,
        cache: ResultCache,
        label_sets: Sequence[LabelSet],
        keywords: KeywordExtractor | None = None,
        keyword_cache: ResultCache | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> None:
        self._reader = reader
        self._writer = writer
        self._classifier = classifier
        self._cache = cache
        self._label_sets = tuple(label_sets)
        self._keywords = keywords
        self._keyword_cache = keyword_cache or cache
        self._on_progress = on_progress or (lambda stage, done, total: None)

    def __call__(self, request: EnrichCatalogRequest) -> EnrichCatalogResponse:
        books = self._reader.read()
        if request.limit is not None:
            books = books[: request.limit]

        computed: dict[str, int] = {}
        scores: dict[str, dict[str, list]] = {}
        for label_set in self._label_sets:
            hypotheses = label_set.hypotheses
            scores[label_set.name], computed[label_set.name] = self._run_stage(
                self._cache,
                label_set.cache_key,
                books,
                request.batch_size,
                lambda texts, h=hypotheses: self._classifier.scores(texts, h),
            )

        keywords: dict[str, list] = {}
        if request.with_keywords and self._keywords is not None:
            extractor = self._keywords
            keywords, computed[KEYWORDS_STAGE] = self._run_stage(
                self._keyword_cache,
                f"{KEYWORDS_STAGE}-top{request.keywords_top_n}",
                books,
                request.batch_size,
                lambda texts: extractor.extract(texts, request.keywords_top_n),
            )

        enriched = [self._apply(book, scores, keywords) for book in books]
        self._writer.write(enriched)
        return self._summary(enriched, computed)

    def _run_stage(
        self,
        cache: ResultCache,
        stage: str,
        books: Sequence[CatalogBook],
        batch_size: int,
        compute: Callable[[list[str]], list[list]],
    ) -> tuple[dict[str, list], int]:
        results = cache.load(stage)
        todo = [b for b in books if b.book_id not in results]
        done = len(books) - len(todo)
        self._on_progress(stage, done, len(books))
        for start in range(0, len(todo), batch_size):
            batch = todo[start : start + batch_size]
            outputs = compute([b.description for b in batch])
            if len(outputs) != len(batch):
                raise RuntimeError(f"{stage} : {len(outputs)} résultats pour {len(batch)} livres")
            new = {b.book_id: out for b, out in zip(batch, outputs, strict=True)}
            cache.append(stage, new)
            results.update(new)
            done += len(batch)
            self._on_progress(stage, done, len(books))
        return results, len(todo)

    def _apply(
        self, book: CatalogBook, scores: dict[str, dict[str, list]], keywords: dict[str, list]
    ) -> CatalogBook:
        changes: dict[str, object] = {}
        for label_set in self._label_sets:
            book_scores = tuple(float(s) for s in scores[label_set.name][book.book_id])
            labels = select_labels(book_scores, label_set)
            if label_set.name == "periods":
                changes["period"] = labels[0] if labels else None
                changes["period_scores"] = book_scores
            else:
                changes[label_set.name] = labels
                changes[_SCORE_FIELDS[label_set.name]] = book_scores
        if book.book_id in keywords:
            changes["keywords"] = tuple(keywords[book.book_id])
        return replace(book, **changes)  # type: ignore[arg-type]

    def _summary(
        self, books: Sequence[CatalogBook], computed: dict[str, int]
    ) -> EnrichCatalogResponse:
        label_counts: dict[str, dict[str, int]] = {}
        without: dict[str, int] = {}
        for label_set in self._label_sets:
            counts = dict.fromkeys(label_set.ids, 0)
            empty = 0
            for book in books:
                chosen = _chosen(book, label_set.name)
                empty += not chosen
                for label in chosen:
                    counts[label] += 1
            label_counts[label_set.name] = counts
            without[label_set.name] = empty
        return EnrichCatalogResponse(len(books), computed, label_counts, without)


_SCORE_FIELDS = {
    "themes": "theme_scores",
    "atmospheres": "atmosphere_scores",
    "narrative_styles": "narrative_style_scores",
}


def _chosen(book: CatalogBook, stage: str) -> tuple[str, ...]:
    if stage == "periods":
        return (book.period,) if book.period else ()
    return getattr(book, stage)
