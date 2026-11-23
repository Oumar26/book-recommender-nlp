"""Écriture du catalogue en Parquet (une ligne par livre, listes natives)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from ..domain.books import CatalogBook


class ParquetCatalogWriter:
    def __init__(self, path: Path) -> None:
        self._path = path

    def write(self, books: Sequence[CatalogBook]) -> None:
        rows = [
            {k: list(v) if isinstance(v, tuple) else v for k, v in asdict(b).items()} for b in books
        ]
        frame = pd.DataFrame(rows)
        for column in ("pages", "year", "complexity"):
            frame[column] = frame[column].astype("Int64")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(self._path, index=False)
