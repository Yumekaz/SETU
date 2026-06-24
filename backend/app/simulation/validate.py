"""Graph validation per SRS Section 12 edge cases."""

from __future__ import annotations

import networkx as nx

from app.simulation.graph_loader import NODE_TYPE_ORDER, NetworkGraph


class GraphValidationError(ValueError):
    pass


def validate_network(network: NetworkGraph) -> list[str]:
    """Validate graph; return list of warnings (e.g. disconnected paths)."""
    g = network.graph
    warnings: list[str] = []

    for node_id, data in g.nodes(data=True):
        if data.get("capacity_mbpd", 0) < 0:
            raise GraphValidationError(f"negative capacity on node {node_id}")

    for source, target, data in g.edges(data=True):
        flow = data.get("flow_mbpd", 0)
        if flow <= 0:
            raise GraphValidationError(f"non-positive flow on edge {source}->{target}: {flow}")
        src_type = g.nodes[source]["node_type"]
        tgt_type = g.nodes[target]["node_type"]
        if NODE_TYPE_ORDER[src_type] >= NODE_TYPE_ORDER[tgt_type]:
            raise GraphValidationError(
                f"invalid type order on edge {source}({src_type})->{target}({tgt_type})"
            )

    if not nx.is_directed_acyclic_graph(g):
        raise GraphValidationError("graph contains cycles")

    demand_nodes = [
        n for n, d in g.nodes(data=True) if d["node_type"] == "DEMAND_CENTER"
    ]
    production_nodes = [
        n for n, d in g.nodes(data=True) if d["node_type"] == "PRODUCTION_FIELD"
    ]

    for demand in demand_nodes:
        reachable = False
        for prod in production_nodes:
            if nx.has_path(g, prod, demand):
                reachable = True
                break
        if not reachable:
            raise GraphValidationError(f"demand center {demand} unreachable from production")

    for corridor in [n for n, d in g.nodes(data=True) if d["node_type"] == "CORRIDOR"]:
        has_demand_path = False
        for demand in demand_nodes:
            if nx.has_path(g, corridor, demand):
                has_demand_path = True
                break
        if not has_demand_path:
            warnings.append(f"corridor {corridor} has no path to any demand center")

    return warnings