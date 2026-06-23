"""Phase 1 signal and risk score API routes."""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.signals.pipeline import run_pipeline
from app.signals.repository import get_signal_event, list_risk_scores, list_signal_events

router = APIRouter(prefix="/api", tags=["signals"])


class PipelineRunRequest(BaseModel):
    source: str = Field(default="cache", pattern="^cache$")


@router.get("/signals")
def get_signals(
    corridor: str | None = None,
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    min_confidence: float | None = None,
) -> list[dict[str, Any]]:
    events = list_signal_events(
        corridor=corridor,
        from_date=from_date,
        to_date=to_date,
        min_confidence=min_confidence,
    )
    return [event.model_dump(mode="json") for event in events]


@router.get("/signals/{event_id}")
def get_signal_by_id(event_id: str) -> dict[str, Any]:
    event = get_signal_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="signal event not found")
    return event.model_dump(mode="json")


@router.get("/risk-scores")
def get_risk_scores(corridor: str | None = None) -> list[dict[str, Any]]:
    scores = list_risk_scores(corridor=corridor, latest_only=False)
    return [score.model_dump(mode="json") for score in scores]


@router.get("/risk-scores/latest")
def get_latest_risk_scores() -> list[dict[str, Any]]:
    scores = list_risk_scores(latest_only=True)
    return [score.model_dump(mode="json") for score in scores]


@router.post("/pipeline/run")
def post_pipeline_run(body: PipelineRunRequest) -> dict[str, Any]:
    result = run_pipeline(source=body.source)
    return {
        "status": "ok",
        "source": body.source,
        "stats": {
            "input_rows": result.stats.input_rows,
            "accepted_events": result.stats.accepted_events,
            "rejected_events": result.stats.rejected_events,
            "dedup_dropped": result.stats.dedup_dropped,
            "risk_scores": result.stats.risk_scores,
        },
        "events": len(result.events),
        "scores": [score.model_dump(mode="json") for score in result.scores],
    }