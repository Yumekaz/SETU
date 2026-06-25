"""Daily point-in-time Hormuz risk score replay."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.backtest.config import BacktestConfig
from app.backtest.integrity import assert_no_future_events, filter_events_up_to
from app.forecast.features import extract_events_from_cache
from app.signals.score import build_risk_scores


@dataclass(frozen=True)
class DailyScore:
    score_date: date
    score: float


def build_pit_daily_scores(
    events: list,
    *,
    config: BacktestConfig,
) -> list[DailyScore]:
    """Replay build_risk_scores daily for the configured corridor."""
    trajectory: list[DailyScore] = []
    current = config.window_start
    while current <= config.window_end:
        visible = filter_events_up_to(events, current)
        assert_no_future_events(visible, current)
        prior_date = current - timedelta(days=7)
        prior_scores = {
            s.corridor: s.score
            for s in build_risk_scores(visible, score_date=prior_date)
        }
        scores = build_risk_scores(visible, score_date=current, prior_scores=prior_scores)
        hormuz = next((s for s in scores if s.corridor == config.corridor), None)
        trajectory.append(
            DailyScore(
                score_date=current,
                score=float(hormuz.score if hormuz else 0.0),
            )
        )
        current += timedelta(days=1)
    return trajectory


def load_backtest_events(config: BacktestConfig) -> list:
    return extract_events_from_cache(config.cache_path)


def find_first_crossing(
    trajectory: list[DailyScore],
    threshold: float,
) -> DailyScore | None:
    for point in trajectory:
        if point.score >= threshold:
            return point
    return None
