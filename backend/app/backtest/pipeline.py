"""Full downstream chain at a point-in-time crossing date."""

from __future__ import annotations

from datetime import date, datetime, timezone

from app.backtest.config import BacktestConfig
from app.backtest.integrity import assert_events_visible_at, filter_events_up_to, pit_diagnostics
from app.forecast.features import build_daily_features
from app.forecast.inference import forecast_corridor
from app.models.generated import CascadeResult, Recommendation, RiskForecast
from app.orchestrator.orchestrate import run_orchestrator
from app.simulation.graph_loader import load_network_graph
from app.simulation.monte_carlo import run_cascade


def run_full_chain_pit(
    chain_date: date,
    events: list,
    *,
    config: BacktestConfig,
) -> tuple[RiskForecast, CascadeResult, Recommendation, dict]:
    """Drive forecast → cascade → orchestrator using data visible through chain_date."""
    pit_events = filter_events_up_to(events, chain_date)
    assert_events_visible_at(pit_events, chain_date)
    integrity = pit_diagnostics(events, chain_date)

    features = build_daily_features(
        pit_events,
        start=config.window_start,
        end=chain_date,
    )
    forecast = forecast_corridor(config.corridor, features)
    network = load_network_graph()
    cascade = run_cascade(
        config.corridor,
        n_simulations=config.n_simulations,
        seed=config.seed,
        network=network,
    )
    generated_at = datetime(
        chain_date.year,
        chain_date.month,
        chain_date.day,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )
    rec = run_orchestrator(
        cascade,
        network,
        forecast=forecast,
        generated_at=generated_at,
    )
    return forecast, cascade, rec, integrity
