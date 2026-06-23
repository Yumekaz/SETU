"""Orchestrate ingest → extract → dedup → score → persist (offline cache mode)."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from app.database import get_db_path, init_db
from app.models.generated import RiskScore, SignalEvent
from app.signals.dedup import deduplicate_events
from app.signals.extract import extract_signal
from app.signals.ingest_gdelt import load_backtest_cache
from app.signals.repository import (
    clear_pipeline_tables,
    insert_extraction_log,
    insert_risk_score,
    insert_signal_event,
)
from app.signals.score import build_risk_scores


@dataclass
class PipelineStats:
    input_rows: int
    accepted_events: int
    rejected_events: int
    dedup_dropped: int
    risk_scores: int


@dataclass
class PipelineResult:
    events: list[SignalEvent]
    scores: list[RiskScore]
    stats: PipelineStats


def _fixed_ingested_at() -> datetime:
    return datetime(2026, 6, 23, 12, 0, 0, tzinfo=timezone.utc)


def run_pipeline(
    *,
    source: str = "cache",
    cache_path: Path | None = None,
    reset: bool = True,
    score_date: date | None = None,
) -> PipelineResult:
    if source != "cache":
        raise ValueError("Phase 1 supports source='cache' only (offline-first)")

    init_db()
    rows = load_backtest_cache(cache_path)

    accepted: list[SignalEvent] = []
    rejected = 0

    with sqlite3.connect(str(get_db_path())) as conn:
        if reset:
            clear_pipeline_tables(conn)

        ingested_at = _fixed_ingested_at()
        for row in rows:
            result = extract_signal(row, ingested_at=ingested_at)
            insert_extraction_log(
                conn,
                source_id=result.source_id,
                status=result.status,
                reason=result.reason,
                payload=result.payload,
            )
            if result.status == "accepted" and result.event is not None:
                accepted.append(result.event)
            else:
                rejected += 1

        kept, dropped = deduplicate_events(accepted)
        for event in kept:
            insert_signal_event(conn, event)

        as_of = score_date or max((event.event_date for event in kept), default=date(2026, 6, 23))
        prior_scores = {}
        week_ago = as_of.fromordinal(as_of.toordinal() - 7)
        prior = build_risk_scores(kept, score_date=week_ago)
        prior_scores = {score.corridor: score.score for score in prior}
        scores = build_risk_scores(kept, score_date=as_of, prior_scores=prior_scores)
        for score in scores:
            insert_risk_score(conn, score)

        conn.commit()

    return PipelineResult(
        events=kept,
        scores=scores,
        stats=PipelineStats(
            input_rows=len(rows),
            accepted_events=len(accepted),
            rejected_events=rejected,
            dedup_dropped=len(dropped),
            risk_scores=len(scores),
        ),
    )
