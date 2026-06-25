"""Daily point-in-time Hormuz risk score replay."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.backtest.config import BacktestConfig
from app.backtest.integrity import assert_events_visible_at, filter_events_up_to, pit_diagnostics
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
        visible_current = filter_events_up_to(events, current)
        assert_events_visible_at(visible_current, current)
        prior_date = current - timedelta(days=7)
        visible_prior = filter_events_up_to(events, prior_date)
        assert_events_visible_at(visible_prior, prior_date)
        prior_scores = {
            s.corridor: s.score
            for s in build_risk_scores(visible_prior, score_date=prior_date)
        }
        scores = build_risk_scores(
            visible_current, score_date=current, prior_scores=prior_scores
        )
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


def find_peak_score(trajectory: list[DailyScore]) -> DailyScore:
    return max(trajectory, key=lambda point: point.score)


def trajectory_summary(trajectory: list[DailyScore], *, head: int = 5) -> dict:
    peak = find_peak_score(trajectory)
    return {
        "length": len(trajectory),
        "peak_date": peak.score_date.isoformat(),
        "peak_score": peak.score,
        "first_scores": [
            {"date": p.score_date.isoformat(), "score": p.score} for p in trajectory[:head]
        ],
        "scores_near_reference": [
            {"date": p.score_date.isoformat(), "score": p.score}
            for p in trajectory
            if p.score_date.month == 3 and p.score_date.day <= 15
        ],
    }