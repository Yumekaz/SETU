"""Phase 1 pipeline acceptance tests."""

from __future__ import annotations

import json
import os
import sqlite3
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


@pytest.fixture()
def phase1_db(tmp_path, monkeypatch):
    db_file = tmp_path / "phase1.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("SETU_EXTRACTOR_MODE", "rules")
    init_db()
    return db_file


def test_extraction_rate_at_least_ninety_percent() -> None:
    os.environ["SETU_EXTRACTOR_MODE"] = "rules"
    rows = load_backtest_cache(BACKTEST)
    accepted = 0
    rejected = 0
    for row in rows:
        result = extract_signal(row)
        if result.status == "accepted" and result.event is not None:
            SignalEvent.model_validate(result.event.model_dump(mode="json"))
            accepted += 1
        else:
            rejected += 1
    rate = accepted / len(rows)
    log = SCRATCH / "extraction.log"
    SCRATCH.mkdir(parents=True, exist_ok=True)
    log.write_text(
        json.dumps({"total": len(rows), "accepted": accepted, "rejected": rejected, "rate": rate}, indent=2),
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