"""Commandes hors ligne : `book-recommender <commande>`."""

from __future__ import annotations

import argparse
import json
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
    from ..catalog_preparation.adapters.textstat_readability import TextstatReadability
    from ..catalog_preparation.application.prepare_catalog import (
        PrepareCatalog,
        PrepareCatalogRequest,
    )

    output = settings.processed_dir / "books_clean.parquet"
    use_case = PrepareCatalog(
        source=CsvRawBookSource(settings.raw_dir / BEST_BOOKS_CSV),
        writer=ParquetCatalogWriter(output),
        rules=load_catalog_rules(settings.options_path),
        readability=TextstatReadability(),
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


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="book-recommender")
    commands = parser.add_subparsers(dest="command", required=True)
    dl = commands.add_parser("download", help="télécharger les datasets dans data/raw/")
    dl.add_argument("--force", action="store_true", help="retélécharger même si présent")
    commands.add_parser("prepare-catalog", help="nettoyer et enrichir → books_clean.parquet")
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    if args.command == "download":
        download(settings, force=args.force)
    elif args.command == "prepare-catalog":
        prepare_catalog(settings)


if __name__ == "__main__":
    main()
