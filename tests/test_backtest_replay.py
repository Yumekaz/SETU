"""Backtest PIT replay tests."""

from __future__ import annotations

from datetime import date, timedelta

from app.backtest.config import load_backtest_config
from app.backtest.integrity import filter_events_up_to
from app.backtest.replay import (
    build_pit_daily_scores,
    find_first_crossing,
    load_backtest_events,
)
from app.signals.score import build_risk_scores


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


def test_prior_scores_use_prior_date_filter_not_current() -> None:
    """7-day trend must not see events between prior_date and score_date."""
    cfg = load_backtest_config()
    events = load_backtest_events(cfg)
    score_date = cfg.window_start + timedelta(days=14)
    prior_date = score_date - timedelta(days=7)
    visible_prior = filter_events_up_to(events, prior_date)
    prior_scores = {
        s.corridor: s.score
        for s in build_risk_scores(visible_prior, score_date=prior_date)
    }
    visible_current = filter_events_up_to(events, score_date)
    scores_current = build_risk_scores(
        visible_current, score_date=score_date, prior_scores=prior_scores
    )
    hormuz = next(s for s in scores_current if s.corridor == cfg.corridor)
    trajectory = build_pit_daily_scores(events, config=cfg)
    replay_point = next(t for t in trajectory if t.score_date == score_date)
    assert replay_point.score == hormuz.score


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
