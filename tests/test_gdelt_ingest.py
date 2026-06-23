"""GDELT ingest parser tests."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from app.signals.ingest_gdelt import (
    load_backtest_cache,
    parse_goldstein,
    parse_sql_date,
)

ROOT = Path(__file__).resolve().parent.parent
BACKTEST = ROOT / "data" / "samples" / "gdelt_hormuz_backtest.json"


def test_parse_sql_date_normalizes_utc_date() -> None:
    assert parse_sql_date("20260311") == date(2026, 3, 11)


def test_parse_goldstein_handles_blank() -> None:
    assert parse_goldstein("") == 0.0
    assert parse_goldstein("-4.5") == -4.5


def test_backtest_cache_has_at_least_fifty_rows() -> None:
    rows = load_backtest_cache(BACKTEST)
    assert len(rows) >= 50
    assert "GLOBALEVENTID" in rows[0]
