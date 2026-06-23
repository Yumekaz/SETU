"""SQLite persistence for SignalEvent and RiskScore."""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from typing import Any
from uuid import UUID

from app.database import get_db_path
from app.models.generated import Corridor, RiskScore, SignalEvent, Trend7d


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(get_db_path()))
    conn.row_factory = sqlite3.Row
    return conn


def insert_signal_event(conn: sqlite3.Connection, event: SignalEvent) -> None:
    payload = event.model_dump(mode="json")
    conn.execute(
        """
        INSERT OR REPLACE INTO signal_events (
            event_id, corridor, event_type, severity, goldstein_scale, confidence,
            event_date, ingested_at, source_url, raw_text_snippet, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(event.event_id),
            event.corridor.value,
            event.event_type.value,
            event.severity,
            event.goldstein_scale,
            event.confidence,
            event.event_date.isoformat(),
            event.ingested_at.isoformat().replace("+00:00", "Z"),
            str(event.source_url),
            event.raw_text_snippet,
            json.dumps(payload),
        ),
    )


def insert_risk_score(conn: sqlite3.Connection, score: RiskScore) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO risk_scores (
            corridor, score, score_date, contributing_event_ids, trend_7d, computed_at
        ) VALUES (?, ?, ?, ?, ?, datetime('now'))
        """,
        (
            score.corridor.value,
            score.score,
            score.score_date.isoformat(),
            json.dumps([str(event_id) for event_id in score.contributing_event_ids]),
            score.trend_7d.value,
        ),
    )


def insert_extraction_log(
    conn: sqlite3.Connection,
    *,
    source_id: str | None,
    status: str,
    reason: str | None,
    payload: dict[str, Any] | None,
) -> None:
    conn.execute(
        """
        INSERT INTO extraction_log (source_id, status, reason, payload_json)
        VALUES (?, ?, ?, ?)
        """,
        (source_id, status, reason, json.dumps(payload) if payload else None),
    )


def clear_pipeline_tables(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM signal_events")
    conn.execute("DELETE FROM risk_scores")
    conn.execute("DELETE FROM extraction_log")


def list_signal_events(
    *,
    corridor: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    min_confidence: float | None = None,
) -> list[SignalEvent]:
    clauses: list[str] = []
    params: list[Any] = []
    if corridor:
        clauses.append("corridor = ?")
        params.append(corridor)
    if from_date:
        clauses.append("event_date >= ?")
        params.append(from_date.isoformat())
    if to_date:
        clauses.append("event_date <= ?")
        params.append(to_date.isoformat())
    if min_confidence is not None:
        clauses.append("confidence >= ?")
        params.append(min_confidence)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"SELECT payload_json FROM signal_events {where} ORDER BY event_date DESC"

    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()

    events: list[SignalEvent] = []
    for row in rows:
        payload = json.loads(row["payload_json"])
        events.append(SignalEvent.model_validate(payload))
    return events


def get_signal_event(event_id: str) -> SignalEvent | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT payload_json FROM signal_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
    if row is None:
        return None
    return SignalEvent.model_validate(json.loads(row["payload_json"]))


def list_risk_scores(
    *,
    corridor: str | None = None,
    latest_only: bool = False,
) -> list[RiskScore]:
    with _connect() as conn:
        if latest_only:
            rows = conn.execute(
                """
                SELECT corridor, score, score_date, contributing_event_ids, trend_7d
                FROM risk_scores rs
                WHERE score_date = (
                    SELECT MAX(score_date) FROM risk_scores WHERE corridor = rs.corridor
                )
                ORDER BY corridor
                """
            ).fetchall()
        else:
            clauses: list[str] = []
            params: list[Any] = []
            if corridor:
                clauses.append("corridor = ?")
                params.append(corridor)
            where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
            rows = conn.execute(
                f"""
                SELECT corridor, score, score_date, contributing_event_ids, trend_7d
                FROM risk_scores {where}
                ORDER BY score_date DESC, corridor
                """,
                params,
            ).fetchall()

    results: list[RiskScore] = []
    for row in rows:
        results.append(
            RiskScore(
                corridor=Corridor(row["corridor"]),
                score=row["score"],
                score_date=date.fromisoformat(row["score_date"]),
                contributing_event_ids=[UUID(value) for value in json.loads(row["contributing_event_ids"])],
                trend_7d=Trend7d(row["trend_7d"]),
            )
        )
    return results