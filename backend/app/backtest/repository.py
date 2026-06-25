"""Append-only persistence for backtest runs."""

from __future__ import annotations

import json
import sqlite3
from uuid import uuid4

from app.database import get_db_path


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(get_db_path()))
    conn.row_factory = sqlite3.Row
    return conn


def insert_backtest_run(conn: sqlite3.Connection, payload: dict) -> str:
    run_id = str(uuid4())
    conn.execute(
        """
        INSERT INTO backtest_runs (run_id, payload_json, computed_at)
        VALUES (?, ?, datetime('now'))
        """,
        (run_id, json.dumps(payload)),
    )
    return run_id


def latest_backtest_run() -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT payload_json FROM backtest_runs
            ORDER BY datetime(computed_at) DESC, rowid DESC
            LIMIT 1
            """
        ).fetchone()
    if row is None:
        return None
    return json.loads(row["payload_json"])


def count_backtest_runs() -> int:
    with _connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM backtest_runs").fetchone()
    return int(row["n"]) if row else 0
