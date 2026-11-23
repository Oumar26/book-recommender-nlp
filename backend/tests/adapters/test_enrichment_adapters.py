from __future__ import annotations

from pathlib import Path

from book_recommender.catalog_preparation.adapters.jsonl_result_cache import JsonlResultCache
from book_recommender.catalog_preparation.adapters.options_rules import (
    load_keywords_top_n,
    load_label_sets,
)
from book_recommender.catalog_preparation.adapters.parquet_catalog_reader import (
    ParquetCatalogReader,
)
from book_recommender.catalog_preparation.adapters.parquet_catalog_writer import (
    ParquetCatalogWriter,
)
from book_recommender.catalog_preparation.domain.books import CatalogBook

OPTIONS = Path(__file__).resolve().parents[2] / "data" / "options.json"


def test_label_sets_from_reference_options() -> None:
    sets = {s.name: s for s in load_label_sets(OPTIONS)}
    assert list(sets) == ["themes", "atmospheres", "narrative_styles", "periods"]
    assert "any" not in sets["periods"].ids  # « indifférent » n'est pas une étiquette
    assert all(len(s.ids) == len(s.hypotheses) for s in sets.values())
    assert sets["periods"].max_labels == 1
    assert load_keywords_top_n(OPTIONS) == 8


def test_jsonl_cache_appends_and_ignores_truncated_line(tmp_path: Path) -> None:
    cache = JsonlResultCache(tmp_path / "cache")
    assert cache.load("themes") == {}
    cache.append("themes", {"a": [0.1, 0.9]})
    cache.append("themes", {"b": [0.5, 0.5]})
    with (tmp_path / "cache" / "themes.jsonl").open("a") as f:
        f.write('{"id": "c", "v": [0.')  # écriture interrompue
    assert cache.load("themes") == {"a": [0.1, 0.9], "b": [0.5, 0.5]}
    assert cache.load("periods") == {}


def test_parquet_reader_roundtrip(tmp_path: Path) -> None:
    original = CatalogBook(
        book_id="1",
        title="Dune",
        author="Frank Herbert",
        description="Desert planet.",
        language="en",
        genre_tags=("Science Fiction", "Fiction"),
        genres=("science_fiction",),
        min_age=13,
        pages=None,
        length_category=None,
        year=1965,
        series="Dune #1",
        cover_url=None,
        rating=4.25,
        num_ratings=10,
        themes=("survival",),
        theme_scores=(0.75, 0.25),
        period=None,
        keywords=("desert", "spice"),
    )
    path = tmp_path / "books.parquet"
    ParquetCatalogWriter(path).write([original])
    assert ParquetCatalogReader(path).read() == [original]
