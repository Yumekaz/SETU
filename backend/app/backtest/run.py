"""Backtest harness entry point."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any

from app.backtest.config import BacktestConfig, load_backtest_config
from app.backtest.metrics import (
    SecondaryComparison,
    compare_recommendation_to_ground_truth,
    compute_lead_time_days,
    crossing_summary,
)
from app.backtest.pipeline import run_full_chain_pit
from app.backtest.replay import (
    build_pit_daily_scores,
    find_first_crossing,
    load_backtest_events,
)


@dataclass(frozen=True)
class BacktestResult:
    status: str
    reference_point_date: date
    reference_point_label: str
    risk_threshold: float
    first_crossing_date: date | None
    crossing_score: float | None
    lead_time_days: int | None
    seed: int
    n_simulations: int
    trajectory_length: int
    crossing_summary: str
    recommendation_status: str | None
    recommendation_option_ids: list[str]
    secondary_comparison: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["reference_point_date"] = self.reference_point_date.isoformat()
        if self.first_crossing_date:
            payload["first_crossing_date"] = self.first_crossing_date.isoformat()
        return payload


def run_backtest(config: BacktestConfig | None = None) -> BacktestResult:
    """Run the Hormuz 2026 PIT backtest; deterministic for fixed cache + config."""
    cfg = config or load_backtest_config()
    events = load_backtest_events(cfg)
    trajectory = build_pit_daily_scores(events, config=cfg)
    crossing = find_first_crossing(trajectory, cfg.risk_threshold)

    rec_status: str | None = None
    option_ids: list[str] = []
    secondary: SecondaryComparison | None = None

    if crossing is not None:
        _, _, rec = run_full_chain_pit(crossing.score_date, events, config=cfg)
        rec_status = rec.status.value
        option_ids = [o.option_id for o in rec.options]
        secondary = compare_recommendation_to_ground_truth(rec, config=cfg)
        lead = compute_lead_time_days(crossing.score_date, cfg.reference_point_date)
        status = "crossed"
        crossing_score = crossing.score
        crossing_date = crossing.score_date
    else:
        lead = None
        status = "no_crossing"
        crossing_score = None
        crossing_date = None

    sec_dict: dict[str, Any] = {}
    if secondary is not None:
        sec_dict = {
            "ground_truth_date": secondary.ground_truth_date.isoformat(),
            "ground_truth_description": secondary.ground_truth_description,
            "generated_option_ids": secondary.generated_option_ids,
            "match_assessment": secondary.match_assessment,
        }

    return BacktestResult(
        status=status,
        reference_point_date=cfg.reference_point_date,
        reference_point_label=cfg.reference_point_label,
        risk_threshold=cfg.risk_threshold,
        first_crossing_date=crossing_date,
        crossing_score=crossing_score,
        lead_time_days=lead,
        seed=cfg.seed,
        n_simulations=cfg.n_simulations,
        trajectory_length=len(trajectory),
        crossing_summary=crossing_summary(crossing, cfg.risk_threshold),
        recommendation_status=rec_status,
        recommendation_option_ids=option_ids,
        secondary_comparison=sec_dict,
    )
