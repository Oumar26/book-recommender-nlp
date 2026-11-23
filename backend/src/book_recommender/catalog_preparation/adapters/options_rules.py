"""Construit CatalogRules à partir de data/options.json."""

from __future__ import annotations

import json
from pathlib import Path

from ..domain.labels import LabelSet
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


LABEL_SET_NAMES = ("themes", "atmospheres", "narrative_styles", "periods")


def load_label_sets(options_path: Path) -> tuple[LabelSet, ...]:
    """Listes zero-shot d'options.json ; « indifférent » (sans hypothèse) est ignoré."""
    options = json.loads(options_path.read_text(encoding="utf-8"))
    config = options["enrichment"]
    label_sets = []
    for name in LABEL_SET_NAMES:
        items = [o for o in options[name] if o.get("hypothesis")]
        label_sets.append(
            LabelSet(
                name=name,
                ids=tuple(o["id"] for o in items),
                hypotheses=tuple(o["hypothesis"] for o in items),
                threshold=float(config[name]["threshold"]),
                max_labels=int(config[name]["max_labels"]),
            )
        )
    return tuple(label_sets)


def load_keywords_top_n(options_path: Path) -> int:
    options = json.loads(options_path.read_text(encoding="utf-8"))
    return int(options["enrichment"]["keywords"]["top_n"])
