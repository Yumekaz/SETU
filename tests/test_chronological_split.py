"""Chronological leakage guard tests (build-failing)."""

from __future__ import annotations

from datetime import date

import pytest
from app.forecast.config import DEFAULT_FEATURES_PATH
from app.forecast.dataset import build_split_windows, load_features_df
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


def test_val_windows_use_train_dates_in_lookback() -> None:
    df = load_features_df(DEFAULT_FEATURES_PATH)
    dates = unique_sorted_dates(df)
    split = chronological_split(dates)
    _, _, meta = build_split_windows(df, split, "val")
    if not meta:
        pytest.skip("no validation windows in current parquet split")
    train_dates = set(split.train_dates)
    _, _, train_meta = build_split_windows(df, split, "train")
    assert train_meta, "expected train windows"
    first_val_origin = min(origin for _, origin in meta)
    idx = dates.index(first_val_origin)
    lookback = dates[idx - 13 : idx + 1]
    overlap = sum(1 for d in lookback if d in train_dates)
    assert overlap > 0, "val lookback should include train dates (inference-aligned)"


def test_build_split_windows_origins_stay_in_partition() -> None:
    df = load_features_df(DEFAULT_FEATURES_PATH)
    dates = unique_sorted_dates(df)
    split = chronological_split(dates)
    for partition in ("train", "val", "test"):
        _, _, meta = build_split_windows(df, split, partition)
        allowed = set(getattr(split, f"{partition}_dates"))
        for _, origin in meta:
            assert origin in allowed
