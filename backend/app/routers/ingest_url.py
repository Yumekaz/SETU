"""FastAPI router for live URL intelligence ingestion."""

from __future__ import annotations

import hashlib
import sqlite3

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.database import get_db_path, init_db
from app.signals.article_extractor import extract_article_metadata
from app.signals.config import load_config
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
    data_origin: str = "LIVE_WEB"
    source_domain: str | None = None
    article_title: str | None = None
    published_at: str | None = None
    scraped_at: str | None = None
    confidence: float | None = None
    goldstein_scale: float | None = None
    evidence_terms: list[str] = Field(default_factory=list)


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

    # Step 2: Derive auditable signal metadata from the article itself.
    metadata = extract_article_metadata(
        title=scraped.title,
        content_text=scraped.content_text,
        published_at_iso=scraped.published_at_iso,
        config=load_config(),
    )
    if metadata is None:
        return IngestUrlResponse(
            status="rejected",
            rejection_reason="No supported corridor and risk-event evidence found in article text",
            source_url=req.url,
            source_domain=scraped.domain,
            article_title=scraped.title,
            published_at=scraped.published_at_iso,
            scraped_at=scraped.scraped_at_iso,
        )

    stable_source_id = hashlib.sha256(req.url.encode("utf-8")).hexdigest()[:24]
    synthetic_row = {
        "GLOBALEVENTID": f"url_{stable_source_id}",
        "SQLDATE": metadata.event_date.strftime("%Y%m%d"),
        "EventCode": metadata.cameo_code,
        "EventTypeHint": metadata.event_type,
        "SeverityHint": str(metadata.severity),
        "ConfidenceHint": str(metadata.confidence),
        "EventDateHint": metadata.event_date.isoformat(),
        "GoldsteinScale": str(metadata.goldstein_scale),
        "ActionGeo_FullName": f"{scraped.title} {scraped.content_text[:1000]}",
        "Actor1Name": scraped.domain,
        "Actor2Name": metadata.corridor,
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
        source_domain=scraped.domain,
        article_title=scraped.title,
        published_at=scraped.published_at_iso,
        scraped_at=scraped.scraped_at_iso,
        confidence=res.event.confidence,
        goldstein_scale=res.event.goldstein_scale,
        evidence_terms=list(metadata.evidence_terms),
    )
