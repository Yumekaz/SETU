"""Backtest PIT replay tests."""

from __future__ import annotations

from datetime import date

from app.backtest.config import load_backtest_config
from app.backtest.replay import (
    build_pit_daily_scores,
    find_first_crossing,
    load_backtest_events,
)


def test_daily_trajectory_length_matches_window() -> None:
    cfg = load_backtest_config()
    events = load_backtest_events(cfg)
    trajectory = build_pit_daily_scores(events, config=cfg)
    expected_days = (cfg.window_end - cfg.window_start).days + 1
    assert len(trajectory) == expected_days


def test_replay_is_deterministic() -> None:
    cfg = load_backtest_config()
    events = load_backtest_events(cfg)
    first = build_pit_daily_scores(events, config=cfg)
    second = build_pit_daily_scores(events, config=cfg)
    assert [(t.score_date, t.score) for t in first] == [(t.score_date, t.score) for t in second]


def test_find_first_crossing_on_synthetic_trajectory() -> None:
    from app.backtest.replay import DailyScore

    trajectory = [
        DailyScore(date(2026, 2, 1), 0.1),
        DailyScore(date(2026, 2, 2), 0.36),
        DailyScore(date(2026, 2, 3), 0.4),
    ]
    crossing = find_first_crossing(trajectory, 0.35)
    assert crossing is not None
    assert crossing.score_date == date(2026, 2, 2)
    assert crossing.score >= 0.35
