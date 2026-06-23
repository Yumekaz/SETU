"""SQLite database initialization for SETU."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"
DEFAULT_DB_PATH = DATA_DIR / "setu.db"


def get_db_path() -> Path:
    url = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")
    if url.startswith("sqlite:///"):
        path = Path(url.replace("sqlite:///", ""))
        if not path.is_absolute():
            path = ROOT / path
        return path
    return DEFAULT_DB_PATH


def init_db() -> None:
    """Create data directory and initialize SQLite with Phase 0 placeholder tables."""
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

            INSERT OR IGNORE INTO schema_meta (key, value)
            VALUES ('phase', '0'), ('version', '0.1.0');
            """
        )
        conn.commit()
    finally:
        conn.close()