"""Cache des résultats NLP : un fichier JSONL par étape, complété lot par lot.

Une ligne = un livre. Une coupure en pleine écriture laisse au pire une dernière ligne
incomplète, ignorée à la relecture : le livre sera simplement recalculé.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path


class JsonlResultCache:
    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def _path(self, stage: str) -> Path:
        return self._directory / f"{stage}.jsonl"

    def load(self, stage: str) -> dict[str, list]:
        path = self._path(stage)
        results: dict[str, list] = {}
        if not path.exists():
            return results
        with path.open(encoding="utf-8") as lines:
            for line in lines:
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                results[item["id"]] = item["v"]
        return results

    def append(self, stage: str, results: Mapping[str, list]) -> None:
        self._directory.mkdir(parents=True, exist_ok=True)
        with self._path(stage).open("a", encoding="utf-8") as out:
            for book_id, value in results.items():
                out.write(json.dumps({"id": book_id, "v": value}, ensure_ascii=False) + "\n")
            out.flush()
            os.fsync(out.fileno())
