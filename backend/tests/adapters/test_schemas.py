"""Contrat de l'API : schémas Pydantic et données fictives du front (P0-06, P0-07)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from book_recommender.recommendation.adapters.web.schemas import (
    BookSearchResponse,
    MapResponse,
    OptionsResponse,
    RecommendRequest,
    RecommendResponse,
)

REPO = Path(__file__).resolve().parents[3]
MOCKS = REPO / "frontend" / "src" / "api-client" / "mocks"
OPTIONS = json.loads((REPO / "backend" / "data" / "options.json").read_text(encoding="utf-8"))

DESCRIPTION = " ".join(["mot"] * 20)


def _mock(name: str) -> dict:
    return json.loads((MOCKS / name).read_text(encoding="utf-8"))


# --- Requête ------------------------------------------------------------------


def test_minimal_request_uses_neutral_defaults() -> None:
    request = RecommendRequest(description=DESCRIPTION, age=30)
    assert (request.importance_themes, request.importance_style, request.importance_atmosphere) == (
        3,
        3,
        3,
    )
    assert request.period == "any" and request.length == "any"
    assert request.liked_book_id is None


@pytest.mark.parametrize(
    "field", ["importance_themes", "importance_style", "importance_atmosphere"]
)
@pytest.mark.parametrize("value", [0, 6])
def test_likert_must_be_between_1_and_5(field: str, value: int) -> None:
    with pytest.raises(ValidationError):
        RecommendRequest(description=DESCRIPTION, age=30, **{field: value})


@pytest.mark.parametrize("age", [0, -1, 121])
def test_age_must_be_plausible(age: int) -> None:
    with pytest.raises(ValidationError):
        RecommendRequest(description=DESCRIPTION, age=age)


def test_description_needs_20_words() -> None:
    with pytest.raises(ValidationError, match="20 mots"):
        RecommendRequest(description=" ".join(["mot"] * 19), age=30)


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        RecommendRequest(description=DESCRIPTION, age=30, budget=20)


def test_duplicate_tags_are_removed_keeping_order() -> None:
    request = RecommendRequest(description=DESCRIPTION, age=30, themes=["love", "war", "love"])
    assert request.themes == ["love", "war"]


# --- Mocks du front -----------------------------------------------------------


def test_request_mock_is_valid_and_uses_known_ids() -> None:
    request = RecommendRequest.model_validate(_mock("recommend_request.json"))
    keys = ["genres", "themes", "atmospheres", "narrative_styles", "periods"]
    keys += ["avoid_quick_options", "length_categories"]
    known = {key: {o["id"] for o in OPTIONS[key]} for key in keys}
    assert set(request.genres) <= known["genres"]
    assert set(request.themes) <= known["themes"]
    assert set(request.atmospheres) <= known["atmospheres"]
    assert set(request.narrative_styles) <= known["narrative_styles"]
    assert set(request.avoid_options) <= known["avoid_quick_options"]
    assert request.period in known["periods"]
    assert request.length in known["length_categories"]


def test_recommend_mock_is_valid_and_ranked() -> None:
    response = RecommendResponse.model_validate(_mock("recommend.json"))
    scores = [r.score for r in response.recommendations]
    assert [r.rank for r in response.recommendations] == [1, 2, 3]
    assert scores == sorted(scores, reverse=True)
    for rec in response.recommendations:
        for criterion in rec.criteria:
            sign = -1 if criterion.criterion == "avoid" else 1
            assert criterion.contribution == pytest.approx(
                sign * criterion.weight * criterion.similarity, abs=1e-4
            )


def test_options_mock_matches_reference_file() -> None:
    response = OptionsResponse.model_validate(_mock("options.json"))
    for key in [
        "genres",
        "themes",
        "atmospheres",
        "narrative_styles",
        "periods",
        "avoid_quick_options",
    ]:
        expected = [(o["id"], o["label_fr"]) for o in OPTIONS[key]]
        assert [(o.id, o.label) for o in getattr(response, key)] == expected


def test_search_and_map_mocks_are_valid() -> None:
    BookSearchResponse.model_validate(_mock("books_search.json"))
    assert MapResponse.model_validate(_mock("map.json")).points
