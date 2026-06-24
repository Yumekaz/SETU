"""Simulation configuration loaders."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_GRAPH_PATH = ROOT / "data" / "graph" / "india_crude_network.json"
DEFAULT_DIST_PATH = ROOT / "data" / "config" / "corridor_distributions.yaml"


@dataclass(frozen=True)
class TriangularDistribution:
    min_days: int
    mode_days: int
    max_days: int
    analogue: str


@dataclass(frozen=True)
class SimulationParams:
    default_n_simulations: int
    ci_n_simulations: int
    default_seed: int
    price_elasticity: float
    max_price_impact_pct: float
    max_throughput_impact_pct: float
    india_total_demand_mbpd: float
    spr_draw_rate_mbpd: float
    duration_scale_days: int


@dataclass(frozen=True)
class SimulationConfig:
    distributions: dict[str, TriangularDistribution]
    params: SimulationParams


def load_simulation_config(path: Path | None = None) -> SimulationConfig:
    config_path = Path(os.getenv("SETU_DISTRIBUTIONS_PATH", str(path or DEFAULT_DIST_PATH)))
    with config_path.open(encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f)

    distributions: dict[str, TriangularDistribution] = {}
    for corridor, spec in raw["distributions"].items():
        distributions[corridor] = TriangularDistribution(
            min_days=int(spec["min_days"]),
            mode_days=int(spec["mode_days"]),
            max_days=int(spec["max_days"]),
            analogue=str(spec.get("analogue", "")),
        )

    p = raw["simulation"]
    params = SimulationParams(
        default_n_simulations=int(p["default_n_simulations"]),
        ci_n_simulations=int(p.get("ci_n_simulations", 500)),
        default_seed=int(p["default_seed"]),
        price_elasticity=float(p["price_elasticity"]),
        max_price_impact_pct=float(p["max_price_impact_pct"]),
        max_throughput_impact_pct=float(p["max_throughput_impact_pct"]),
        india_total_demand_mbpd=float(p["india_total_demand_mbpd"]),
        spr_draw_rate_mbpd=float(p["spr_draw_rate_mbpd"]),
        duration_scale_days=int(p["duration_scale_days"]),
    )
    return SimulationConfig(distributions=distributions, params=params)


def default_graph_path() -> Path:
    return Path(os.getenv("SETU_GRAPH_PATH", str(DEFAULT_GRAPH_PATH)))