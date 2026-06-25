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
    find_peak_score,
    load_backtest_events,
    trajectory_summary,
)
from app.models.generated import Recommendation


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
    trajectory_peak: dict[str, Any]
    orchestrator_at_crossing: dict[str, Any] | None
    orchestrator_at_peak: dict[str, Any] | None
    pit_integrity: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["reference_point_date"] = self.reference_point_date.isoformat()
        payload["reference_date"] = self.reference_point_date.isoformat()
        if self.first_crossing_date:
            payload["first_crossing_date"] = self.first_crossing_date.isoformat()
            payload["first_threshold_crossing_date"] = self.first_crossing_date.isoformat()
        else:
            payload["first_threshold_crossing_date"] = None
        orchestrator = self.orchestrator_at_crossing or self.orchestrator_at_peak
        payload["orchestrator_summary"] = orchestrator
        return payload


def _orchestrator_payload(rec: Recommendation, integrity: dict[str, Any]) -> dict[str, Any]:
    return {
        "chain_date": integrity["as_of"],
        "status": rec.status.value,
        "option_ids": [o.option_id for o in rec.options],
        "pit_integrity": integrity,
    }


def run_backtest(config: BacktestConfig | None = None) -> BacktestResult:
    """Run the Hormuz 2026 PIT backtest; deterministic for fixed cache + config."""
    cfg = config or load_backtest_config()
    events = load_backtest_events(cfg)
    trajectory = build_pit_daily_scores(events, config=cfg)
    peak = find_peak_score(trajectory)
    crossing = find_first_crossing(trajectory, cfg.risk_threshold)

    rec_status: str | None = None
    option_ids: list[str] = []
    secondary: SecondaryComparison | None = None
    orchestrator_at_crossing: dict[str, Any] | None = None
    orchestrator_at_peak: dict[str, Any] | None = None
    pit_integrity: dict[str, Any] | None = None

    if crossing is not None:
        _, _, rec, integrity = run_full_chain_pit(
            crossing.score_date, events, config=cfg
        )
        orchestrator_at_crossing = _orchestrator_payload(rec, integrity)
        pit_integrity = integrity
        rec_status = rec.status.value
        option_ids = [o.option_id for o in rec.options]
        secondary = compare_recommendation_to_ground_truth(rec, config=cfg)
        lead = compute_lead_time_days(crossing.score_date, cfg.reference_point_date)
        status = "crossed"
        crossing_score = crossing.score
        crossing_date = crossing.score_date
    else:
        _, _, rec, integrity = run_full_chain_pit(peak.score_date, events, config=cfg)
        orchestrator_at_peak = _orchestrator_payload(rec, integrity)
        pit_integrity = integrity
        rec_status = rec.status.value
        option_ids = [o.option_id for o in rec.options]
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

    trajectory_peak = {
        **trajectory_summary(trajectory),
        "peak_date": peak.score_date.isoformat(),
        "peak_score": peak.score,
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
        trajectory_peak=trajectory_peak,
        orchestrator_at_crossing=orchestrator_at_crossing,
        orchestrator_at_peak=orchestrator_at_peak,
        pit_integrity=pit_integrity,
    )