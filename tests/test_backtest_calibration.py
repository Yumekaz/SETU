"""Baseline-only threshold calibration tests."""

from __future__ import annotations

from datetime import date

from app.backtest.calibration import calibrate_threshold
from app.backtest.config import load_backtest_config
from app.backtest.replay import load_backtest_events


def test_preincident_baseline_has_no_operational_threshold() -> None:
    config = load_backtest_config()
    result = calibrate_threshold(
        load_backtest_events(config),
        config=config,
        baseline_start=date(2026, 1, 15),
        baseline_end=date(2026, 1, 31),
        target_false_positive_rate=0.05,
    )

    assert result.status == "calibrated"
    assert result.sample_count == 17
    assert result.min_score == 0.0
    assert result.max_score == 0.4375
    assert result.calibrated_threshold == 0.437501
    assert result.lowest_zero_alert_threshold == 0.437501
    assert result.calibrated_threshold <= result.model_score_ceiling
