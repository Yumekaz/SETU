"""Dynamic Global Maritime Router using NetworkX and Haversine distances.

Calculates real voyage distances, transit days, fuel costs, canal fees,
and war risk insurance surcharges across global shipping lanes.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Any

import networkx as nx

from app.models.generated import Corridor

logger = logging.getLogger(__name__)

# Standard constants for VLCC crude tankers (~300,000 DWT)
VLCC_SPEED_KNOTS = 12.0
VLCC_DAILY_FUEL_TONS = 80.0
BUNKER_FUEL_PRICE_USD_PER_TON = 450.0  # IFO380 proxy
DAILY_FUEL_COST_USD = VLCC_DAILY_FUEL_TONS * BUNKER_FUEL_PRICE_USD_PER_TON  # $36,000/day
SUEZ_CANAL_FEE_USD = 700000.0  # ~$700k for loaded VLCC
CARGO_VALUE_USD = 150_000_000.0  # ~2M barrels @ $75/bbl
BASE_WAR_RISK_RATE = 0.0005  # 0.05% base rate in high-risk zones


@dataclass(frozen=True)
class RouteResult:
    path: list[str]
    total_distance_nm: float
    total_transit_days: float
    total_fuel_cost_usd: float
    total_canal_fees_usd: float
    insurance_premium_pct: float
    total_cost_usd: float
    is_fallback: bool
    error: str | None = None


@dataclass(frozen=True)
class RouteComparison:
    normal: RouteResult
    alternative: RouteResult
    extra_days: float
    extra_cost_usd: float
    extra_distance_nm: float


def haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Great Circle distance in nautical miles between two lat/lon coordinates."""
    r_nm = 3440.065  # Earth radius in nautical miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r_nm * c


# Node definitions with real geographical coordinates
MARITIME_NODES: dict[str, dict[str, Any]] = {
    "persian_gulf": {"type": "SOURCE", "name": "Persian Gulf (Ras Tanura)", "lat": 26.65, "lon": 50.17},
    "hormuz": {"type": "CHOKEPOINT", "name": "Strait of Hormuz", "lat": 26.57, "lon": 56.25},
    "gulf_of_aden": {"type": "CHOKEPOINT", "name": "Bab-el-Mandeb / Gulf of Aden", "lat": 12.58, "lon": 43.33},
    "malacca": {"type": "CHOKEPOINT", "name": "Strait of Malacca", "lat": 1.27, "lon": 103.75},
    "suez_canal": {"type": "CANAL", "name": "Suez Canal", "lat": 30.46, "lon": 32.34},
    "cape_of_good_hope": {"type": "WAYPOINT", "name": "Cape of Good Hope", "lat": -34.36, "lon": 18.50},
    "jamnagar": {"type": "PORT", "name": "Jamnagar (Vadinar)", "lat": 22.47, "lon": 69.67},
    "mumbai": {"type": "PORT", "name": "Mumbai (JNPT)", "lat": 18.95, "lon": 72.95},
    "kochi": {"type": "PORT", "name": "Kochi (Cochin)", "lat": 9.97, "lon": 76.27},
    "chennai": {"type": "PORT", "name": "Chennai (Ennore)", "lat": 13.22, "lon": 80.32},
    "se_asia": {"type": "SOURCE", "name": "SE Asia (Brunei)", "lat": 4.93, "lon": 114.95},
    "arabian_sea": {"type": "WAYPOINT", "name": "Arabian Sea Transit", "lat": 15.00, "lon": 65.00},
    "red_sea_north": {"type": "WAYPOINT", "name": "North Red Sea", "lat": 27.50, "lon": 34.00},
    "mediterranean": {"type": "WAYPOINT", "name": "Mediterranean Sea", "lat": 35.00, "lon": 25.00},
    "atlantic_west_africa": {"type": "WAYPOINT", "name": "West Africa Atlantic", "lat": 5.00, "lon": -5.00},
    "mozambique_channel": {"type": "WAYPOINT", "name": "Mozambique Channel", "lat": -15.00, "lon": 42.00},
}

# Directed shipping edges: (source, target, corridor_dependency, canal_fee)
MARITIME_EDGES: list[tuple[str, str, str | None, float]] = [
    # Hormuz routes
    ("persian_gulf", "hormuz", "HORMUZ", 0.0),
    ("hormuz", "arabian_sea", "HORMUZ", 0.0),
    ("arabian_sea", "jamnagar", None, 0.0),
    ("arabian_sea", "mumbai", None, 0.0),
    ("arabian_sea", "kochi", None, 0.0),

    # Bab-el-Mandeb / Red Sea routes
    ("persian_gulf", "gulf_of_aden", "HORMUZ", 0.0),  # Exiting Persian Gulf requires Hormuz passage
    ("gulf_of_aden", "red_sea_north", "BAB_EL_MANDEB", 0.0),
    ("red_sea_north", "suez_canal", "BAB_EL_MANDEB", SUEZ_CANAL_FEE_USD),
    ("suez_canal", "mediterranean", None, 0.0),

    # Cape of Good Hope reroute (bypasses Hormuz & Bab-el-Mandeb)
    ("persian_gulf", "mozambique_channel", None, 0.0),
    ("mozambique_channel", "cape_of_good_hope", None, 0.0),
    ("cape_of_good_hope", "atlantic_west_africa", None, 0.0),
    ("atlantic_west_africa", "jamnagar", None, 0.0),
    ("atlantic_west_africa", "mumbai", None, 0.0),

    # Malacca routes
    ("se_asia", "malacca", "MALACCA", 0.0),
    ("malacca", "chennai", "MALACCA", 0.0),
    ("malacca", "kochi", "MALACCA", 0.0),

    # Inter-waypoint links for connectivity
    ("gulf_of_aden", "arabian_sea", None, 0.0),
    ("arabian_sea", "gulf_of_aden", None, 0.0),
    ("kochi", "chennai", None, 0.0),
]


def build_maritime_graph() -> nx.DiGraph:
    """Construct directed Graph with distance, transit time, and cost attributes."""
    g = nx.DiGraph()

    for node_id, data in MARITIME_NODES.items():
        g.add_node(node_id, **data)

    for src, tgt, dep, canal_fee in MARITIME_EDGES:
        if src not in MARITIME_NODES or tgt not in MARITIME_NODES:
            continue
        n1 = MARITIME_NODES[src]
        n2 = MARITIME_NODES[tgt]
        dist_nm = haversine_nm(n1["lat"], n1["lon"], n2["lat"], n2["lon"])
        transit_days = dist_nm / (VLCC_SPEED_KNOTS * 24.0)
        fuel_cost = transit_days * DAILY_FUEL_COST_USD

        g.add_edge(
            src,
            tgt,
            distance_nm=round(dist_nm, 2),
            transit_days=round(transit_days, 2),
            base_fuel_cost=round(fuel_cost, 2),
            canal_fee_usd=canal_fee,
            corridor_dependency=dep,
        )

    return g


def find_optimal_route(
    graph: nx.DiGraph,
    origin: str,
    destination: str,
    blocked_corridors: list[str] | list[Corridor] | None = None,
    risk_scores: dict[str, float] | None = None,
) -> RouteResult:
    """Compute optimal route taking into account blocked corridors and risk surcharges."""
    if origin == destination:
        return RouteResult(
            path=[origin],
            total_distance_nm=0.0,
            total_transit_days=0.0,
            total_fuel_cost_usd=0.0,
            total_canal_fees_usd=0.0,
            insurance_premium_pct=0.0,
            total_cost_usd=0.0,
            is_fallback=False,
        )

    if origin not in graph or destination not in graph:
        return RouteResult(
            path=[],
            total_distance_nm=0.0,
            total_transit_days=0.0,
            total_fuel_cost_usd=0.0,
            total_canal_fees_usd=0.0,
            insurance_premium_pct=0.0,
            total_cost_usd=0.0,
            is_fallback=False,
            error=f"Invalid origin '{origin}' or destination '{destination}'",
        )

    # Normalize blocked corridor strings
    blocked_set: set[str] = set()
    if blocked_corridors:
        for b in blocked_corridors:
            val = b.value if isinstance(b, Corridor) else str(b)
            blocked_set.add(val.upper())

    # Build filtered subgraph or weight map
    subgraph = graph.copy()
    edges_to_remove = []
    for u, v, d in subgraph.edges(data=True):
        dep = d.get("corridor_dependency")
        if dep and dep.upper() in blocked_set:
            edges_to_remove.append((u, v))

    subgraph.remove_edges_from(edges_to_remove)

    try:
        path = nx.dijkstra_path(subgraph, origin, destination, weight="transit_days")
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return RouteResult(
            path=[],
            total_distance_nm=0.0,
            total_transit_days=0.0,
            total_fuel_cost_usd=0.0,
            total_canal_fees_usd=0.0,
            insurance_premium_pct=0.0,
            total_cost_usd=0.0,
            is_fallback=bool(blocked_set),
            error="NO_FEASIBLE_ROUTE",
        )

    total_dist = 0.0
    total_days = 0.0
    total_fuel = 0.0
    total_canal = 0.0
    risk_surcharge = 0.0

    scores = risk_scores or {}

    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        edge_data = graph[u][v]
        total_dist += edge_data["distance_nm"]
        total_days += edge_data["transit_days"]
        total_fuel += edge_data["base_fuel_cost"]
        total_canal += edge_data["canal_fee_usd"]

        dep = edge_data.get("corridor_dependency")
        if dep and dep in scores:
            c_score = scores[dep]
            risk_surcharge += BASE_WAR_RISK_RATE * c_score * CARGO_VALUE_USD

    total_cost = total_fuel + total_canal + risk_surcharge
    insurance_pct = (risk_surcharge / CARGO_VALUE_USD) * 100.0 if CARGO_VALUE_USD > 0 else 0.0
    is_fallback = len(blocked_set) > 0

    return RouteResult(
        path=path,
        total_distance_nm=round(total_dist, 2),
        total_transit_days=round(total_days, 2),
        total_fuel_cost_usd=round(total_fuel, 2),
        total_canal_fees_usd=round(total_canal, 2),
        insurance_premium_pct=round(insurance_pct, 4),
        total_cost_usd=round(total_cost, 2),
        is_fallback=is_fallback,
    )


def compare_routes(
    origin: str,
    destination: str,
    blocked_corridors: list[str] | list[Corridor] | None = None,
    risk_scores: dict[str, float] | None = None,
) -> RouteComparison:
    """Compare normal path vs path with blocked corridors."""
    g = build_maritime_graph()
    normal = find_optimal_route(g, origin, destination, blocked_corridors=None, risk_scores=risk_scores)
    alt = find_optimal_route(g, origin, destination, blocked_corridors=blocked_corridors, risk_scores=risk_scores)

    extra_days = max(0.0, alt.total_transit_days - normal.total_transit_days)
    extra_cost = max(0.0, alt.total_cost_usd - normal.total_cost_usd)
    extra_dist = max(0.0, alt.total_distance_nm - normal.total_distance_nm)

    return RouteComparison(
        normal=normal,
        alternative=alt,
        extra_days=round(extra_days, 2),
        extra_cost_usd=round(extra_cost, 2),
        extra_distance_nm=round(extra_dist, 2),
    )
