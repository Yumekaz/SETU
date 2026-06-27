"""Phase 2 graph and cascade simulation API routes."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, ValidationError

from app.database import get_db_path, init_db
from app.forecast.repository import list_risk_forecasts
from app.models.generated import Corridor
from app.signals.repository import list_risk_scores
from app.simulation.config import load_simulation_config
from app.simulation.corridors import (
    SUPPORTED_SIMULATION_CORRIDORS,
    UnsupportedSimulationCorridorError,
    require_simulatable_corridor,
)
from app.simulation.graph_loader import load_network_graph
from app.simulation.monte_carlo import default_n_simulations, run_cascade
from app.simulation.repository import insert_cascade_result, list_cascade_results
from app.simulation.validate import GraphValidationError, validate_network

router = APIRouter(prefix="/api", tags=["cascade"])


class CascadeSimulateRequest(BaseModel):
    corridor: Corridor
    seed: int | None = None
    n_simulations: int | None = Field(default=None, ge=1)


@router.get("/graph")
def get_graph() -> dict[str, Any]:
    try:
        network = load_network_graph()
        validate_network(network)
    except (
        json.JSONDecodeError,
        ValidationError,
        GraphValidationError,
        ValueError,
        KeyError,
        OSError,
    ) as exc:
        raise HTTPException(status_code=422, detail=f"graph load failed: {exc}") from exc
    return {
        "sources": network.sources,
        "nodes": [n.model_dump(mode="json") for n in network.nodes],
        "edges": [e.model_dump(mode="json") for e in network.edges],
    }


@router.post("/cascade/simulate")
def post_cascade_simulate(body: CascadeSimulateRequest) -> dict[str, Any]:
    init_db()
    try:
        require_simulatable_corridor(body.corridor)
    except UnsupportedSimulationCorridorError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    cfg = load_simulation_config()
    seed = body.seed if body.seed is not None else cfg.params.default_seed
    n = body.n_simulations or default_n_simulations(cfg)
    try:
        result = run_cascade(body.corridor, n_simulations=n, seed=seed)
    except UnsupportedSimulationCorridorError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    with sqlite3.connect(str(get_db_path())) as conn:
        insert_cascade_result(conn, result, seed=seed)
        conn.commit()

    return result.model_dump(mode="json")


@router.post("/cascade/simulate/from-risk")
def post_cascade_simulate_from_risk(
    seed: int | None = None,
    n_simulations: int | None = Query(default=None, ge=1),
) -> dict[str, Any]:
    scores = list_risk_scores(latest_only=True)
    if not scores:
        raise HTTPException(
            status_code=404,
            detail="no risk scores available; run Phase 1 pipeline first",
        )
    simulatable = [s for s in scores if s.corridor in SUPPORTED_SIMULATION_CORRIDORS]
    if not simulatable:
        raise HTTPException(
            status_code=422,
            detail=(
                "no simulatable corridor in risk scores; "
                "supported: HORMUZ, BAB_EL_MANDEB, MALACCA"
            ),
        )
    trigger = max(simulatable, key=lambda s: s.score)
    body = CascadeSimulateRequest(
        corridor=trigger.corridor,
        seed=seed,
        n_simulations=n_simulations,
    )
    payload = post_cascade_simulate(body)
    payload["trigger_risk_score"] = trigger.model_dump(mode="json")
    return payload


@router.get("/cascade/results")
def get_cascade_results(corridor: str | None = None) -> list[dict[str, Any]]:
    results = list_cascade_results(corridor=corridor, latest_only=False)
    return [r.model_dump(mode="json") for r in results]


@router.get("/cascade/results/latest")
def get_cascade_results_latest() -> list[dict[str, Any]]:
    results = list_cascade_results(latest_only=True)
    return [r.model_dump(mode="json") for r in results]


@router.post("/cascade/simulate/from-forecast")
def post_cascade_simulate_from_forecast(
    seed: int | None = None,
    n_simulations: int | None = Query(default=None, ge=1),
) -> dict[str, Any]:
    from app.forecast.inference import highest_risk_forecast

    init_db()
    forecasts = list_risk_forecasts(latest_only=True)
    if not forecasts:
        raise HTTPException(
            status_code=404,
            detail="no forecasts available; run POST /api/forecast/run first",
        )
    try:
        trigger = highest_risk_forecast(forecasts)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    body = CascadeSimulateRequest(
        corridor=trigger.corridor,
        seed=seed,
        n_simulations=n_simulations,
    )
    payload = post_cascade_simulate(body)
    payload["trigger_forecast"] = trigger.model_dump(mode="json")
    return payload
