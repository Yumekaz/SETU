"""Build Recommendation objects from cascade inputs."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import NAMESPACE_URL, UUID, uuid5

from app.models.generated import CascadeResult, Recommendation, RiskForecast, Status
from app.orchestrator.config import OrchestratorConfig, load_orchestrator_config
from app.orchestrator.options import generate_candidate_options, trigger_risk_score
from app.orchestrator.pareto import mark_pareto_optimal, sort_frontier
from app.simulation.graph_loader import NetworkGraph


def _freeze_now() -> datetime:
    return datetime(2026, 6, 23, 12, 0, 0, tzinfo=timezone.utc)


def _deterministic_recommendation_id(cascade: CascadeResult) -> UUID:
    return uuid5(NAMESPACE_URL, f"setu-recommendation:{cascade.scenario_id}")


def run_orchestrator(
    cascade: CascadeResult,
    network: NetworkGraph,
    *,
    forecast: RiskForecast | None = None,
    config: OrchestratorConfig | None = None,
    generated_at: datetime | None = None,
) -> Recommendation:
    """Produce a Recommendation with Pareto-marked options or NO_FEASIBLE_OPTION."""
    cfg = config or load_orchestrator_config()
    now = generated_at or _freeze_now()
    candidates = generate_candidate_options(cascade, network, forecast=forecast, config=cfg)

    rec_id = _deterministic_recommendation_id(cascade)
    base = {
        "recommendation_id": rec_id,
        "generated_at": now,
        "trigger_corridor": cascade.corridor,
        "source_cascade_id": cascade.scenario_id,
        "source_forecast_id": forecast.forecast_id if forecast else None,
        "inputs_as_of": now,
    }

    if not candidates:
        return Recommendation(
            **base,
            options=[],
            status=Status.no_feasible_option,
            operator_note=(
                "No feasible mitigation under current constraints: SPR draw exceeds reserve "
                f"cap ({cfg.spr_reserve_days_available:.0f} days) and/or no reroute path "
                f"for {cascade.corridor.value}."
            ),
        )

    marked = mark_pareto_optimal(candidates)
    ordered = sort_frontier(marked)
    return Recommendation(
        **base,
        options=ordered,
        status=Status.pending_approval,
        operator_note=None,
    )


def infeasible_recommendation(
    cascade: CascadeResult,
    *,
    config: OrchestratorConfig | None = None,
    note: str | None = None,
) -> Recommendation:
    """Explicit infeasible state for tests with constrained config."""
    cfg = config or load_orchestrator_config()
    now = _freeze_now()
    rec_id = _deterministic_recommendation_id(cascade)
    return Recommendation(
        recommendation_id=rec_id,
        generated_at=now,
        trigger_corridor=cascade.corridor,
        source_cascade_id=cascade.scenario_id,
        source_forecast_id=None,
        inputs_as_of=now,
        options=[],
        status=Status.no_feasible_option,
        operator_note=note
        or (
            f"No feasible mitigation: constraints block all options for {cascade.corridor.value} "
            f"(reserve cap {cfg.spr_reserve_days_available:.0f} days)."
        ),
    )


def recommendation_trigger_risk(rec: Recommendation, config: OrchestratorConfig) -> float:
    """Risk proxy from stored recommendation for hysteresis."""
    if rec.options:
        return min(o.risk_score for o in rec.options)
    return 0.0


__all__ = [
    "run_orchestrator",
    "infeasible_recommendation",
    "trigger_risk_score",
    "recommendation_trigger_risk",
]
