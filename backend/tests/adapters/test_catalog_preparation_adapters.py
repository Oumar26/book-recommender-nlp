from __future__ import annotations

from pathlib import Path

import pandas as pd

from book_recommender.catalog_preparation.adapters.csv_raw_book_source import CsvRawBookSource
from book_recommender.catalog_preparation.adapters.options_rules import load_catalog_rules
from book_recommender.catalog_preparation.adapters.parquet_catalog_writer import (
    ParquetCatalogWriter,
)
from book_recommender.catalog_preparation.domain.books import CatalogBook

OPTIONS = Path(__file__).resolve().parents[2] / "data" / "options.json"

HEADER = (
    "bookId,title,series,author,rating,description,language,isbn,genres,characters,bookFormat,"
    "edition,pages,publisher,publishDate,firstPublishDate,awards,numRatings,ratingsByStars,"
    "likedPercent,setting,coverImg,bbeScore,bbeVotes,price"
)


def test_rules_load_from_reference_options() -> None:
    rules = load_catalog_rules(OPTIONS)
    assert rules.languages == {"English": "en", "French": "fr"}
    assert len(rules.genre_tags) == 10
    assert "crime_thriller" in rules.genre_tags
    assert [c.id for c in rules.length_categories] == ["short", "medium", "long"]
    assert {e.reason for e in rules.exclusions} >= {"poetry", "erotica"}


def test_csv_source_decodes_lists_numbers_and_missing_values(tmp_path: Path) -> None:
    csv = tmp_path / "books.csv"
    csv.write_text(
        HEADER + "\n"
        '1-a,Dune,Dune #1,Frank Herbert,4.25,"Desert planet.",English,1,'
        "\"['Science Fiction', 'Fiction']\",[],Paperback,,412,Ace,"
        "August 2nd 2005,08/01/65,[],1000,[],95,[],http://c.jpg,1,1,\n"
        "2-b,Odd,,Anon,,,,1,not-a-list,[],,,1 page,,,,[],,[],,[],,1,1,\n",
        encoding="utf-8",
    )
    first, second = list(CsvRawBookSource(csv).read())

    assert first.genre_tags == ("Science Fiction", "Fiction")
    assert (first.pages, first.rating, first.num_ratings) == (412, 4.25, 1000)
    assert first.series == "Dune #1"
    assert second.genre_tags == ()
    assert second.pages is None and second.rating is None and second.description is None
    assert second.num_ratings == 0


def test_parquet_writer_roundtrip(tmp_path: Path) -> None:
    book = CatalogBook(
        book_id="1",
        title="Dune",
        author="Frank Herbert",
        description="Desert planet.",
        language="en",
        genre_tags=("Science Fiction",),
        genres=("science_fiction",),
        min_age=18,
        pages=None,
        length_category=None,
        year=1965,
        series=None,
        cover_url=None,
        rating=4.2,
        num_ratings=10,
    )
    path = tmp_path / "out" / "books.parquet"
    ParquetCatalogWriter(path).write([book])
    frame = pd.read_parquet(path)

    assert list(frame.loc[0, "genres"]) == ["science_fiction"]
    assert pd.isna(frame.loc[0, "pages"])
    assert frame.loc[0, "year"] == 1965
