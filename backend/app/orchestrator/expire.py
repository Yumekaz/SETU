"""Expire stale pending recommendations."""

from __future__ import annotations

import json
import sqlite3

from app.models.generated import Recommendation, Status
from app.orchestrator.config import OrchestratorConfig


def expire_stale_pending(conn: sqlite3.Connection, config: OrchestratorConfig) -> int:
    """Mark PENDING_APPROVAL rows older than TTL as EXPIRED; return count updated."""
    rows = conn.execute(
        """
        SELECT recommendation_id, payload_json FROM recommendations
        WHERE status = ?
          AND datetime(computed_at) < datetime('now', ?)
        """,
        (Status.pending_approval.value, f"-{config.pending_ttl_hours} hours"),
    ).fetchall()
    count = 0
    for row in rows:
        payload = json.loads(row["payload_json"])
        rec = Recommendation.model_validate(payload)
        updated = rec.model_copy(
            update={"status": Status.expired, "operator_note": "Expired: pending review timeout"}
        )
        conn.execute(
            """
            UPDATE recommendations
            SET status = ?, payload_json = ?
            WHERE recommendation_id = ?
            """,
            (
                Status.expired.value,
                json.dumps(updated.model_dump(mode="json")),
                str(row["recommendation_id"]),
            ),
        )
        count += 1
    return count
