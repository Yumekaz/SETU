"""Monte Carlo cascade engine."""

from __future__ import annotations

import os
import uuid
from typing import Iterable

import numpy as np

from app.models.generated import CascadeResult, Corridor, PercentileBand
from app.simulation.config import SimulationConfig, load_simulation_config
from app.simulation.corridors import require_simulatable_corridor
from app.simulation.distributions import sample_duration
from app.simulation.graph_loader import NetworkGraph, load_network_graph
from app.simulation.propagate import SimulationMetrics, simulate_once
from app.simulation.validate import validate_network


def _percentile_band(values: Iterable[float]) -> PercentileBand:
    arr = np.array(list(values), dtype=float)
    p10, p50, p90 = np.percentile(arr, [10, 50, 90])
    return PercentileBand(
        p10=round(float(p10), 4),
        p50=round(float(p50), 4),
        p90=round(float(p90), 4),
    )


def _scenario_uuid(corridor: Corridor, seed: int, n_simulations: int) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"setu-cascade:{corridor.value}:{seed}:{n_simulations}")


def default_n_simulations(config: SimulationConfig | None = None) -> int:
    cfg = config or load_simulation_config()
    env = os.getenv("SETU_MC_N_SIMULATIONS", "").strip()
    if env:
        return int(env)
    ci = os.getenv("CI", "").lower() in {"1", "true", "yes"}
    return cfg.params.ci_n_simulations if ci else cfg.params.default_n_simulations


def run_cascade(
    corridor: Corridor,
    *,
    n_simulations: int | None = None,
    seed: int | None = None,
    network: NetworkGraph | None = None,
    config: SimulationConfig | None = None,
) -> CascadeResult:
    require_simulatable_corridor(corridor)
    cfg = config or load_simulation_config()
    net = network or load_network_graph()
    validate_network(net)

    n = n_simulations or default_n_simulations(cfg)
    rng_seed = seed if seed is not None else cfg.params.default_seed
    rng = np.random.default_rng(rng_seed)

    durations: list[int] = []
    price_draws: list[float] = []
    throughput_draws: list[float] = []
    spr_draws: list[float] = []
    affected_union: set[str] = set()

    for _ in range(n):
        duration = sample_duration(corridor, rng, cfg)
        metrics: SimulationMetrics = simulate_once(net.graph, corridor, duration, cfg.params)
        durations.append(duration)
        price_draws.append(metrics.price_impact_pct)
        throughput_draws.append(metrics.refinery_throughput_impact_pct)
        spr_draws.append(metrics.spr_days_required)
        affected_union.update(metrics.affected_downstream_nodes)

    return CascadeResult(
        scenario_id=_scenario_uuid(corridor, rng_seed, n),
        corridor=corridor,
        disruption_duration_days=int(np.median(durations)),
        n_simulations=n,
        price_impact_pct=_percentile_band(price_draws),
        refinery_throughput_impact_pct=_percentile_band(throughput_draws),
        spr_days_required=_percentile_band(spr_draws),
        affected_downstream_nodes=sorted(affected_union),
    )
