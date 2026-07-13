"""GDELT ingest parser tests."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from app.signals.ingest_gdelt import (
    GDELT_HEADERS,
    load_backtest_cache,
    parse_goldstein,
    parse_sql_date,
    row_to_dict,
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


def test_current_gdelt_61_column_schema_preserves_source_url() -> None:
    """New ADM2 columns must not shift ActionGeo or SOURCEURL fields."""
    assert len(GDELT_HEADERS) == 61
    row = [""] * len(GDELT_HEADERS)
    row[0] = "123"
    row[52] = "Strait of Hormuz"
    row[60] = "https://example.test/source"

    parsed = row_to_dict(row)

    assert parsed["ActionGeo_FullName"] == "Strait of Hormuz"
    assert parsed["SOURCEURL"] == "https://example.test/source"
