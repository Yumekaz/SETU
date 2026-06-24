"""Supply shock propagation through the import/refining graph."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass

import networkx as nx

from app.models.generated import Corridor
from app.simulation.config import SimulationParams, load_simulation_config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SimulationMetrics:
    price_impact_pct: float
    refinery_throughput_impact_pct: float
    spr_days_required: float
    affected_downstream_nodes: list[str]
    shortfall_mbpd: float
    clipped: bool


def _clip(value: float, upper: float, label: str) -> tuple[float, bool]:
    if value > upper:
        logger.debug("clipping %s from %.2f to %.2f", label, value, upper)
        return upper, True
    return max(0.0, value), False


def _corridor_node_ids(g: nx.DiGraph, corridor: Corridor) -> list[str]:
    corridor_key = corridor.value
    return [
        n
        for n, d in g.nodes(data=True)
        if (
            d["node_type"] == "CORRIDOR"
            and corridor_key.replace("_", "") in n.upper().replace("_", "")
        )
    ]


def corridor_dependent_edges(g: nx.DiGraph, corridor: Corridor) -> list[tuple[str, str, dict]]:
    dep = corridor.value
    return [(u, v, d) for u, v, d in g.edges(data=True) if d.get("corridor_dependency") == dep]


def flow_lost_and_node_impacts(
    g: nx.DiGraph, corridor: Corridor
) -> tuple[float, dict[str, float]]:
    """
    Traverse corridor-dependent edges downstream from the chokepoint.

    Propagates supply shock with per-node capacity caps (Appendix B step 2 + 4).
    Returns chokepoint flow lost (mbpd) and per-node lost flow after capacity limits.
    """
    dep = corridor.value
    corridor_nodes = _corridor_node_ids(g, corridor)
    if not corridor_nodes:
        return 0.0, {}

    at_risk: dict[str, float] = {str(n): 0.0 for n in g.nodes}
    node_lost: dict[str, float] = {str(n): 0.0 for n in g.nodes}

    for cn in corridor_nodes:
        for _u, _v, data in g.in_edges(cn, data=True):
            if data.get("corridor_dependency") == dep:
                at_risk[cn] += float(data["flow_mbpd"])

    chokepoint_flow = sum(at_risk[cn] for cn in corridor_nodes)
    if chokepoint_flow <= 0:
        for cn in corridor_nodes:
            for _u, _v, data in g.out_edges(cn, data=True):
                if data.get("corridor_dependency") == dep:
                    at_risk[cn] += float(data["flow_mbpd"])
        chokepoint_flow = sum(at_risk[cn] for cn in corridor_nodes)

    reachable: set[str] = set()
    for cn in corridor_nodes:
        reachable.add(cn)
        reachable.update(nx.descendants(g, cn))

    for node in (n for n in nx.topological_sort(g) if n in reachable):
        inbound = at_risk.get(node, 0.0)
        if inbound <= 0:
            continue

        cap = float(g.nodes[node].get("capacity_mbpd") or 0.0)
        lost = min(inbound, cap) if cap > 0 else inbound
        node_lost[node] = lost

        # Downstream shock follows all edges in the reachable subgraph; edge tags
        # describe import-route dependency, not whether capacity loss propagates.
        out_edges = [
            (v, float(d["flow_mbpd"])) for _u, v, d in g.out_edges(node, data=True)
        ]
        if not out_edges:
            continue
        total_out = sum(flow for _, flow in out_edges)
        if total_out <= 0:
            continue
        for v, flow in out_edges:
            at_risk[v] = at_risk.get(v, 0.0) + lost * (flow / total_out)

    return chokepoint_flow, node_lost


def corridor_dependent_flow(g: nx.DiGraph, corridor: Corridor) -> float:
    """Chokepoint flow lost (mbpd) via dependent-edge traversal."""
    flow_lost, _ = flow_lost_and_node_impacts(g, corridor)
    return flow_lost


def affected_nodes_from_corridor(g: nx.DiGraph, corridor: Corridor) -> list[str]:
    corridor_nodes = _corridor_node_ids(g, corridor)
    affected: set[str] = set()
    for corridor_node in corridor_nodes:
        affected.add(corridor_node)
        affected.update(nx.descendants(g, corridor_node))
    return sorted(affected)


def simulate_once(
    g: nx.DiGraph,
    corridor: Corridor,
    duration_days: int,
    params: SimulationParams | None = None,
) -> SimulationMetrics:
    cfg = load_simulation_config()
    p = params or cfg.params

    flow_lost, node_lost = flow_lost_and_node_impacts(g, corridor)
    shortfall = flow_lost * (duration_days / p.duration_scale_days)

    total_demand = p.india_total_demand_mbpd
    price_raw = p.price_elasticity * math.log1p(shortfall / max(total_demand, 0.01))
    price_impact, clipped_price = _clip(price_raw, p.max_price_impact_pct, "price_impact_pct")

    refinery_nodes = [
        (n, float(d["capacity_mbpd"]))
        for n, d in g.nodes(data=True)
        if d["node_type"] == "REFINERY"
    ]
    if refinery_nodes:
        total_ref_cap = sum(cap for _, cap in refinery_nodes)
        refinery_lost = sum(node_lost.get(n, 0.0) for n, _ in refinery_nodes)
        refinery_shortfall = refinery_lost * (duration_days / p.duration_scale_days)
        throughput_raw = (refinery_shortfall / max(total_ref_cap, 0.01)) * 100.0
    else:
        throughput_raw = 0.0
    throughput_impact, clipped_tp = _clip(
        throughput_raw, p.max_throughput_impact_pct, "refinery_throughput_impact_pct"
    )

    spr_raw = shortfall / max(p.spr_draw_rate_mbpd, 0.01)
    spr_days, _ = _clip(spr_raw, 365.0, "spr_days_required")

    affected = affected_nodes_from_corridor(g, corridor)
    return SimulationMetrics(
        price_impact_pct=round(price_impact, 4),
        refinery_throughput_impact_pct=round(throughput_impact, 4),
        spr_days_required=round(spr_days, 4),
        affected_downstream_nodes=affected,
        shortfall_mbpd=round(shortfall, 4),
        clipped=clipped_price or clipped_tp,
    )
