"""FastAPI router for maritime pathfinding and route comparisons."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from app.models.generated import Corridor
from app.simulation.router import (
    MARITIME_NODES,
    build_maritime_graph,
    compare_routes,
    find_optimal_route,
)

router = APIRouter(prefix="/api/route", tags=["route"])

CORRIDOR_ENDPOINTS: dict[Corridor, tuple[str, str]] = {
    Corridor.hormuz: ("persian_gulf", "jamnagar"),
    Corridor.bab_el_mandeb: ("persian_gulf", "mediterranean"),
    Corridor.malacca: ("se_asia", "kochi"),
    Corridor.other: ("persian_gulf", "jamnagar"),
}


class RouteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    origin: str = Field("persian_gulf", description="Origin node ID")
    destination: str = Field("jamnagar", description="Destination node ID")
    blocked_corridors: list[Corridor] = Field(default_factory=list)
    risk_scores: dict[str, float] | None = None


@router.post("/find")
def find_route(req: RouteRequest) -> dict[str, object]:
    g = build_maritime_graph()
    res = find_optimal_route(
        g,
        origin=req.origin,
        destination=req.destination,
        blocked_corridors=req.blocked_corridors,
        risk_scores=req.risk_scores,
    )
    if res.error:
        raise HTTPException(status_code=422, detail=res.error)
    return {
        "path": res.path,
        "total_distance_nm": res.total_distance_nm,
        "total_transit_days": res.total_transit_days,
        "total_fuel_cost_usd": res.total_fuel_cost_usd,
        "total_canal_fees_usd": res.total_canal_fees_usd,
        "insurance_premium_pct": res.insurance_premium_pct,
        "total_cost_usd": res.total_cost_usd,
        "is_fallback": res.is_fallback,
    }


@router.get("/compare")
def compare_corridor_route(
    corridor: Corridor = Query(Corridor.hormuz),
    origin: str | None = Query(None),
    destination: str | None = Query(None),
) -> dict[str, object]:
    default_origin, default_destination = CORRIDOR_ENDPOINTS[corridor]
    resolved_origin = origin or default_origin
    resolved_destination = destination or default_destination
    comp = compare_routes(
        origin=resolved_origin,
        destination=resolved_destination,
        blocked_corridors=[corridor],
    )
    return {
        "corridor": corridor.value,
        "origin": resolved_origin,
        "destination": resolved_destination,
        "normal": {
            "path": comp.normal.path,
            "distance_nm": comp.normal.total_distance_nm,
            "transit_days": comp.normal.total_transit_days,
            "cost_usd": comp.normal.total_cost_usd,
        },
        "alternative": {
            "path": comp.alternative.path,
            "distance_nm": comp.alternative.total_distance_nm,
            "transit_days": comp.alternative.total_transit_days,
            "cost_usd": comp.alternative.total_cost_usd,
            "error": comp.alternative.error,
        },
        "comparison": {
            "extra_days": comp.extra_days,
            "extra_cost_usd": comp.extra_cost_usd,
            "extra_distance_nm": comp.extra_distance_nm,
        },
    }


@router.get("/network")
def get_maritime_network() -> dict[str, object]:
    """Return nodes and edges of the maritime network for map rendering."""
    g = build_maritime_graph()
    nodes = [
        {
            "id": nid,
            "name": data["name"],
            "type": data["type"],
            "lat": data["lat"],
            "lon": data["lon"],
        }
        for nid, data in MARITIME_NODES.items()
    ]
    edges = [
        {
            "source": u,
            "target": v,
            "distance_nm": d["distance_nm"],
            "transit_days": d["transit_days"],
            "corridor_dependency": d.get("corridor_dependency"),
        }
        for u, v, d in g.edges(data=True)
    ]
    return {"nodes": nodes, "edges": edges}
