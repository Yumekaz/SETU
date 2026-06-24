"""Phase 3 daily feature builder tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.forecast.config import FEATURE_COLUMNS
from app.forecast.features import build_daily_features

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