"""Backtest metrics unit tests."""

from __future__ import annotations

from datetime import date

from app.backtest.metrics import compute_lead_time_days
from app.backtest.replay import DailyScore, find_first_crossing


def test_lead_time_days_formula() -> None:
    assert compute_lead_time_days(date(2026, 3, 4), date(2026, 3, 11)) == 7


def test_no_crossing_returns_none_from_finder() -> None:
    trajectory = [DailyScore(date(2026, 2, 1), 0.1), DailyScore(date(2026, 2, 2), 0.2)]
    assert find_first_crossing(trajectory, 0.35) is None
