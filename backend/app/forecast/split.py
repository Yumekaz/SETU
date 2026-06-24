"""Chronological train/val/test splits and leakage guard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd


class ChronologicalLeakageError(ValueError):
    pass


@dataclass(frozen=True)
class ChronologicalSplit:
    train_dates: list[date]
    val_dates: list[date]
    test_dates: list[date]


def unique_sorted_dates(df: pd.DataFrame) -> list[date]:
    dates = sorted({date.fromisoformat(str(d)[:10]) for d in df["date"].unique()})
    return dates


def chronological_split(
    dates: list[date],
    *,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
) -> ChronologicalSplit:
    if len(dates) < 3:
        raise ValueError("need at least 3 unique dates for chronological split")
    n = len(dates)
    train_end = max(1, int(n * train_ratio))
    val_end = max(train_end + 1, train_end + int(n * val_ratio))
    val_end = min(val_end, n - 1)
    return ChronologicalSplit(
        train_dates=dates[:train_end],
        val_dates=dates[train_end:val_end],
        test_dates=dates[val_end:],
    )


def assert_no_chronological_leakage(split: ChronologicalSplit) -> None:
    if not split.train_dates or not split.test_dates:
        raise ChronologicalLeakageError("empty train or test date set")
    max_train = max(split.train_dates)
    min_test = min(split.test_dates)
    if max_train >= min_test:
        raise ChronologicalLeakageError(
            f"leakage: max train date {max_train} >= min test date {min_test}"
        )
    if split.val_dates:
        max_val = max(split.val_dates)
        min_val = min(split.val_dates)
        if max_train >= min_val:
            raise ChronologicalLeakageError("leakage: train overlaps val")
        if max_val >= min_test:
            raise ChronologicalLeakageError("leakage: val overlaps test")