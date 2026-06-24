"""Phase 2 Monte Carlo cascade engine tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import pytest

from app.models.generated import CascadeResult, Corridor
from app.simulation.corridors import UnsupportedSimulationCorridorError
from app.simulation.graph_loader import load_network_graph
from app.simulation.monte_carlo import run_cascade

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = Path("/tmp/grok-goal-673d97933c7a/implementer")


def _bands_ordered(result: CascadeResult) -> None:
    for band in (
        result.price_impact_pct,
        result.refinery_throughput_impact_pct,
        result.spr_days_required,
    ):
        assert band.p10 <= band.p50 <= band.p90


def test_run_cascade_returns_valid_ordered_bands() -> None:
    result = run_cascade(Corridor.hormuz, n_simulations=100, seed=42)
    CascadeResult.model_validate(result.model_dump(mode="json"))
    _bands_ordered(result)
    assert result.affected_downstream_nodes
    assert "corridor_hormuz" in result.affected_downstream_nodes


def test_run_cascade_is_deterministic_for_identical_inputs() -> None:
    kwargs = {
        "corridor": Corridor.hormuz,
        "n_simulations": 200,
        "seed": 42,
        "network": load_network_graph(),
    }
    first = run_cascade(**kwargs)
    second = run_cascade(**kwargs)
    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_run_cascade_rejects_other_corridor() -> None:
    with pytest.raises(UnsupportedSimulationCorridorError, match="OTHER"):
        run_cascade(Corridor.other, n_simulations=10, seed=42)


def test_hormuz_p50_price_is_directionally_consistent_with_timeline() -> None:
    result = run_cascade(Corridor.hormuz, n_simulations=200, seed=42)
    p50 = result.price_impact_pct.p50
    assert p50 > 0.0
    assert p50 < 25.0

    SCRATCH.mkdir(parents=True, exist_ok=True)
    (SCRATCH / "cascade_sim.log").write_text(
        json.dumps(
            {
                "corridor": "HORMUZ",
                "seed": 42,
                "n_simulations": 200,
                "result": result.model_dump(mode="json"),
                "brent_anchor_pct": 8.8,
                "directional_note": "positive p50 within order of magnitude of ~8.8% Brent move",
            },
            indent=2,
        ),
        encoding="utf-8",
    )