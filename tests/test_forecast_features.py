"""Phase 3 daily feature builder tests."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.forecast.config import CORRIDOR_ORDER, FEATURE_COLUMNS, PARQUET_COLUMNS
from app.forecast.dataset import load_features_df
from app.forecast.features import (
    build_current_signal_features,
    build_daily_features,
    ensure_features_parquet,
    latest_event_date,
    parquet_has_all_corridors,
    write_features_parquet,
)
from app.models.generated import Corridor, EventType, SignalEvent
from app.signals.repository import insert_signal_event

ROOT = Path(__file__).resolve().parent.parent


def test_build_daily_features_has_required_columns_and_corridors() -> None:
    df = build_daily_features()
    assert list(df.columns) == list(PARQUET_COLUMNS)
    for col in FEATURE_COLUMNS:
        assert col in df.columns
    assert "trend_7d" not in df.columns
    assert len(df[df["corridor"] == "HORMUZ"]) > 30
    for corridor in ("HORMUZ", "BAB_EL_MANDEB", "MALACCA", "OTHER"):
        assert corridor in set(df["corridor"])


def test_build_daily_features_is_deterministic() -> None:
    first = build_daily_features().to_json()
    second = build_daily_features().to_json()
    assert first == second


def test_build_daily_features_other_has_scored_rows() -> None:
    df = build_daily_features()
    other = df[df["corridor"] == "OTHER"]
    assert len(other) > 30
    assert float(other["risk_score"].iloc[-1]) >= 0.0


def test_parquet_has_all_corridors_detects_stale_file(tmp_path: Path) -> None:
    df = load_features_df(ROOT / "data" / "forecast" / "daily_features.parquet")
    stale = df[df["corridor"] != "OTHER"]
    path = tmp_path / "daily_features.parquet"
    write_features_parquet(stale, path)
    assert not parquet_has_all_corridors(path)
    assert set(CORRIDOR_ORDER) - set(stale["corridor"].unique()) == {"OTHER"}


def test_ensure_features_parquet_rebuilds_incomplete(tmp_path: Path) -> None:
    df = load_features_df(ROOT / "data" / "forecast" / "daily_features.parquet")
    stale = df[df["corridor"] != "OTHER"]
    path = tmp_path / "daily_features.parquet"
    write_features_parquet(stale, path)
    ensure_features_parquet(path)
    rebuilt = load_features_df(path)
    assert parquet_has_all_corridors(path)
    for corridor in CORRIDOR_ORDER:
        assert corridor in set(rebuilt["corridor"].unique())


def test_latest_event_date_uses_newest_signal() -> None:
    events = [
        SignalEvent(
            event_id=uuid4(),
            corridor=Corridor.hormuz,
            event_type=EventType.military,
            severity=0.7,
            goldstein_scale=-7.0,
            confidence=0.8,
            event_date=date(2026, 6, 1),
            ingested_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
            source_url="https://example.com/a",
            raw_text_snippet="Hormuz naval incident",
        ),
        SignalEvent(
            event_id=uuid4(),
            corridor=Corridor.hormuz,
            event_type=EventType.military,
            severity=0.8,
            goldstein_scale=-8.0,
            confidence=0.9,
            event_date=date(2026, 7, 7),
            ingested_at=datetime(2026, 7, 7, tzinfo=timezone.utc),
            source_url="https://example.com/b",
            raw_text_snippet="Hormuz strike report",
        ),
    ]

    assert latest_event_date(events) == date(2026, 7, 7)


def test_build_current_signal_features_extends_to_live_db_event(
    tmp_path: Path, monkeypatch
) -> None:
    from app.database import init_db

    db_file = tmp_path / "forecast-live.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:////{db_file}")
    init_db()
    event = SignalEvent(
        event_id=uuid4(),
        corridor=Corridor.hormuz,
        event_type=EventType.military,
        severity=0.83,
        goldstein_scale=-8.3,
        confidence=0.88,
        event_date=date(2026, 7, 7),
        ingested_at=datetime(2026, 7, 7, tzinfo=timezone.utc),
        source_url="https://example.com/hormuz",
        raw_text_snippet="Strait of Hormuz military strikes",
    )

    import sqlite3

    with sqlite3.connect(str(db_file)) as conn:
        insert_signal_event(conn, event)
        conn.commit()

    df = build_current_signal_features()
    assert max(df["date"]) == "2026-07-07"
    hormuz = df[(df["corridor"] == "HORMUZ") & (df["date"] == "2026-07-07")]
    assert int(hormuz.iloc[0]["event_count"]) == 1
