"""Append-only SQLite persistence for recommendations."""

from __future__ import annotations

import json
import sqlite3

from app.database import get_db_path
from app.models.generated import Recommendation, Status


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(get_db_path()))
    conn.row_factory = sqlite3.Row
    return conn


def insert_recommendation(conn: sqlite3.Connection, rec: Recommendation) -> None:
    """Append a new recommendation row (never upsert).

    computed_at is always set explicitly so rows remain valid after legacy
    ALTER migrations that cannot attach a non-constant DEFAULT.
    """
    conn.execute(
        """
        INSERT INTO recommendations (
            recommendation_id, trigger_corridor, status,
            source_cascade_id, payload_json, computed_at
        ) VALUES (?, ?, ?, ?, ?, datetime('now'))
        """,
        (
            str(rec.recommendation_id),
            rec.trigger_corridor.value,
            rec.status.value,
            str(rec.source_cascade_id),
            json.dumps(rec.model_dump(mode="json")),
        ),
    )


def update_recommendation(conn: sqlite3.Connection, rec: Recommendation) -> None:
    """Update status/note on an existing row (HITL transitions only)."""
    conn.execute(
        """
        UPDATE recommendations
        SET status = ?, payload_json = ?
        WHERE recommendation_id = ?
        """,
        (
            rec.status.value,
            json.dumps(rec.model_dump(mode="json")),
            str(rec.recommendation_id),
        ),
    )


def get_recommendation(recommendation_id: str) -> Recommendation | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT payload_json FROM recommendations WHERE recommendation_id = ?",
            (recommendation_id,),
        ).fetchone()
    if row is None:
        return None
    return Recommendation.model_validate(json.loads(row["payload_json"]))


def list_recommendations(
    *,
    corridor: str | None = None,
    status: str | None = None,
    latest_only: bool = False,
) -> list[Recommendation]:
    with _connect() as conn:
        if latest_only:
            rows = conn.execute(
                """
                SELECT payload_json FROM recommendations AS r
                WHERE rowid = (
                    SELECT rowid FROM recommendations
                    WHERE trigger_corridor = r.trigger_corridor
                    ORDER BY datetime(computed_at) DESC, rowid DESC
                    LIMIT 1
                )
                ORDER BY trigger_corridor
                """
            ).fetchall()
        else:
            clauses: list[str] = []
            params: list[str] = []
            if corridor:
                clauses.append("trigger_corridor = ?")
                params.append(corridor)
            if status:
                clauses.append("status = ?")
                params.append(status)
            where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
            rows = conn.execute(
                f"SELECT payload_json FROM recommendations {where} ORDER BY computed_at DESC",
                params,
            ).fetchall()

    return [Recommendation.model_validate(json.loads(r["payload_json"])) for r in rows]


def latest_pending_for_corridor(corridor: str) -> Recommendation | None:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT payload_json FROM recommendations
            WHERE trigger_corridor = ? AND status = ?
            ORDER BY datetime(computed_at) DESC, rowid DESC
            LIMIT 1
            """,
            (corridor, Status.pending_approval.value),
        ).fetchone()
    if row is None:
        return None
    return Recommendation.model_validate(json.loads(row["payload_json"]))


def count_recommendations() -> int:
    with _connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM recommendations").fetchone()
    return int(row["n"]) if row else 0
