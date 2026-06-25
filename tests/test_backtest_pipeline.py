"""Full backtest harness reproducibility tests."""

from __future__ import annotations

from dataclasses import replace

from app.backtest.config import load_backtest_config
from app.backtest.run import run_backtest


def test_run_backtest_reproducible_twice() -> None:
    first = run_backtest()
    second = run_backtest()
    assert first.status == second.status
    assert first.lead_time_days == second.lead_time_days
    assert first.first_crossing_date == second.first_crossing_date
    assert first.crossing_score == second.crossing_score
    assert first.crossing_summary == second.crossing_summary
    assert first.reference_point_date.isoformat() == "2026-03-11"
    assert first.risk_threshold == 0.35


def test_run_backtest_returns_required_keys() -> None:
    result = run_backtest().to_dict()
    for key in (
        "status",
        "reference_point_date",
        "reference_point_label",
        "risk_threshold",
        "lead_time_days",
        "first_crossing_date",
        "crossing_score",
        "recommendation_status",
        "recommendation_option_ids",
        "secondary_comparison",
        "seed",
        "n_simulations",
    ):
        assert key in result


def test_run_backtest_with_lower_threshold_invokes_chain() -> None:
    """Full chain executes when threshold is crossed (synthetic threshold only in test)."""
    cfg = replace(load_backtest_config(), risk_threshold=0.2, n_simulations=50)
    result = run_backtest(cfg)
    assert result.status == "crossed"
    assert result.first_crossing_date is not None
    assert result.crossing_score is not None
    assert result.crossing_score >= 0.2
    assert result.lead_time_days is not None
    assert result.lead_time_days >= 0
    assert result.recommendation_status is not None
    assert len(result.recommendation_option_ids) >= 1
    assert result.secondary_comparison.get("match_assessment")
