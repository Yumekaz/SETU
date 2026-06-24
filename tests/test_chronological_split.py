"""Chronological leakage guard tests (build-failing)."""

from __future__ import annotations

import pytest

from app.forecast.config import DEFAULT_FEATURES_PATH
from app.forecast.dataset import load_features_df
from app.forecast.split import (
    ChronologicalLeakageError,
    assert_no_chronological_leakage,
    chronological_split,
    unique_sorted_dates,
)


def test_chronological_split_passes_leakage_guard() -> None:
    df = load_features_df(DEFAULT_FEATURES_PATH)
    dates = unique_sorted_dates(df)
    split = chronological_split(dates)
    assert_no_chronological_leakage(split)


def test_leakage_guard_fails_on_violation() -> None:
    from datetime import date

    split = chronological_split(
        [date(2026, 2, 1), date(2026, 3, 1), date(2026, 4, 1), date(2026, 5, 1)]
    )
    bad = type(split)(
        train_dates=[date(2026, 5, 1)],
        val_dates=[],
        test_dates=[date(2026, 2, 1)],
    )
    with pytest.raises(ChronologicalLeakageError):
        assert_no_chronological_leakage(bad)