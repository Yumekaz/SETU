"""Phase 3 daily feature builder tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.forecast.config import CORRIDOR_ORDER, FEATURE_COLUMNS
from app.forecast.features import (
    build_daily_features,
    ensure_features_parquet,
    parquet_has_all_corridors,
    write_features_parquet,
)
from app.forecast.dataset import load_features_df

ROOT = Path(__file__).resolve().parent.parent


def test_build_daily_features_has_required_columns_and_corridors() -> None:
    df = build_daily_features()
    for col in FEATURE_COLUMNS:
        assert col in df.columns
    assert "date" in df.columns
    assert "corridor" in df.columns
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
    assert "trend_7d" in other.columns


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