"""Étiquettes zero-shot (thèmes, atmosphères, styles, périodes) : listes fixes et sélection."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class LabelSet:
    """Liste fermée d'options.json, avec une hypothèse NLI par étiquette."""

    name: str  # "themes", "atmospheres", "narrative_styles", "periods"
    ids: tuple[str, ...]
    hypotheses: tuple[str, ...]
    threshold: float
    max_labels: int

    def __post_init__(self) -> None:
        if len(self.ids) != len(self.hypotheses):
            raise ValueError(f"{self.name} : autant d'hypothèses que d'étiquettes attendues")
        if not 0.0 <= self.threshold <= 1.0 or self.max_labels < 1:
            raise ValueError(f"{self.name} : seuil dans [0, 1] et au moins une étiquette")

    @property
    def cache_key(self) -> str:
        """Change dès qu'une étiquette ou une hypothèse change (le cache est alors ignoré)."""
        content = "\n".join(f"{i}={h}" for i, h in zip(self.ids, self.hypotheses, strict=True))
        return f"{self.name}-{hashlib.sha256(content.encode()).hexdigest()[:10]}"


def select_labels(scores: Sequence[float], label_set: LabelSet) -> tuple[str, ...]:
    """Étiquettes au-dessus du seuil, les plus probables d'abord, au plus max_labels."""
    if len(scores) != len(label_set.ids):
        raise ValueError(
            f"{label_set.name} : {len(scores)} scores pour {len(label_set.ids)} étiquettes"
        )
    ranked = sorted(zip(scores, label_set.ids, strict=True), key=lambda pair: -pair[0])
    return tuple(label for score, label in ranked if score >= label_set.threshold)[
        : label_set.max_labels
    ]
