"""Deterministic candidate option generation from cascade + graph."""

from __future__ import annotations

from dataclasses import dataclass

from app.models.generated import CascadeResult, Corridor, Option, RiskForecast
from app.orchestrator.config import OrchestratorConfig
from app.simulation.corridors import SUPPORTED_SIMULATION_CORRIDORS
from app.simulation.graph_loader import NetworkGraph


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _normalize(value: float, cap: float) -> float:
    if cap <= 0:
        return 0.0
    return _clamp01(value / cap)


@dataclass(frozen=True)
class _Scores:
    cost: float
    time: float
    risk: float


def _max_alt_penalty_days(network: NetworkGraph, corridor: Corridor) -> float:
    corridor_key = corridor.value
    penalties = [
        float(edge.alt_route_penalty_days)
        for edge in network.edges
        if edge.corridor_dependency.value == corridor_key and edge.alt_route_penalty_days > 0
    ]
    return max(penalties) if penalties else 0.0


def _flow_through_corridor(network: NetworkGraph, corridor: Corridor) -> float:
    corridor_key = corridor.value
    return sum(
        float(edge.flow_mbpd)
        for edge in network.edges
        if edge.corridor_dependency.value == corridor_key
    )


def _reroute_option(
    cascade: CascadeResult,
    network: NetworkGraph,
    config: OrchestratorConfig,
) -> Option | None:
    penalty = _max_alt_penalty_days(network, cascade.corridor)
    if penalty <= 0:
        return None
    flow = _flow_through_corridor(network, cascade.corridor)
    price_p50 = cascade.price_impact_pct.p50
    scores = _Scores(
        cost=_normalize(penalty * flow * 0.1, config.max_penalty_days_cap * 3.0),
        time=_normalize(penalty, config.max_penalty_days_cap),
        risk=_normalize(price_p50, config.max_price_impact_cap_pct),
    )
    return Option(
        option_id=f"reroute_{cascade.corridor.value.lower()}",
        description=(
            f"Reroute via alternate corridor (max {penalty:.0f}d penalty) "
            f"for {cascade.corridor.value} disruption"
        ),
        cost_score=round(scores.cost, 4),
        time_score=round(scores.time, 4),
        risk_score=round(scores.risk, 4),
        is_pareto_optimal=False,
    )


def _spr_option(cascade: CascadeResult, config: OrchestratorConfig) -> Option | None:
    spr_days = cascade.spr_days_required.p50
    if spr_days > config.spr_reserve_days_available:
        return None
    throughput_p50 = cascade.refinery_throughput_impact_pct.p50
    scores = _Scores(
        cost=_normalize(spr_days * config.spr_unit_cost_proxy, 1.0),
        time=_normalize(spr_days, config.spr_reserve_days_available),
        risk=_normalize(throughput_p50, config.max_throughput_impact_cap_pct),
    )
    return Option(
        option_id=f"spr_draw_{cascade.corridor.value.lower()}",
        description=(
            f"Draw strategic reserves ({spr_days:.1f} days required, "
            f"{config.spr_reserve_days_available:.0f} days available)"
        ),
        cost_score=round(scores.cost, 4),
        time_score=round(scores.time, 4),
        risk_score=round(scores.risk, 4),
        is_pareto_optimal=False,
    )


def _mix_shift_option(
    cascade: CascadeResult,
    network: NetworkGraph,
    config: OrchestratorConfig,
) -> Option | None:
    others = sorted(
        (c for c in SUPPORTED_SIMULATION_CORRIDORS if c != cascade.corridor),
        key=lambda c: c.value,
    )
    if not others:
        return None
    alt_penalties = [
        _max_alt_penalty_days(network, c) for c in others if _max_alt_penalty_days(network, c) > 0
    ]
    if not alt_penalties:
        return None
    avg_penalty = sum(alt_penalties) / len(alt_penalties)
    price_p50 = cascade.price_impact_pct.p50
    scores = _Scores(
        cost=_normalize(avg_penalty * config.mix_shift_cost_proxy, config.max_penalty_days_cap),
        time=_normalize(avg_penalty * 0.6, config.max_penalty_days_cap),
        risk=_normalize(price_p50 * 0.7, config.max_price_impact_cap_pct),
    )
    alt_names = ", ".join(c.value for c in others)
    return Option(
        option_id=f"mix_shift_{cascade.corridor.value.lower()}",
        description=(
            f"Shift supplier/corridor mix toward {alt_names} "
            f"(avg alt penalty {avg_penalty:.0f}d)"
        ),
        cost_score=round(scores.cost, 4),
        time_score=round(scores.time, 4),
        risk_score=round(scores.risk, 4),
        is_pareto_optimal=False,
    )


def generate_candidate_options(
    cascade: CascadeResult,
    network: NetworkGraph,
    *,
    forecast: RiskForecast | None = None,
    config: OrchestratorConfig,
) -> list[Option]:
    """Enumerate feasible reroute, SPR, and corridor-mix options."""
    del forecast  # reserved for future risk-score blending; provenance only today
    candidates: list[Option] = []
    for opt in (
        _reroute_option(cascade, network, config),
        _spr_option(cascade, config),
        _mix_shift_option(cascade, network, config),
    ):
        if opt is not None:
            candidates.append(opt)
    return candidates


def trigger_risk_score(
    cascade: CascadeResult,
    network: NetworkGraph,
    config: OrchestratorConfig,
) -> float:
    """Risk proxy for hysteresis; matches min option risk_score on the same inputs."""
    options = generate_candidate_options(cascade, network, config=config)
    if options:
        return min(o.risk_score for o in options)
    return 0.0
