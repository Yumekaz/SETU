"""Hysteresis guard tests."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.models.generated import Corridor, Option, Recommendation, Status
from app.orchestrator.config import OrchestratorConfig, load_orchestrator_config
from app.orchestrator.hysteresis import should_supersede_pending
from app.orchestrator.options import trigger_risk_score
from app.orchestrator.orchestrate import recommendation_trigger_risk, run_orchestrator
from app.simulation.graph_loader import load_network_graph

ROOT = Path(__file__).resolve().parent.parent


def _pending_rec(risk: float) -> Recommendation:
    return Recommendation(
        recommendation_id=uuid4(),
        generated_at=datetime(2026, 6, 23, 12, 0, 0, tzinfo=timezone.utc),
        trigger_corridor=Corridor.hormuz,
        source_cascade_id=uuid4(),
        source_forecast_id=None,
        inputs_as_of=datetime(2026, 6, 23, 12, 0, 0, tzinfo=timezone.utc),
        options=[
            Option(
                option_id="opt1",
                description="test",
                cost_score=0.3,
                time_score=0.3,
                risk_score=risk,
                is_pareto_optimal=True,
            )
        ],
        status=Status.pending_approval,
        operator_note=None,
    )


def test_blocks_small_risk_delta() -> None:
    cfg = OrchestratorConfig(
        spr_reserve_days_available=90.0,
        max_penalty_days_cap=30.0,
        max_price_impact_cap_pct=50.0,
        max_throughput_impact_cap_pct=100.0,
        spr_unit_cost_proxy=0.35,
        mix_shift_cost_proxy=0.45,
        hysteresis_risk_delta=0.05,
        pending_ttl_hours=24,
    )
    pending = _pending_rec(0.20)
    assert not should_supersede_pending(0.22, pending, cfg)


def test_allows_large_risk_delta() -> None:
    cfg = OrchestratorConfig(
        spr_reserve_days_available=90.0,
        max_penalty_days_cap=30.0,
        max_price_impact_cap_pct=50.0,
        max_throughput_impact_cap_pct=100.0,
        spr_unit_cost_proxy=0.35,
        mix_shift_cost_proxy=0.45,
        hysteresis_risk_delta=0.05,
        pending_ttl_hours=24,
    )
    pending = _pending_rec(0.20)
    assert should_supersede_pending(0.30, pending, cfg)


def test_force_bypasses_hysteresis() -> None:
    cfg = OrchestratorConfig(
        spr_reserve_days_available=90.0,
        max_penalty_days_cap=30.0,
        max_price_impact_cap_pct=50.0,
        max_throughput_impact_cap_pct=100.0,
        spr_unit_cost_proxy=0.35,
        mix_shift_cost_proxy=0.45,
        hysteresis_risk_delta=0.05,
        pending_ttl_hours=24,
    )
    pending = _pending_rec(0.20)
    assert should_supersede_pending(0.21, pending, cfg, force=True)


def test_trigger_risk_matches_stored_recommendation_min_option_risk() -> None:
    """New-run and pending risk proxies use the same min option risk_score."""
    from app.models.generated import CascadeResult

    rows = json.loads((ROOT / "data/fixtures/cascade_results.json").read_text())
    cascade = CascadeResult.model_validate(rows[0])
    network = load_network_graph()
    cfg = load_orchestrator_config()
    rec = run_orchestrator(cascade, network, config=cfg)
    new_risk = trigger_risk_score(cascade, network, cfg)
    prior_risk = recommendation_trigger_risk(rec, cfg)
    assert new_risk == prior_risk
    assert new_risk == min(o.risk_score for o in rec.options)
