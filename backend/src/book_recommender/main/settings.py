"""Configuration de l'application.

Seul endroit du code qui lit l'environnement : les autres couches reçoivent
leurs valeurs par injection (main/container.py).

Variables reconnues (toutes optionnelles) :
- BOOKREC_DATA_DIR      dossier des données (défaut : backend/data)
- BOOKREC_DEVICE        "cpu" (défaut) ou "cuda" (Colab)
- BOOKREC_SBERT_MODEL   modèle SBERT multilingue (choix confirmé en phase 4)
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

# backend/src/book_recommender/main/settings.py → backend/
_BACKEND_DIR = Path(__file__).resolve().parents[3]

DEFAULT_SBERT_MODEL = "intfloat/multilingual-e5-base"
_DEVICES = frozenset({"cpu", "cuda"})


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    device: str = "cpu"
    sbert_model: str = DEFAULT_SBERT_MODEL

    def __post_init__(self) -> None:
        if self.device not in _DEVICES:
            raise ValueError(f"device doit valoir {sorted(_DEVICES)}, reçu : {self.device!r}")

    @property
    def options_path(self) -> Path:
        return self.data_dir / "options.json"

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def embeddings_dir(self) -> Path:
        return self.data_dir / "embeddings"

    @property
    def eval_dir(self) -> Path:
        return self.data_dir / "eval"

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        env = os.environ if env is None else env
        return cls(
            data_dir=Path(env.get("BOOKREC_DATA_DIR", _BACKEND_DIR / "data")),
            device=env.get("BOOKREC_DEVICE", "cpu"),
            sbert_model=env.get("BOOKREC_SBERT_MODEL", DEFAULT_SBERT_MODEL),
        )
