"""Phase 1 pipeline acceptance tests."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest
from app.database import get_db_path, init_db
from app.models.generated import SignalEvent
from app.signals.extract import extract_signal
from app.signals.ingest_gdelt import load_backtest_cache
from app.signals.pipeline import run_pipeline

ROOT = Path(__file__).resolve().parent.parent
BACKTEST = ROOT / "data" / "samples" / "gdelt_hormuz_backtest.json"
SCRATCH = Path("/tmp/grok-goal-7dbdddf7e201/implementer")


def _fixed_ingested_at() -> datetime:
    return datetime(2026, 6, 23, 12, 0, 0, tzinfo=timezone.utc)


def _extract_all(rows: list[dict[str, str]]) -> tuple[list[SignalEvent], list[dict]]:
    accepted_events: list[SignalEvent] = []
    rejected_records: list[dict] = []
    ingested_at = _fixed_ingested_at()
    for row in rows:
        result = extract_signal(row, ingested_at=ingested_at)
        if result.status == "accepted" and result.event is not None:
            SignalEvent.model_validate(result.event.model_dump(mode="json"))
            accepted_events.append(result.event)
        else:
            rejected_records.append(
                {
                    "source_id": result.source_id,
                    "reason": result.reason,
                    "payload": result.payload,
                }
            )
    return accepted_events, rejected_records


@pytest.fixture()
def phase1_db(tmp_path, monkeypatch):
    db_file = tmp_path / "phase1.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:////{db_file}")
    monkeypatch.setenv("SETU_EXTRACTOR_MODE", "rules")
    init_db()
    return db_file


def test_extraction_rate_at_least_ninety_percent_with_determinism() -> None:
    os.environ["SETU_EXTRACTOR_MODE"] = "rules"
    rows = load_backtest_cache(BACKTEST)

    first_events, first_rejected = _extract_all(rows)
    second_events, second_rejected = _extract_all(rows)

    first_json = json.dumps(
        [e.model_dump(mode="json") for e in first_events], sort_keys=True
    )
    second_json = json.dumps(
        [e.model_dump(mode="json") for e in second_events], sort_keys=True
    )
    assert first_json == second_json

    rate = len(first_events) / len(rows)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    (SCRATCH / "extraction.log").write_text(
        json.dumps(
            {
                "total": len(rows),
                "accepted": len(first_events),
                "rejected": len(first_rejected),
                "rate": rate,
                "sample_accepted": [
                    e.model_dump(mode="json") for e in first_events[:3]
                ],
                "sample_rejected": first_rejected[:3],
                "deterministic": first_json == second_json,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    assert len(rows) >= 50
    assert rate >= 0.9


def test_pipeline_persists_events_and_scores(phase1_db) -> None:
    result = run_pipeline(source="cache", reset=True)
    assert result.stats.input_rows >= 50
    assert result.stats.risk_scores == 3
    assert len(result.events) > 0

    conn = sqlite3.connect(str(get_db_path()))
    try:
        event_count = conn.execute("SELECT COUNT(*) FROM signal_events").fetchone()[0]
        score_count = conn.execute("SELECT COUNT(*) FROM risk_scores").fetchone()[0]
        corridors = {
            row[0]
            for row in conn.execute("SELECT DISTINCT corridor FROM risk_scores").fetchall()
        }
    finally:
        conn.close()

    assert event_count > 0
    assert score_count >= 3
    assert {"HORMUZ", "BAB_EL_MANDEB", "MALACCA"} <= corridors
