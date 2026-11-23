from __future__ import annotations

import textstat


class TextstatReadability:
    """Niveau scolaire Flesch-Kincaid de la description (anglais ; approximatif en français)."""

    def grade(self, text: str) -> float:
        return float(textstat.flesch_kincaid_grade(text)) if text else 0.0
