"""Orchestrator option generation and infeasible path tests."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import networkx as nx
from app.models.generated import CascadeResult, Corridor, PercentileBand, Status
from app.orchestrator.config import OrchestratorConfig
from app.orchestrator.options import generate_candidate_options
from app.orchestrator.orchestrate import run_orchestrator
from app.orchestrator.pareto import mark_pareto_optimal
from app.simulation.graph_loader import NetworkGraph, load_network_graph

ROOT = Path(__file__).resolve().parent.parent


def _load_cascade(index: int = 0) -> CascadeResult:
    rows = json.loads((ROOT / "data/fixtures/cascade_results.json").read_text())
    return CascadeResult.model_validate(rows[index])


def _tight_config() -> OrchestratorConfig:
    return OrchestratorConfig(
        spr_reserve_days_available=1.0,
        max_penalty_days_cap=30.0,
        max_price_impact_cap_pct=50.0,
        max_throughput_impact_cap_pct=100.0,
        spr_unit_cost_proxy=0.35,
        mix_shift_cost_proxy=0.45,
        hysteresis_risk_delta=0.05,
        pending_ttl_hours=24,
    )


def test_hormuz_generates_three_option_types() -> None:
    cascade = _load_cascade(0)
    network = load_network_graph()
    cfg = _tight_config()
    cfg = OrchestratorConfig(
        spr_reserve_days_available=90.0,
        max_penalty_days_cap=cfg.max_penalty_days_cap,
        max_price_impact_cap_pct=cfg.max_price_impact_cap_pct,
        max_throughput_impact_cap_pct=cfg.max_throughput_impact_cap_pct,
        spr_unit_cost_proxy=cfg.spr_unit_cost_proxy,
        mix_shift_cost_proxy=cfg.mix_shift_cost_proxy,
        hysteresis_risk_delta=cfg.hysteresis_risk_delta,
        pending_ttl_hours=cfg.pending_ttl_hours,
    )
    options = generate_candidate_options(cascade, network, config=cfg)
    assert len(options) == 3
    ids = {o.option_id for o in options}
    assert f"reroute_{cascade.corridor.value.lower()}" in ids
    assert f"spr_draw_{cascade.corridor.value.lower()}" in ids
    assert f"mix_shift_{cascade.corridor.value.lower()}" in ids
    for opt in options:
        assert 0.0 <= opt.cost_score <= 1.0
        assert 0.0 <= opt.time_score <= 1.0
        assert 0.0 <= opt.risk_score <= 1.0


def test_bab_scenario_has_pareto_flags() -> None:
    cascade = _load_cascade(1)
    network = load_network_graph()
    cfg = _tight_config()
    cfg = OrchestratorConfig(
        spr_reserve_days_available=90.0,
        max_penalty_days_cap=cfg.max_penalty_days_cap,
        max_price_impact_cap_pct=cfg.max_price_impact_cap_pct,
        max_throughput_impact_cap_pct=cfg.max_throughput_impact_cap_pct,
        spr_unit_cost_proxy=cfg.spr_unit_cost_proxy,
        mix_shift_cost_proxy=cfg.mix_shift_cost_proxy,
        hysteresis_risk_delta=cfg.hysteresis_risk_delta,
        pending_ttl_hours=cfg.pending_ttl_hours,
    )
    options = generate_candidate_options(cascade, network, config=cfg)
    marked = mark_pareto_optimal(options)
    assert any(o.is_pareto_optimal for o in marked)


def test_malacca_run_orchestrator_pending() -> None:
    cascade = _load_cascade(2)
    network = load_network_graph()
    rec = run_orchestrator(cascade, network)
    assert rec.status == Status.pending_approval
    assert rec.source_cascade_id == cascade.scenario_id
    assert rec.inputs_as_of is not None
    assert len(rec.options) >= 2


def test_infeasible_when_no_options_pass_constraints() -> None:
    cascade = CascadeResult(
        scenario_id=uuid4(),
        corridor=Corridor.hormuz,
        disruption_duration_days=90,
        n_simulations=50,
        price_impact_pct=PercentileBand(p10=40.0, p50=45.0, p90=50.0),
        refinery_throughput_impact_pct=PercentileBand(p10=80.0, p50=90.0, p90=100.0),
        spr_days_required=PercentileBand(p10=80.0, p50=95.0, p90=100.0),
        affected_downstream_nodes=[],
    )
    empty_network = NetworkGraph(graph=nx.DiGraph(), nodes=[], edges=[], sources=[])
    cfg = _tight_config()
    rec = run_orchestrator(cascade, empty_network, config=cfg)
    assert rec.status == Status.no_feasible_option
    assert rec.options == []
    assert rec.operator_note is not None
    assert "No feasible mitigation" in rec.operator_note
