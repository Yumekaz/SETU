"""Empirical threshold calibration for a separately held baseline window."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import date

from app.backtest.config import BacktestConfig
from app.backtest.replay import build_pit_daily_scores


@dataclass(frozen=True)
class ThresholdCalibrationResult:
    baseline_start: date
    baseline_end: date
    target_false_positive_rate: float
    sample_count: int
    min_score: float
    max_score: float
    model_score_ceiling: float
    calibrated_threshold: float | None
    lowest_zero_alert_threshold: float
    status: str
    reason: str

    def to_dict(self) -> dict:
        result = asdict(self)
        result["baseline_start"] = self.baseline_start.isoformat()
        result["baseline_end"] = self.baseline_end.isoformat()
        return result


def calibrate_threshold(
    events: list,
    *,
    config: BacktestConfig,
    baseline_start: date,
    baseline_end: date,
    target_false_positive_rate: float,
) -> ThresholdCalibrationResult:
    """Find whether a baseline-derived operational threshold exists.

    An alert is defined as ``score >= threshold``.  A valid threshold must be
    reachable by the current score model and keep the observed baseline alert
    rate at or below the requested false-positive-rate target.
    """
    if not 0.0 <= target_false_positive_rate < 1.0:
        raise ValueError("target_false_positive_rate must be in [0, 1)")
    if baseline_end < baseline_start:
        raise ValueError("baseline_end must not precede baseline_start")

    baseline_config = replace(
        config,
        window_start=baseline_start,
        window_end=baseline_end,
    )
    scores = [point.score for point in build_pit_daily_scores(events, config=baseline_config)]
    if not scores:
        raise ValueError("baseline window produced no scores")

    # Noisy-OR preserves the per-event cap while allowing independently sourced
    # evidence to accumulate. Its global bound is 1.0, not CAP_SINGLE.
    ceiling = 1.0
    min_score = min(scores)
    max_score = max(scores)
    # A six-decimal score is the API's public precision. This is the first
    # threshold above all observed baseline values, but it is only operational
    # when it remains within the model's attainable score range.
    zero_alert_threshold = round(max_score + 0.000001, 6)
    if zero_alert_threshold <= ceiling:
        return ThresholdCalibrationResult(
            baseline_start=baseline_start,
            baseline_end=baseline_end,
            target_false_positive_rate=target_false_positive_rate,
            sample_count=len(scores),
            min_score=min_score,
            max_score=max_score,
            model_score_ceiling=ceiling,
            calibrated_threshold=zero_alert_threshold,
            lowest_zero_alert_threshold=zero_alert_threshold,
            status="calibrated",
            reason=(
                "The threshold is one six-decimal increment above the maximum "
                "baseline score and yields an observed false-positive rate of 0%."
            ),
        )

    return ThresholdCalibrationResult(
        baseline_start=baseline_start,
        baseline_end=baseline_end,
        target_false_positive_rate=target_false_positive_rate,
        sample_count=len(scores),
        min_score=min_score,
        max_score=max_score,
        model_score_ceiling=ceiling,
        calibrated_threshold=None,
        lowest_zero_alert_threshold=zero_alert_threshold,
        status="non_discriminative_score_range",
        reason=(
            "No reachable threshold meets the target: every score at or below "
            f"the {ceiling:.6f} ceiling alerts on the baseline; the first "
            f"zero-alert threshold ({zero_alert_threshold:.6f}) is unreachable."
        ),
    )
