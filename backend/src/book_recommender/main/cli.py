"""Commandes hors ligne : `book-recommender <commande>`."""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.request
from dataclasses import asdict
from datetime import date

from .settings import Settings

DATASETS = {
    "books_1.Best_Books_Ever.csv": "https://zenodo.org/records/4265096/files/books_1.Best_Books_Ever.csv?download=1",
    "goodbooks10k/books_enriched.csv": "https://raw.githubusercontent.com/malcolmosh/goodbooks-10k-extended/master/books_enriched.csv",
    "goodbooks10k/ratings.csv": "https://raw.githubusercontent.com/malcolmosh/goodbooks-10k-extended/master/ratings.csv",
}
BEST_BOOKS_CSV = "books_1.Best_Books_Ever.csv"


def download(settings: Settings, force: bool = False) -> None:
    """P1-01 : télécharge les datasets dans data/raw/ (ignore ceux déjà présents)."""
    for name, url in DATASETS.items():
        target = settings.raw_dir / name
        if target.exists() and not force:
            print(f"déjà présent : {target}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        print(f"téléchargement : {name}")
        tmp = target.with_suffix(target.suffix + ".part")
        urllib.request.urlretrieve(url, tmp)  # noqa: S310 (URL fixe, https)
        tmp.replace(target)


def prepare_catalog(settings: Settings) -> None:
    """P1-13 : nettoyage + enrichissements par règles → data/processed/books_clean.parquet."""
    from ..catalog_preparation.adapters.csv_raw_book_source import CsvRawBookSource
    from ..catalog_preparation.adapters.options_rules import load_catalog_rules
    from ..catalog_preparation.adapters.parquet_catalog_writer import ParquetCatalogWriter
    from ..catalog_preparation.application.prepare_catalog import (
        PrepareCatalog,
        PrepareCatalogRequest,
    )

    output = settings.processed_dir / "books_clean.parquet"
    use_case = PrepareCatalog(
        source=CsvRawBookSource(settings.raw_dir / BEST_BOOKS_CSV),
        writer=ParquetCatalogWriter(output),
        rules=load_catalog_rules(settings.options_path),
    )
    report = use_case(PrepareCatalogRequest(current_year=date.today().year))

    print(f"{'étape':<40} {'retirés':>8} {'restants':>9}")
    print(f"{'entrée':<40} {'':>8} {report.input_count:>9}")
    for s in report.steps:
        print(f"{s.step:<40} {s.removed:>8} {s.remaining:>9}")
    print(f"sans genre normalisé : {report.without_genre}")
    print(f"sans nombre de pages : {report.without_pages}")
    report_path = settings.processed_dir / "preparation_report.json"
    payload = {**asdict(report), "output_count": report.output_count}
    report_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"→ {output}\n→ {report_path}")


def _slug(model_name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", model_name)


def enrich_catalog(
    settings: Settings, batch_size: int, limit: int | None, with_keywords: bool
) -> None:
    """P1-09, P1-10, P1-12 : zero-shot + KeyBERT → data/processed/books.parquet (GPU conseillé)."""
    from ..catalog_preparation.adapters.jsonl_result_cache import JsonlResultCache
    from ..catalog_preparation.adapters.keybert_keyword_extractor import KeyBertKeywordExtractor
    from ..catalog_preparation.adapters.nli_label_classifier import NliLabelClassifier
    from ..catalog_preparation.adapters.options_rules import load_keywords_top_n, load_label_sets
    from ..catalog_preparation.adapters.parquet_catalog_reader import ParquetCatalogReader
    from ..catalog_preparation.adapters.parquet_catalog_writer import ParquetCatalogWriter
    from ..catalog_preparation.application.enrich_catalog import (
        EnrichCatalog,
        EnrichCatalogRequest,
    )

    started = time.monotonic()
    output = settings.processed_dir / ("books.parquet" if limit is None else "books_sample.parquet")

    def progress(stage: str, done: int, total: int) -> None:
        elapsed = time.monotonic() - started
        print(f"[{elapsed / 60:6.1f} min] {stage:<32} {done:>6}/{total}", flush=True)

    print(f"device={settings.device} · NLI={settings.nli_model}")
    use_case = EnrichCatalog(
        reader=ParquetCatalogReader(settings.processed_dir / "books_clean.parquet"),
        writer=ParquetCatalogWriter(output),
        classifier=NliLabelClassifier(settings.nli_model, device=settings.device),
        cache=JsonlResultCache(settings.cache_dir / _slug(settings.nli_model)),
        label_sets=load_label_sets(settings.options_path),
        keywords=(
            KeyBertKeywordExtractor(settings.keyword_model, device=settings.device)
            if with_keywords
            else None
        ),
        keyword_cache=JsonlResultCache(settings.cache_dir / _slug(settings.keyword_model)),
        on_progress=progress,
    )
    response = use_case(
        EnrichCatalogRequest(
            batch_size=batch_size,
            keywords_top_n=load_keywords_top_n(settings.options_path),
            limit=limit,
            with_keywords=with_keywords,
        )
    )
    for stage, counts in response.label_counts.items():
        top = sorted(counts.items(), key=lambda item: -item[1])
        print(
            f"\n{stage} (sans étiquette : {response.without_labels[stage]}/{response.book_count})"
        )
        print("  " + " · ".join(f"{label} {n}" for label, n in top))
    print(f"\ncalculés à ce passage : {response.computed}")
    print(f"→ {output}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="book-recommender")
    commands = parser.add_subparsers(dest="command", required=True)
    dl = commands.add_parser("download", help="télécharger les datasets dans data/raw/")
    dl.add_argument("--force", action="store_true", help="retélécharger même si présent")
    commands.add_parser("prepare-catalog", help="nettoyer et enrichir → books_clean.parquet")
    en = commands.add_parser("enrich-catalog", help="zero-shot + KeyBERT → books.parquet")
    en.add_argument("--batch-size", type=int, default=256, help="livres par lot mis en cache")
    en.add_argument("--limit", type=int, help="essai sur les N premiers livres")
    en.add_argument("--no-keywords", action="store_true", help="sans KeyBERT")
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    if args.command == "download":
        download(settings, force=args.force)
    elif args.command == "prepare-catalog":
        prepare_catalog(settings)
    elif args.command == "enrich-catalog":
        enrich_catalog(settings, args.batch_size, args.limit, not args.no_keywords)


if __name__ == "__main__":
    main()
