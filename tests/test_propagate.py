"""Phase 2 supply shock propagation tests."""

from __future__ import annotations

from app.models.generated import Corridor
from app.simulation.graph_loader import load_network_graph
from app.simulation.propagate import (
    corridor_dependent_edges,
    corridor_dependent_flow,
    flow_lost_and_node_impacts,
    simulate_once,
)

ROOT_GRAPH = load_network_graph()


def test_corridor_dependent_edges_traverses_tagged_edges() -> None:
    edges = corridor_dependent_edges(ROOT_GRAPH.graph, Corridor.hormuz)
    assert len(edges) >= 5
    assert all(d["corridor_dependency"] == "HORMUZ" for _, _, d in edges)


def test_flow_lost_propagates_capacity_caps_to_refineries() -> None:
    flow_lost, node_lost = flow_lost_and_node_impacts(ROOT_GRAPH.graph, Corridor.hormuz)
    assert flow_lost == 3.0
    assert node_lost["refinery_jamnagar"] > 0
    assert node_lost["refinery_mumbai"] > 0
    jam_cap = ROOT_GRAPH.graph.nodes["refinery_jamnagar"]["capacity_mbpd"]
    assert node_lost["refinery_jamnagar"] <= jam_cap


def test_throughput_uses_propagated_refinery_losses_not_chokepoint_only() -> None:
    g = ROOT_GRAPH.graph
    duration = 30
    metrics = simulate_once(g, Corridor.hormuz, duration)
    _, node_lost = flow_lost_and_node_impacts(g, Corridor.hormuz)
    refinery_lost = sum(
        node_lost[n]
        for n, d in g.nodes(data=True)
        if d["node_type"] == "REFINERY"
    )
    total_ref_cap = sum(
        d["capacity_mbpd"] for n, d in g.nodes(data=True) if d["node_type"] == "REFINERY"
    )
    expected_throughput = (refinery_lost / total_ref_cap) * 100.0
    assert metrics.refinery_throughput_impact_pct == round(expected_throughput, 4)
    assert metrics.refinery_throughput_impact_pct < 100.0


def test_corridor_dependent_flow_matches_chokepoint_inbound() -> None:
    assert corridor_dependent_flow(ROOT_GRAPH.graph, Corridor.hormuz) == 3.0


def test_bab_propagation_reaches_refinery_despite_mixed_edge_tags() -> None:
    g = ROOT_GRAPH.graph
    flow_lost, node_lost = flow_lost_and_node_impacts(g, Corridor.bab_el_mandeb)
    assert flow_lost == 0.8
    assert node_lost["refinery_jamnagar"] > 0
    assert node_lost["refinery_jamnagar"] <= g.nodes["refinery_jamnagar"]["capacity_mbpd"]

    metrics = simulate_once(g, Corridor.bab_el_mandeb, duration_days=30)
    assert metrics.refinery_throughput_impact_pct > 0.0
    assert "refinery_jamnagar" in metrics.affected_downstream_nodes


def test_malacca_propagation_reaches_chennai_refinery() -> None:
    g = ROOT_GRAPH.graph
    flow_lost, node_lost = flow_lost_and_node_impacts(g, Corridor.malacca)
    assert flow_lost == 1.2
    assert node_lost["refinery_chennai"] > 0
    assert node_lost["refinery_chennai"] <= g.nodes["refinery_chennai"]["capacity_mbpd"]

    metrics = simulate_once(g, Corridor.malacca, duration_days=30)
    assert metrics.refinery_throughput_impact_pct > 0.0
    assert "refinery_chennai" in metrics.affected_downstream_nodes
