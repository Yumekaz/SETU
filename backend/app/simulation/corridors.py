"""Simulatable corridor allowlist for Phase 2 cascade."""

from __future__ import annotations

from app.models.generated import Corridor

SUPPORTED_SIMULATION_CORRIDORS: frozenset[Corridor] = frozenset(
    {
        Corridor.hormuz,
        Corridor.bab_el_mandeb,
        Corridor.malacca,
    }
)


class UnsupportedSimulationCorridorError(ValueError):
    def __init__(self, corridor: Corridor) -> None:
        self.corridor = corridor
        supported = ", ".join(sorted(c.value for c in SUPPORTED_SIMULATION_CORRIDORS))
        super().__init__(
            f"corridor {corridor.value} is not simulatable; supported: {supported}"
        )


def require_simulatable_corridor(corridor: Corridor) -> None:
    if corridor not in SUPPORTED_SIMULATION_CORRIDORS:
        raise UnsupportedSimulationCorridorError(corridor)


def supported_corridor_names() -> list[str]:
    return sorted(c.value for c in SUPPORTED_SIMULATION_CORRIDORS)
