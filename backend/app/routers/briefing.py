"""FastAPI router for grounded intelligence briefings."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.database import init_db
from app.models.generated import Corridor, RiskScore
from app.signals.briefing import generate_all_briefings, generate_briefing
from app.signals.repository import list_risk_scores, list_signal_events

router = APIRouter(prefix="/api/briefing", tags=["briefing"])


@router.get("/latest")
def get_latest_briefing(corridor: Corridor = Query(Corridor.hormuz)) -> dict[str, object]:
    init_db()
    scores = list_risk_scores(latest_only=True)
    events = list_signal_events()

    target_score = next((s for s in scores if s.corridor == corridor), None)
    if target_score is None:
        from datetime import date

        from app.models.generated import Trend7d
        target_score = RiskScore(
            corridor=corridor,
            score=0.0,
            score_date=date.today(),
            contributing_event_ids=[],
            trend_7d=Trend7d.stable,
        )

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
    scores = list_risk_scores(latest_only=True)
    events = list_signal_events()

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
