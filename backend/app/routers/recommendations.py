"""Phase 4 procurement orchestrator API routes."""

from __future__ import annotations

import sqlite3
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.database import get_db_path, init_db
from app.forecast.repository import list_risk_forecasts
from app.models.generated import Corridor, Recommendation, Status
from app.orchestrator.config import load_orchestrator_config
from app.orchestrator.expire import expire_stale_pending
from app.orchestrator.hysteresis import should_supersede_pending
from app.orchestrator.options import trigger_risk_score
from app.orchestrator.orchestrate import run_orchestrator
from app.orchestrator.repository import (
    get_recommendation,
    insert_recommendation,
    latest_pending_for_corridor,
    list_recommendations,
    update_recommendation,
)
from app.routers.cascade import post_cascade_simulate_from_forecast
from app.simulation.graph_loader import load_network_graph
from app.simulation.repository import get_cascade_result, list_cascade_results

router = APIRouter(prefix="/api", tags=["recommendations"])


class OperatorNoteBody(BaseModel):
    operator_note: str = Field(..., min_length=1)


def _persist_recommendation(rec: Recommendation) -> dict[str, Any]:
    persisted = rec.model_copy(update={"recommendation_id": uuid4()})
    with sqlite3.connect(str(get_db_path())) as conn:
        insert_recommendation(conn, persisted)
        conn.commit()
    return persisted.model_dump(mode="json")


def _resolve_cascade(
    *,
    scenario_id: str | None = None,
) -> tuple[Any, Any | None]:
    if scenario_id:
        cascade = get_cascade_result(scenario_id)
        if cascade is None:
            raise HTTPException(status_code=404, detail=f"cascade not found: {scenario_id}")
        return cascade, None

    cascades = list_cascade_results(latest_only=True)
    if cascades:
        forecasts = list_risk_forecasts(latest_only=True)
        forecast = forecasts[0] if forecasts else None
        return cascades[0], forecast

    payload = post_cascade_simulate_from_forecast(seed=42, n_simulations=50)
    cascade = get_cascade_result(payload["scenario_id"])
    if cascade is None:
        raise HTTPException(status_code=500, detail="cascade simulation did not persist")
    forecast_payload = payload.get("trigger_forecast")
    return cascade, forecast_payload


@router.get("/recommendations")
def get_recommendations(
    corridor: Corridor | None = None,
    status: Status | None = None,
) -> list[dict[str, Any]]:
    init_db()
    cfg = load_orchestrator_config()
    with sqlite3.connect(str(get_db_path())) as conn:
        expire_stale_pending(conn, cfg)
        conn.commit()
    corridor_value = corridor.value if corridor is not None else None
    status_value = status.value if status is not None else None
    recs = list_recommendations(corridor=corridor_value, status=status_value, latest_only=False)
    return [r.model_dump(mode="json") for r in recs]


@router.get("/recommendations/latest")
def get_recommendations_latest() -> list[dict[str, Any]]:
    init_db()
    cfg = load_orchestrator_config()
    with sqlite3.connect(str(get_db_path())) as conn:
        expire_stale_pending(conn, cfg)
        conn.commit()
    recs = list_recommendations(latest_only=True)
    return [r.model_dump(mode="json") for r in recs]


@router.post("/recommendations/run")
def post_recommendations_run(
    force: bool = Query(default=False),
) -> dict[str, Any]:
    init_db()
    cfg = load_orchestrator_config()
    cascade, forecast_payload = _resolve_cascade()
    network = load_network_graph()

    from app.models.generated import RiskForecast

    forecast = (
        RiskForecast.model_validate(forecast_payload) if forecast_payload else None
    )
    new_risk = trigger_risk_score(cascade, cfg)
    pending = latest_pending_for_corridor(cascade.corridor.value)
    if not should_supersede_pending(new_risk, pending, cfg, force=force):
        prior = pending.options[0].risk_score if pending and pending.options else 0.0
        delta = abs(new_risk - prior)
        raise HTTPException(
            status_code=409,
            detail=(
                f"pending recommendation exists for {cascade.corridor.value}; "
                f"risk delta {delta:.4f} < hysteresis {cfg.hysteresis_risk_delta}"
            ),
        )

    rec = run_orchestrator(cascade, network, forecast=forecast, config=cfg)
    return _persist_recommendation(rec)


@router.post("/recommendations/generate/from-cascade")
def post_recommendations_from_cascade(
    scenario_id: UUID,
    force: bool = Query(default=False),
) -> dict[str, Any]:
    init_db()
    cfg = load_orchestrator_config()
    cascade = get_cascade_result(str(scenario_id))
    if cascade is None:
        raise HTTPException(status_code=404, detail=f"cascade not found: {scenario_id}")
    network = load_network_graph()
    new_risk = trigger_risk_score(cascade, cfg)
    pending = latest_pending_for_corridor(cascade.corridor.value)
    if not should_supersede_pending(new_risk, pending, cfg, force=force):
        raise HTTPException(
            status_code=409,
            detail="pending recommendation; risk delta below hysteresis threshold",
        )

    rec = run_orchestrator(cascade, network, config=cfg)
    return _persist_recommendation(rec)


@router.post("/recommendations/{recommendation_id}/approve")
def post_recommendation_approve(
    recommendation_id: UUID,
    body: OperatorNoteBody,
) -> dict[str, Any]:
    init_db()
    rec = get_recommendation(str(recommendation_id))
    if rec is None:
        raise HTTPException(status_code=404, detail="recommendation not found")
    if rec.status != Status.pending_approval:
        raise HTTPException(status_code=422, detail=f"cannot approve status {rec.status.value}")
    updated = rec.model_copy(
        update={"status": Status.approved, "operator_note": body.operator_note}
    )
    with sqlite3.connect(str(get_db_path())) as conn:
        update_recommendation(conn, updated)
        conn.commit()
    return updated.model_dump(mode="json")


@router.post("/recommendations/{recommendation_id}/reject")
def post_recommendation_reject(
    recommendation_id: UUID,
    body: OperatorNoteBody,
) -> dict[str, Any]:
    init_db()
    rec = get_recommendation(str(recommendation_id))
    if rec is None:
        raise HTTPException(status_code=404, detail="recommendation not found")
    if rec.status != Status.pending_approval:
        raise HTTPException(status_code=422, detail=f"cannot reject status {rec.status.value}")
    updated = rec.model_copy(
        update={"status": Status.rejected, "operator_note": body.operator_note}
    )
    with sqlite3.connect(str(get_db_path())) as conn:
        update_recommendation(conn, updated)
        conn.commit()
    return updated.model_dump(mode="json")
