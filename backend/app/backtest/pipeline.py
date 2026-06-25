"""Full downstream chain at a point-in-time crossing date."""

from __future__ import annotations

from datetime import date, datetime, timezone

from app.backtest.config import BacktestConfig
from app.forecast.features import build_daily_features
from app.forecast.inference import forecast_corridor
from app.models.generated import CascadeResult, Recommendation, RiskForecast
from app.orchestrator.orchestrate import run_orchestrator
from app.simulation.graph_loader import load_network_graph
from app.simulation.monte_carlo import run_cascade


def run_full_chain_pit(
    crossing_date: date,
    events: list,
    *,
    config: BacktestConfig,
) -> tuple[RiskForecast, CascadeResult, Recommendation]:
    """Drive forecast → cascade → orchestrator using data visible through crossing_date."""
    features = build_daily_features(
        events,
        start=config.window_start,
        end=crossing_date,
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
        crossing_date.year,
        crossing_date.month,
        crossing_date.day,
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
    return forecast, cascade, rec
