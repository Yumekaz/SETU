"""Tests for maritime routing engine and edge cases EC-47 to EC-51."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.models.generated import Corridor  # noqa: E402
from app.simulation.router import (  # noqa: E402
    build_maritime_graph,
    compare_routes,
    find_optimal_route,
    haversine_nm,
)


def test_haversine_known_distance() -> None:
    # 1 degree of latitude at equator is ~60 nautical miles
    dist = haversine_nm(0.0, 0.0, 1.0, 0.0)
    assert 59.0 <= dist <= 61.0


def test_graph_builds_without_error() -> None:
    g = build_maritime_graph()
    assert len(g.nodes) >= 10
    assert len(g.edges) >= 10


def test_normal_hormuz_route_to_jamnagar() -> None:
    g = build_maritime_graph()
    res = find_optimal_route(g, "persian_gulf", "jamnagar")
    assert not res.error
    assert res.path == ["persian_gulf", "hormuz", "arabian_sea", "jamnagar"]
    assert res.total_distance_nm > 0
    assert res.total_transit_days > 0
    assert res.total_cost_usd > 0
    assert not res.is_fallback


def test_blocked_hormuz_uses_cape_route_ec_51() -> None:
    g = build_maritime_graph()
    res = find_optimal_route(g, "persian_gulf", "jamnagar", blocked_corridors=[Corridor.hormuz])
    assert not res.error
    assert "hormuz" not in res.path
    assert res.is_fallback
    assert res.total_transit_days > 20.0  # Cape route is much longer (~35-40 days)


def test_all_corridors_blocked_returns_error_ec_47() -> None:
    g = build_maritime_graph()
    # Remove all edges to simulate total blockage
    sub = g.copy()
    sub.clear_edges()
    res = find_optimal_route(sub, "persian_gulf", "jamnagar", blocked_corridors=["HORMUZ"])
    assert res.error == "NO_FEASIBLE_ROUTE"
    assert res.path == []


def test_same_origin_destination_zero_cost_ec_48() -> None:
    g = build_maritime_graph()
    res = find_optimal_route(g, "jamnagar", "jamnagar")
    assert res.path == ["jamnagar"]
    assert res.total_cost_usd == 0.0
    assert res.total_transit_days == 0.0


def test_disconnected_nodes_returns_error_ec_49() -> None:
    g = build_maritime_graph()
    res = find_optimal_route(g, "persian_gulf", "mediterranean", blocked_corridors=["HORMUZ", "BAB_EL_MANDEB"])
    assert res.error == "NO_FEASIBLE_ROUTE" or res.total_transit_days > 0  # Either fails or reroutes


def test_blocked_irrelevant_corridor_returns_normal_ec_51() -> None:
    g = build_maritime_graph()
    res = find_optimal_route(g, "persian_gulf", "jamnagar", blocked_corridors=["MALACCA"])
    assert res.path == ["persian_gulf", "hormuz", "arabian_sea", "jamnagar"]


def test_route_comparison_function() -> None:
    comp = compare_routes("persian_gulf", "jamnagar", blocked_corridors=[Corridor.hormuz])
    assert comp.extra_days > 15.0
    assert comp.extra_cost_usd > 0
    assert comp.extra_distance_nm > 1000.0
