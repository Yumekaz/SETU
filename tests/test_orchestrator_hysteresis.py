"""Hysteresis guard tests."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.models.generated import Corridor, Option, Recommendation, Status
from app.orchestrator.config import OrchestratorConfig
from app.orchestrator.hysteresis import should_supersede_pending


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
