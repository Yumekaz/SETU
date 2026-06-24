"""Load and build NetworkX graph from cited network JSON."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import networkx as nx

from app.models.generated import GraphEdge, GraphNode
from app.simulation.config import default_graph_path

NODE_TYPE_ORDER = {
    "PRODUCTION_FIELD": 0,
    "CORRIDOR": 1,
    "PORT": 2,
    "REFINERY": 3,
    "DEMAND_CENTER": 4,
}


@dataclass(frozen=True)
class NetworkGraph:
    graph: nx.DiGraph
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    sources: list[dict]


def load_network_graph(path: Path | None = None) -> NetworkGraph:
    graph_path = path or default_graph_path()
    with graph_path.open(encoding="utf-8") as f:
        payload = json.load(f)

    nodes = [GraphNode.model_validate(n) for n in payload["nodes"]]
    edges = [GraphEdge.model_validate(e) for e in payload["edges"]]
    sources = list(payload.get("sources", []))

    g = nx.DiGraph()
    for node in nodes:
        g.add_node(
            node.node_id,
            node_type=node.node_type.value,
            capacity_mbpd=node.capacity_mbpd,
            name=node.name,
        )
    for edge in edges:
        g.add_edge(
            edge.source,
            edge.target,
            flow_mbpd=edge.flow_mbpd,
            corridor_dependency=edge.corridor_dependency.value,
            alt_route_penalty_days=edge.alt_route_penalty_days,
        )

    return NetworkGraph(graph=g, nodes=nodes, edges=edges, sources=sources)