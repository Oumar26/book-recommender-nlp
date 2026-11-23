"""Classification zero-shot par NLI (transformers), multi-étiquettes.

Pour chaque paire (description, hypothèse), le modèle prédit entailment / neutral /
contradiction. Comme la pipeline « zero-shot-classification » de transformers en mode
multi-étiquettes, on garde softmax(entailment, contradiction)[entailment] : chaque étiquette
est jugée indépendamment des autres.
"""

from __future__ import annotations

from collections.abc import Sequence

DEFAULT_NLI_MODEL = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"


class NliLabelClassifier:
    def __init__(
        self,
        model_name: str = DEFAULT_NLI_MODEL,
        device: str = "cpu",
        batch_size: int = 32,
        max_length: int = 384,
    ) -> None:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self._torch = torch
        self._device = device
        self._batch_size = batch_size
        self._max_length = max_length
        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name).to(device).eval()
        self._model = model.half() if device == "cuda" else model
        label2id = {k.lower(): v for k, v in model.config.label2id.items()}
        self._entailment = label2id["entailment"]
        self._contradiction = label2id["contradiction"]

    def scores(self, texts: Sequence[str], hypotheses: Sequence[str]) -> list[list[float]]:
        torch = self._torch
        pairs = [(text, hypothesis) for text in texts for hypothesis in hypotheses]
        # Trier par longueur limite le remplissage (padding) dans chaque lot.
        order = sorted(range(len(pairs)), key=lambda i: len(pairs[i][0]))
        flat = [0.0] * len(pairs)
        with torch.inference_mode():
            for start in range(0, len(order), self._batch_size):
                batch = order[start : start + self._batch_size]
                encoded = self._tokenizer(
                    [pairs[i][0] for i in batch],
                    [pairs[i][1] for i in batch],
                    truncation="only_first",
                    max_length=self._max_length,
                    padding=True,
                    return_tensors="pt",
                ).to(self._device)
                logits = self._model(**encoded).logits.float()
                pair_logits = logits[:, [self._entailment, self._contradiction]]
                probabilities = torch.softmax(pair_logits, dim=-1)[:, 0].tolist()
                for i, p in zip(batch, probabilities, strict=True):
                    flat[i] = p
        n = len(hypotheses)
        return [flat[k * n : (k + 1) * n] for k in range(len(texts))]
