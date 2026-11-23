"""Lecture de books_clean.parquet (ou books.parquet) en CatalogBook."""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import numpy as np
import pandas as pd

from ..domain.books import CatalogBook

_FIELDS = [f.name for f in fields(CatalogBook)]


def _value(value: object) -> object:
    if isinstance(value, np.ndarray | list | tuple):
        return tuple(v.item() if isinstance(v, np.generic) else v for v in value)
    if value is None or value is pd.NA or (isinstance(value, float) and np.isnan(value)):
        return None
    return value.item() if isinstance(value, np.generic) else value


class ParquetCatalogReader:
    def __init__(self, path: Path) -> None:
        self._path = path

    def read(self) -> list[CatalogBook]:
        frame = pd.read_parquet(self._path)
        columns = [c for c in _FIELDS if c in frame.columns]
        return [
            CatalogBook(**{c: _value(v) for c, v in zip(columns, row, strict=True)})
            for row in frame[columns].itertuples(index=False, name=None)
        ]
