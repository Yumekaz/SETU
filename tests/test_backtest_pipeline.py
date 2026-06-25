"""Full backtest harness reproducibility and chain tests."""

from __future__ import annotations

from dataclasses import replace

from app.backtest.config import load_backtest_config
from app.backtest.pipeline import run_full_chain_pit
from app.backtest.replay import find_peak_score, load_backtest_events
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
        "reference_date",
        "reference_point_label",
        "risk_threshold",
        "lead_time_days",
        "first_crossing_date",
        "first_threshold_crossing_date",
        "crossing_score",
        "recommendation_status",
        "recommendation_option_ids",
        "secondary_comparison",
        "trajectory_peak",
        "orchestrator_at_peak",
        "orchestrator_summary",
        "pit_integrity",
        "seed",
        "n_simulations",
    ):
        assert key in result


def test_default_run_invokes_chain_at_peak_when_no_crossing() -> None:
    result = run_backtest()
    assert result.status == "no_crossing"
    assert result.lead_time_days is None
    assert result.orchestrator_at_peak is not None
    assert result.orchestrator_at_crossing is None
    assert result.recommendation_status is not None
    assert len(result.recommendation_option_ids) >= 1
    assert result.pit_integrity is not None
    assert result.pit_integrity["pit_ok"] is True
    assert result.trajectory_peak["peak_score"] == 0.25


def test_run_full_chain_pit_filters_future_events() -> None:
    cfg = load_backtest_config()
    events = load_backtest_events(cfg)
    from app.backtest.replay import build_pit_daily_scores

    peak = find_peak_score(build_pit_daily_scores(events, config=cfg))
    _, _, _, integrity = run_full_chain_pit(peak.score_date, events, config=cfg)
    assert integrity["pit_ok"] is True
    assert integrity["as_of"] == peak.score_date.isoformat()
    assert integrity["max_visible_event_date"] <= peak.score_date.isoformat()


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
