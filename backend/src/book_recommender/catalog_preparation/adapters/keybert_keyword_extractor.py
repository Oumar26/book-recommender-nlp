"""Mots-clés par KeyBERT (P1-10) : expressions de 1 à 2 mots, diversifiées (MMR)."""

from __future__ import annotations

from collections.abc import Sequence

DEFAULT_KEYWORD_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class KeyBertKeywordExtractor:
    def __init__(self, model_name: str = DEFAULT_KEYWORD_MODEL, device: str = "cpu") -> None:
        from keybert import KeyBERT
        from sentence_transformers import SentenceTransformer

        self._keybert = KeyBERT(model=SentenceTransformer(model_name, device=device))

    def extract(self, texts: Sequence[str], top_n: int) -> list[list[str]]:
        if not texts:
            return []
        results = self._keybert.extract_keywords(
            list(texts),
            keyphrase_ngram_range=(1, 2),
            stop_words="english",
            top_n=top_n,
            use_mmr=True,
            diversity=0.5,
        )
        if len(texts) == 1:  # KeyBERT renvoie une liste simple pour un seul document
            results = [results]
        return [[keyword for keyword, _ in doc] for doc in results]
