"""Règles de nettoyage (P1-03) : fonctions pures, sans pandas."""

from __future__ import annotations

import html
import re
import unicodedata
from collections.abc import Sequence

from .rules import CatalogRules, ExclusionRule

_TAG = re.compile(r"<[^>]+>")
_SPACES = re.compile(r"\s+")
# « FORTUNE.LOSING » ou « dead.But » : espace manquant entre deux phrases.
_GLUED_SENTENCE = re.compile(r"(?<=[a-z]{2}|[A-Z]{2})([.!?])(?=[A-Z][a-zA-Z])")
# « BEGUN. . . .In » ou « wait...Then » : points de suspension collés à la phrase suivante.
_GLUED_ELLIPSIS = re.compile(r"(\.\s?\.)(?=[A-Z][a-z])")
_ROLE = re.compile(r"\s*\(([^)]*)\)\s*$")


def normalize_text(text: str) -> str:
    """Entités et balises HTML, phrases collées, espaces. La casse est conservée (SBERT, NLI)."""
    text = html.unescape(text)
    text = _TAG.sub(" ", text)
    text = _GLUED_SENTENCE.sub(r"\1 ", text)
    text = _GLUED_ELLIPSIS.sub(r"\1 ", text)
    return _SPACES.sub(" ", text).strip()


def word_count(text: str | None) -> int:
    return len(text.split()) if text else 0


def has_enough_description(description: str | None, min_words: int) -> bool:
    return word_count(description) >= min_words


def language_code(language: str | None, rules: CatalogRules) -> str | None:
    """Code ISO si la langue est acceptée (en, fr), sinon None."""
    return rules.languages.get(language.strip()) if language else None


def is_fiction(tags: Sequence[str], rules: CatalogRules) -> bool:
    tag_set = set(tags)
    return bool(tag_set & rules.fiction_tags) and not tag_set & rules.nonfiction_tags


def exclusion_reason(tags: Sequence[str], rules: CatalogRules) -> str | None:
    """Raison d'exclure le livre (roman graphique, poésie, erotica), ou None."""
    for rule in rules.exclusions:
        if _matches(tags, rule):
            return rule.reason
    return None


def _matches(tags: Sequence[str], rule: ExclusionRule) -> bool:
    considered = tags if rule.within_first_tags is None else tags[: rule.within_first_tags]
    return any(tag in rule.tags for tag in considered)


def primary_author(author: str) -> str:
    """Premier auteur, sans les rôles.

    « Charlotte Brontë, Michael Mason (Editor) » → « Charlotte Brontë ».
    """
    for part in author.split(","):
        name, role = _split_role(part)
        if name and role in (None, "Goodreads Author"):
            return name
    first = author.split(",")[0]
    return _split_role(first)[0] or first.strip()


def _split_role(part: str) -> tuple[str, str | None]:
    match = _ROLE.search(part)
    if not match:
        return part.strip(), None
    return part[: match.start()].strip(), match.group(1).strip()


def _fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.casefold())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^\w\s]", " ", text).split())


def dedup_key(title: str, author: str) -> str:
    """Titre + auteur principal, sans casse, accents ni ponctuation."""
    return f"{_fold(title)}|{_fold(primary_author(author))}"


_TWO_DIGIT_DATE = re.compile(r"^\s*\d{1,2}/\d{1,2}/(\d{2})\s*$")
_FOUR_DIGIT_YEAR = re.compile(r"\b(1\d{3}|20\d{2})\b")


def publication_year(
    first_publish_date: str | None, publish_date: str | None, current_year: int
) -> int | None:
    """Année de première publication.

    firstPublishDate est au format MM/DD/YY (siècle perdu). On prend la plus grande année
    finissant par YY qui ne dépasse pas l'année de l'édition (publishDate, sur 4 chiffres),
    sinon l'année courante. Sans firstPublishDate, on prend l'année de l'édition (4 ou 2
    chiffres). Limite connue : un classique du XIXe peut sortir au XXe (Jane Eyre, « 47 »
    → 1947 si l'édition date de 2006).
    """
    edition_year = None
    if publish_date and (found := _FOUR_DIGIT_YEAR.search(publish_date)):
        edition_year = int(found.group(1))
    for date_text, ceiling in (
        (first_publish_date, edition_year or current_year),
        (None if edition_year else publish_date, current_year),
    ):
        if date_text and (match := _TWO_DIGIT_DATE.match(date_text)):
            year = (ceiling // 100) * 100 + int(match.group(1))
            return year if year <= ceiling else year - 100
    return edition_year
