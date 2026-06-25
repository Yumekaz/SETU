"""Backtest headline and secondary metrics."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date

from app.backtest.config import BacktestConfig
from app.backtest.replay import DailyScore
from app.models.generated import Recommendation


@dataclass(frozen=True)
class SecondaryComparison:
    ground_truth_date: date
    ground_truth_description: str
    generated_option_ids: list[str]
    match_assessment: str


def compute_lead_time_days(crossing_date: date, reference_date: date) -> int:
    return (reference_date - crossing_date).days


def load_timeline_row(config: BacktestConfig, on_date: date) -> dict[str, str] | None:
    with config.timeline_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("date") == on_date.isoformat():
                return row
    return None


def compare_recommendation_to_ground_truth(
    rec: Recommendation,
    *,
    config: BacktestConfig,
) -> SecondaryComparison:
    row = load_timeline_row(config, config.ground_truth_compare_date)
    description = row["description"] if row else "ground truth row missing"
    option_ids = [o.option_id for o in rec.options]
    lowered = description.lower()
    expected_tokens = []
    if "spr" in lowered or "reserve" in lowered:
        expected_tokens.append("spr")
    if "reroute" in lowered or "cape" in lowered or "route" in lowered:
        expected_tokens.append("reroute")
    if "mix" in lowered or "corridor" in lowered:
        expected_tokens.append("mix")

    matches = [
        oid
        for oid in option_ids
        if any(token in oid.lower() for token in expected_tokens)
    ]
    if matches:
        assessment = f"partial_match: generated {matches} align with ground truth themes"
    elif option_ids:
        assessment = "no_match: options generated but themes differ from ground truth row"
    else:
        assessment = "no_match: no feasible options at crossing"

    return SecondaryComparison(
        ground_truth_date=config.ground_truth_compare_date,
        ground_truth_description=description,
        generated_option_ids=option_ids,
        match_assessment=assessment,
    )


def crossing_summary(crossing: DailyScore | None, threshold: float) -> str:
    if crossing is None:
        return f"no_crossing: Hormuz score never reached threshold {threshold}"
    return (
        f"crossed on {crossing.score_date.isoformat()} "
        f"with score {crossing.score:.4f} (threshold {threshold})"
    )
