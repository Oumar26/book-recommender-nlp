"""Configuration de l'application.

Seul endroit du code qui lit l'environnement : les autres couches reçoivent
leurs valeurs par injection (main/container.py).

Variables reconnues (toutes optionnelles) :
- BOOKREC_DATA_DIR       dossier des données (défaut : backend/data ; sur Colab : un dossier Drive)
- BOOKREC_OPTIONS_PATH   listes du questionnaire (défaut : backend/data/options.json, versionné)
- BOOKREC_DEVICE         "cpu" (défaut) ou "cuda" (Colab)
- BOOKREC_SBERT_MODEL    modèle SBERT multilingue (choix confirmé en phase 4)
- BOOKREC_NLI_MODEL      modèle NLI du zero-shot (P1-09)
- BOOKREC_KEYWORD_MODEL  modèle d'embeddings de KeyBERT (P1-10)
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

# backend/src/book_recommender/main/settings.py → backend/
_BACKEND_DIR = Path(__file__).resolve().parents[3]

DEFAULT_SBERT_MODEL = "intfloat/multilingual-e5-base"
DEFAULT_NLI_MODEL = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
DEFAULT_KEYWORD_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
_DEVICES = frozenset({"cpu", "cuda"})


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    options_path: Path = field(default=_BACKEND_DIR / "data" / "options.json")
    device: str = "cpu"
    sbert_model: str = DEFAULT_SBERT_MODEL
    nli_model: str = DEFAULT_NLI_MODEL
    keyword_model: str = DEFAULT_KEYWORD_MODEL

    def __post_init__(self) -> None:
        if self.device not in _DEVICES:
            raise ValueError(f"device doit valoir {sorted(_DEVICES)}, reçu : {self.device!r}")

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def cache_dir(self) -> Path:
        return self.processed_dir / "cache"

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
            options_path=Path(
                env.get("BOOKREC_OPTIONS_PATH", _BACKEND_DIR / "data" / "options.json")
            ),
            device=env.get("BOOKREC_DEVICE", "cpu"),
            sbert_model=env.get("BOOKREC_SBERT_MODEL", DEFAULT_SBERT_MODEL),
            nli_model=env.get("BOOKREC_NLI_MODEL", DEFAULT_NLI_MODEL),
            keyword_model=env.get("BOOKREC_KEYWORD_MODEL", DEFAULT_KEYWORD_MODEL),
        )
