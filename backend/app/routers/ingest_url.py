"""FastAPI router for live URL intelligence ingestion."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.database import get_db_path, init_db
from app.signals.extract import extract_signal
from app.signals.repository import (
    insert_extraction_log,
    insert_risk_score,
    insert_signal_event,
    list_signal_events,
)
from app.signals.score import build_risk_scores
from app.signals.scraper import scrape_url

router = APIRouter(prefix="/api/signals", tags=["signals"])


class IngestUrlRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str = Field(..., description="Public news article URL to scrape and analyze")


class IngestUrlResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str  # "accepted" | "rejected"
    event_id: str | None = None
    corridor: str | None = None
    event_type: str | None = None
    severity: float | None = None
    risk_score_after: float | None = None
    rejection_reason: str | None = None
    source_url: str


@router.post("/ingest-url", response_model=IngestUrlResponse)
def ingest_live_url(req: IngestUrlRequest) -> IngestUrlResponse:
    init_db()

    # Step 1: Scrape article text
    scraped = scrape_url(req.url)
    if scraped.rejection_reason:
        return IngestUrlResponse(
            status="rejected",
            rejection_reason=scraped.rejection_reason,
            source_url=req.url,
        )

    # Step 2: Convert scraped text into synthetic GDELT row structure for extraction pipeline
    synthetic_row = {
        "GLOBALEVENTID": f"url_{hash(req.url) & 0xffffffff}",
        "SQLDATE": datetime.now(timezone.utc).strftime("%Y%m%d"),
        "EventCode": "190",  # Military / conflict root default for scraped security intelligence
        "GoldsteinScale": "-5.0",  # Moderate negative tone default
        "ActionGeo_FullName": scraped.title or "Geopolitical News Article",
        "Actor1Name": scraped.domain,
        "Actor2Name": "Maritime Security",
        "SOURCEURL": req.url,
        "raw_text_snippet": scraped.content_text[:500],
    }

    # Step 3: Extract signal
    res = extract_signal(synthetic_row)

    with sqlite3.connect(str(get_db_path())) as conn:
        insert_extraction_log(
            conn,
            source_id=res.source_id,
            status=res.status,
            reason=res.reason,
            payload=res.payload,
        )

        if res.status != "accepted" or res.event is None:
            return IngestUrlResponse(
                status="rejected",
                rejection_reason=res.reason or "Extraction filter rejected event",
                source_url=req.url,
            )

        # Step 4: Persist event
        insert_signal_event(conn, res.event)

        # Step 5: Recalculate risk score for the corridor
        all_events = list_signal_events(conn=conn)
        new_scores = build_risk_scores(all_events, score_date=res.event.event_date)
        after_score = None
        for s in new_scores:
            insert_risk_score(conn, s)
            if s.corridor == res.event.corridor:
                after_score = s.score

        conn.commit()

    return IngestUrlResponse(
        status="accepted",
        event_id=str(res.event.event_id),
        corridor=res.event.corridor.value,
        event_type=res.event.event_type.value,
        severity=res.event.severity,
        risk_score_after=after_score,
        source_url=req.url,
    )
