"""Construit CatalogRules à partir de data/options.json."""

from __future__ import annotations

import json
from pathlib import Path

from ..domain.rules import AgeRule, CatalogRules, ExclusionRule, LengthCategory


def load_catalog_rules(options_path: Path) -> CatalogRules:
    options = json.loads(options_path.read_text(encoding="utf-8"))
    filters = options["catalog_filters"]
    ages = options["age_rules"]
    return CatalogRules(
        languages=dict(filters["languages"]),
        fiction_tags=frozenset(filters["fiction_tags"]),
        nonfiction_tags=frozenset(filters["nonfiction_tags"]),
        min_description_words=int(filters["min_description_words"]),
        exclusions=tuple(
            ExclusionRule(e["reason"], frozenset(e["goodreads_tags"]), e["within_first_tags"])
            for e in options["catalog_exclusions"]
        ),
        genre_tags={g["id"]: tuple(g["goodreads_tags"]) for g in options["genres"]},
        age_rules=tuple(
            AgeRule(frozenset(r["goodreads_tags"]), int(r["min_age"])) for r in ages["book_min_age"]
        ),
        default_min_age=int(ages["default_min_age"]),
        length_categories=tuple(
            LengthCategory(c["id"], c["min_pages"], c["max_pages"])
            for c in options["length_categories"]
            if c["id"] != "any"
        ),
    )
