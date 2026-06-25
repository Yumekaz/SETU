"""SQLite database initialization for SETU."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"
DEFAULT_DB_PATH = DATA_DIR / "setu.db"


def get_db_path() -> Path:
    url = os.getenv("DATABASE_URL", "sqlite:///data/setu.db")
    if url.startswith("sqlite:////"):
        # sqlite:////absolute/path — four slashes after the scheme
        return Path(url[len("sqlite://") :])
    if url.startswith("sqlite:///"):
        # sqlite:///relative/path — resolve under repo root (e.g. data/setu.db)
        return ROOT / url[len("sqlite:///") :]
    return DEFAULT_DB_PATH


def init_db() -> None:
    """Create data directory and initialize SQLite schema."""
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS signal_events (
                event_id TEXT PRIMARY KEY,
                corridor TEXT NOT NULL,
                event_type TEXT NOT NULL,
                severity REAL NOT NULL,
                goldstein_scale REAL NOT NULL,
                confidence REAL NOT NULL,
                event_date TEXT NOT NULL,
                ingested_at TEXT NOT NULL,
                source_url TEXT NOT NULL,
                raw_text_snippet TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS risk_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                corridor TEXT NOT NULL,
                score REAL NOT NULL,
                score_date TEXT NOT NULL,
                contributing_event_ids TEXT NOT NULL,
                trend_7d TEXT NOT NULL,
                computed_at TEXT DEFAULT (datetime('now')),
                UNIQUE(corridor, score_date)
            );

            CREATE TABLE IF NOT EXISTS extraction_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT,
                status TEXT NOT NULL,
                reason TEXT,
                payload_json TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS cascade_results (
                scenario_id TEXT PRIMARY KEY,
                corridor TEXT NOT NULL,
                disruption_duration_days INTEGER NOT NULL,
                n_simulations INTEGER NOT NULL,
                price_impact_pct TEXT NOT NULL,
                refinery_throughput_impact_pct TEXT NOT NULL,
                spr_days_required TEXT NOT NULL,
                affected_downstream_nodes TEXT NOT NULL,
                seed INTEGER NOT NULL,
                payload_json TEXT NOT NULL,
                computed_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS risk_forecasts (
                forecast_id TEXT PRIMARY KEY,
                corridor TEXT NOT NULL,
                origin_date TEXT NOT NULL,
                model_source TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                computed_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS recommendations (
                recommendation_id TEXT PRIMARY KEY,
                trigger_corridor TEXT NOT NULL,
                status TEXT NOT NULL,
                source_cascade_id TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                computed_at TEXT DEFAULT (datetime('now'))
            );

            INSERT OR IGNORE INTO schema_meta (key, value)
            VALUES ('phase', '4'), ('version', '0.5.0');
            """
        )
        conn.execute(
            "INSERT OR REPLACE INTO schema_meta (key, value) VALUES ('phase', '4')"
        )
        conn.execute(
            "INSERT OR REPLACE INTO schema_meta (key, value) VALUES ('version', '0.5.0')"
        )
        rec_cols = {
            row[1] for row in conn.execute("PRAGMA table_info(recommendations)").fetchall()
        }
        if rec_cols and "computed_at" not in rec_cols:
            conn.execute(
                "ALTER TABLE recommendations ADD COLUMN computed_at TEXT "
                "DEFAULT (datetime('now'))"
            )
        conn.commit()
    finally:
        conn.close()
