from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Protocol

from ..domain.books import CatalogBook, RawBook


class RawBookSource(Protocol):
    def read(self) -> Iterable[RawBook]: ...


class CatalogWriter(Protocol):
    def write(self, books: Sequence[CatalogBook]) -> None: ...
