"""Phase 2 network graph loader and validation tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from app.simulation.graph_loader import load_network_graph
from app.simulation.validate import GraphValidationError, validate_network

ROOT = Path(__file__).resolve().parent.parent
GRAPH_PATH = ROOT / "data" / "graph" / "india_crude_network.json"
SCRATCH = Path("/tmp/grok-goal-673d97933c7a/implementer")


def test_graph_loads_with_semantic_ids_and_citations() -> None:
    network = load_network_graph(GRAPH_PATH)
    node_ids = {n.node_id for n in network.nodes}

    assert "corridor_hormuz" in node_ids
    assert "port_mumbai" in node_ids
    assert "refinery_jamnagar" in node_ids
    assert "demand_north" in node_ids
    assert not any(nid.startswith("node_") for nid in node_ids)

    assert len(network.nodes) >= 10
    assert len(network.edges) >= 10
    assert network.sources
    assert any("EIA" in s.get("name", "") for s in network.sources)


def test_validate_network_passes_on_committed_graph() -> None:
    network = load_network_graph(GRAPH_PATH)
    warnings = validate_network(network)
    assert isinstance(warnings, list)


def test_validate_network_rejects_non_positive_flow() -> None:
    network = load_network_graph(GRAPH_PATH)
    edge = network.edges[0]
    network.graph[edge.source][edge.target]["flow_mbpd"] = 0.0

    with pytest.raises(GraphValidationError, match="non-positive flow"):
        validate_network(network)


def test_validate_network_rejects_unreachable_demand() -> None:
    network = load_network_graph(GRAPH_PATH)
    demand_nodes = [
        n for n, d in network.graph.nodes(data=True) if d["node_type"] == "DEMAND_CENTER"
    ]
    for edge in list(network.graph.in_edges(demand_nodes[0])):
        network.graph.remove_edge(*edge)

    with pytest.raises(GraphValidationError, match="unreachable"):
        validate_network(network)


def test_graph_validation_writes_scratch_evidence() -> None:
    """Verification plan step 2: graph load counts + citations to scratch."""
    network = load_network_graph(GRAPH_PATH)
    warnings = validate_network(network)
    payload = {
        "node_count": len(network.nodes),
        "edge_count": len(network.edges),
        "sources": network.sources,
        "citation_excerpts": [
            s.get("name", "") for s in network.sources if s.get("name")
        ],
        "warnings": warnings,
        "sample_node_ids": [n.node_id for n in network.nodes[:6]],
    }
    SCRATCH.mkdir(parents=True, exist_ok=True)
    (SCRATCH / "graph_load.txt").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    assert payload["node_count"] >= 10
    assert payload["edge_count"] >= 10
    assert any("EIA" in name for name in payload["citation_excerpts"])
