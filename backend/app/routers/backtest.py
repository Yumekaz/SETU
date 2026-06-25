"""Phase 5/6 historical backtest API routes."""

from __future__ import annotations

import csv
import sqlite3
from typing import Any

from fastapi import APIRouter

from app.backtest.config import load_backtest_config
from app.backtest.replay import build_pit_daily_scores, load_backtest_events
from app.backtest.repository import insert_backtest_run, latest_backtest_run
from app.backtest.run import run_backtest
from app.database import get_db_path, init_db

router = APIRouter(prefix="/api", tags=["backtest"])


@router.get("/backtest/config")
def get_backtest_config() -> dict[str, Any]:
    cfg = load_backtest_config()
    return {
        "window_start": cfg.window_start.isoformat(),
        "window_end": cfg.window_end.isoformat(),
        "corridor": cfg.corridor.value,
        "risk_threshold": cfg.risk_threshold,
        "reference_point_date": cfg.reference_point_date.isoformat(),
        "reference_point_label": cfg.reference_point_label,
        "seed": cfg.seed,
        "n_simulations": cfg.n_simulations,
        "ground_truth_compare_date": cfg.ground_truth_compare_date.isoformat(),
    }


@router.post("/backtest/run")
def post_backtest_run() -> dict[str, Any]:
    init_db()
    result = run_backtest()
    payload = result.to_dict()
    with sqlite3.connect(str(get_db_path())) as conn:
        run_id = insert_backtest_run(conn, payload)
        conn.commit()
    payload["run_id"] = run_id
    return payload


@router.get("/backtest/latest")
def get_backtest_latest() -> dict[str, Any]:
    init_db()
    latest = latest_backtest_run()
    if latest is None:
        return {"status": "empty"}
    return latest


@router.get("/backtest/trajectory")
def get_backtest_trajectory() -> dict[str, Any]:
    """Full daily PIT Hormuz score series for replay UI."""
    cfg = load_backtest_config()
    events = load_backtest_events(cfg)
    trajectory = build_pit_daily_scores(events, config=cfg)
    return {
        "corridor": cfg.corridor.value,
        "window_start": cfg.window_start.isoformat(),
        "window_end": cfg.window_end.isoformat(),
        "points": [
            {"date": point.score_date.isoformat(), "score": point.score}
            for point in trajectory
        ],
    }


@router.get("/backtest/timeline")
def get_backtest_timeline() -> list[dict[str, Any]]:
    """Cited Hormuz 2026 timeline rows for replay sync."""
    cfg = load_backtest_config()
    rows: list[dict[str, Any]] = []
    with cfg.timeline_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(
                {
                    "date": row["date"],
                    "event_type": row["event_type"],
                    "description": row["description"],
                    "source_url": row["source_url"],
                    "brent_usd": row.get("brent_usd"),
                    "notes": row.get("notes", ""),
                }
            )
    return rows
