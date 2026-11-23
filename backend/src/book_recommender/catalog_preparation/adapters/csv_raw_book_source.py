"""Lecture du CSV Best Books Ever (Zenodo) en RawBook."""

from __future__ import annotations

import ast
from collections.abc import Iterator
from pathlib import Path

import pandas as pd

from ..domain.books import RawBook


def _text(value: object) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text or None


def _tags(value: object) -> tuple[str, ...]:
    text = _text(value)
    if not text:
        return ()
    try:
        parsed = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return ()
    return (
        tuple(str(t).strip() for t in parsed if str(t).strip()) if isinstance(parsed, list) else ()
    )


def _int(value: object) -> int | None:
    number = pd.to_numeric(_text(value), errors="coerce")
    return None if pd.isna(number) else int(number)


def _pages(value: object) -> int | None:
    """« 384 » → 384 ; valeurs aberrantes (« 1 page », < 10 ou > 5000) → None."""
    text = _text(value)
    pages = _int(text.split()[0]) if text else None
    return pages if pages is not None and 10 <= pages <= 5000 else None


class CsvRawBookSource:
    def __init__(self, path: Path) -> None:
        self._path = path

    def read(self) -> Iterator[RawBook]:
        frame = pd.read_csv(self._path, dtype=str, keep_default_na=False, na_values=[""])
        for row in frame.itertuples(index=False):
            rating = pd.to_numeric(_text(row.rating), errors="coerce")
            yield RawBook(
                book_id=str(row.bookId),
                title=_text(row.title) or "",
                author=_text(row.author) or "",
                description=_text(row.description),
                language=_text(row.language),
                genre_tags=_tags(row.genres),
                pages=_pages(row.pages),
                series=_text(row.series),
                first_publish_date=_text(row.firstPublishDate),
                publish_date=_text(row.publishDate),
                cover_url=_text(row.coverImg),
                rating=None if pd.isna(rating) else float(rating),
                num_ratings=_int(row.numRatings) or 0,
            )
