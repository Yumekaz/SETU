"""Phase 3 daily feature builder tests."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from app.forecast.config import FEATURE_COLUMNS
from app.forecast.features import build_daily_features

SCRATCH = Path("/tmp/grok-goal-87d4d5399344/implementer")
ROOT = Path(__file__).resolve().parent.parent


def test_build_daily_features_has_required_columns_and_corridors() -> None:
    df = build_daily_features()
    for col in FEATURE_COLUMNS:
        assert col in df.columns
    assert "date" in df.columns
    assert "corridor" in df.columns
    assert len(df[df["corridor"] == "HORMUZ"]) > 30
    for corridor in ("HORMUZ", "BAB_EL_MANDEB", "MALACCA"):
        assert corridor in set(df["corridor"])


def test_build_daily_features_is_deterministic() -> None:
    first = build_daily_features().to_json()
    second = build_daily_features().to_json()
    assert first == second


def test_build_daily_features_writes_scratch_evidence() -> None:
    df = build_daily_features()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    payload = {
        "rows": len(df),
        "columns": list(df.columns),
        "date_min": str(df["date"].min()),
        "date_max": str(df["date"].max()),
        "per_corridor": df.groupby("corridor").size().to_dict(),
        "sample": df.head(3).to_dict(orient="records"),
    }
    (SCRATCH / "daily_features.txt").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    assert payload["rows"] > 0