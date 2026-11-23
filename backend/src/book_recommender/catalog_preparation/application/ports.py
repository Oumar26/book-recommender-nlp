from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Protocol

from ..domain.books import CatalogBook, RawBook


class RawBookSource(Protocol):
    def read(self) -> Iterable[RawBook]: ...


class CatalogReader(Protocol):
    def read(self) -> list[CatalogBook]: ...


class CatalogWriter(Protocol):
    def write(self, books: Sequence[CatalogBook]) -> None: ...


class LabelClassifier(Protocol):
    def scores(self, texts: Sequence[str], hypotheses: Sequence[str]) -> list[list[float]]:
        """Probabilité (0-1) que chaque texte implique chaque hypothèse, indépendamment."""
        ...


class KeywordExtractor(Protocol):
    def extract(self, texts: Sequence[str], top_n: int) -> list[list[str]]: ...


class ResultCache(Protocol):
    """Résultats déjà calculés, par étape et par livre : permet de reprendre après une coupure."""

    def load(self, stage: str) -> dict[str, list]: ...

    def append(self, stage: str, results: Mapping[str, list]) -> None: ...
