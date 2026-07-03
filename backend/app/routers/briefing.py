"""FastAPI router for grounded intelligence briefings."""

from __future__ import annotations

import sqlite3
from fastapi import APIRouter, HTTPException, Query

from app.database import get_db_path, init_db
from app.models.generated import Corridor
from app.signals.briefing import generate_all_briefings, generate_briefing
from app.signals.repository import get_all_signal_events, get_latest_risk_scores

router = APIRouter(prefix="/api/briefing", tags=["briefing"])


@router.get("/latest")
def get_latest_briefing(corridor: Corridor = Query(Corridor.hormuz)) -> dict[str, object]:
    init_db()
    with sqlite3.connect(str(get_db_path())) as conn:
        scores = get_latest_risk_scores(conn)
        events = get_all_signal_events(conn)

    target_score = next((s for s in scores if s.corridor == corridor), None)
    if target_score is None:
        raise HTTPException(status_code=404, detail=f"No risk score found for corridor '{corridor.value}'")

    b = generate_briefing(target_score, events)
    return {
        "corridor": b.corridor,
        "risk_level": b.risk_level,
        "score": b.score,
        "trend": b.trend,
        "headline": b.headline,
        "contributing_factors": [
            {
                "event_type": f.event_type,
                "event_date": f.event_date,
                "contribution_pct": f.contribution_pct,
                "goldstein_scale": f.goldstein_scale,
                "source_url": f.source_url,
                "snippet": f.snippet,
            }
            for f in b.contributing_factors
        ],
        "recommended_posture": b.recommended_posture,
        "generated_at": b.generated_at,
    }


@router.get("/all")
def get_all_briefings_endpoint() -> list[dict[str, object]]:
    init_db()
    with sqlite3.connect(str(get_db_path())) as conn:
        scores = get_latest_risk_scores(conn)
        events = get_all_signal_events(conn)

    briefings = generate_all_briefings(scores, events)
    return [
        {
            "corridor": b.corridor,
            "risk_level": b.risk_level,
            "score": b.score,
            "trend": b.trend,
            "headline": b.headline,
            "contributing_factors": [
                {
                    "event_type": f.event_type,
                    "event_date": f.event_date,
                    "contribution_pct": f.contribution_pct,
                    "goldstein_scale": f.goldstein_scale,
                    "source_url": f.source_url,
                    "snippet": f.snippet,
                }
                for f in b.contributing_factors
            ],
            "recommended_posture": b.recommended_posture,
            "generated_at": b.generated_at,
        }
        for b in briefings
    ]
