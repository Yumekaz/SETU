"""Corridor disruption duration sampling."""

from __future__ import annotations

import numpy as np

from app.models.generated import Corridor
from app.simulation.config import SimulationConfig, TriangularDistribution, load_simulation_config
from app.simulation.corridors import require_simulatable_corridor


def sample_duration(
    corridor: Corridor | str,
    rng: np.random.Generator,
    config: SimulationConfig | None = None,
) -> int:
    corridor_enum = corridor if isinstance(corridor, Corridor) else Corridor(corridor)
    require_simulatable_corridor(corridor_enum)
    cfg = config or load_simulation_config()
    key = corridor_enum.value
    dist = cfg.distributions[key]
    value = rng.triangular(dist.min_days, dist.mode_days, dist.max_days)
    return max(1, int(round(value)))


def get_distribution(corridor: Corridor | str, config: SimulationConfig | None = None) -> TriangularDistribution:
    corridor_enum = corridor if isinstance(corridor, Corridor) else Corridor(corridor)
    require_simulatable_corridor(corridor_enum)
    cfg = config or load_simulation_config()
    return cfg.distributions[corridor_enum.value]