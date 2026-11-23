from __future__ import annotations

import pytest

from book_recommender.catalog_preparation.domain.labels import LabelSet, select_labels


def label_set(threshold: float = 0.5, max_labels: int = 2) -> LabelSet:
    return LabelSet("themes", ("love", "war", "grief"), ("h1", "h2", "h3"), threshold, max_labels)


def test_keeps_labels_above_threshold_most_probable_first() -> None:
    assert select_labels([0.6, 0.9, 0.2], label_set()) == ("war", "love")


def test_caps_number_of_labels() -> None:
    assert select_labels([0.6, 0.9, 0.7], label_set(max_labels=2)) == ("war", "grief")


def test_threshold_is_inclusive_and_can_leave_no_label() -> None:
    assert select_labels([0.5, 0.1, 0.1], label_set()) == ("love",)
    assert select_labels([0.4, 0.1, 0.1], label_set()) == ()


def test_scores_must_match_labels() -> None:
    with pytest.raises(ValueError):
        select_labels([0.9, 0.1], label_set())


@pytest.mark.parametrize(
    "kwargs",
    [{"hypotheses": ("h1",)}, {"threshold": 1.5}, {"max_labels": 0}],
)
def test_invalid_label_sets_are_rejected(kwargs) -> None:
    values = {"name": "t", "ids": ("a", "b"), "hypotheses": ("x", "y"), "threshold": 0.5}
    values["max_labels"] = 1
    values.update(kwargs)
    with pytest.raises(ValueError):
        LabelSet(**values)


def test_cache_key_changes_with_hypotheses_only() -> None:
    base = label_set()
    assert base.cache_key == label_set(threshold=0.9, max_labels=1).cache_key
    changed = LabelSet("themes", base.ids, ("h1", "h2", "other"), 0.5, 2)
    assert changed.cache_key != base.cache_key
    assert base.cache_key.startswith("themes-")
