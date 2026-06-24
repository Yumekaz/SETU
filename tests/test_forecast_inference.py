"""Forecast inference and fallback tests."""

from __future__ import annotations

import json
from pathlib import Path

import torch

from app.forecast.config import DEFAULT_CHECKPOINT_PATH, DEFAULT_FEATURES_PATH
from app.forecast.dataset import load_features_df
from app.forecast.inference import forecast_corridor, run_all_forecasts
from app.models.generated import Corridor, ModelSource

SCRATCH = Path("/tmp/grok-goal-87d4d5399344/implementer")


def test_inference_returns_valid_trajectory() -> None:
    df = load_features_df(DEFAULT_FEATURES_PATH)
    fc = forecast_corridor(Corridor.hormuz, df)
    assert len(fc.trajectory) == 7
    for step in fc.trajectory:
        assert step.score_band.p10 <= step.score_band.p50 <= step.score_band.p90


def test_run_all_forecasts_deterministic() -> None:
    df = load_features_df(DEFAULT_FEATURES_PATH)
    a = [f.model_dump(mode="json") for f in run_all_forecasts(df)]
    b = [f.model_dump(mode="json") for f in run_all_forecasts(df)]
    assert a == b


def test_other_corridor_uses_trend_fallback() -> None:
    df = load_features_df(DEFAULT_FEATURES_PATH)
    fc = forecast_corridor(Corridor.other, df)
    ckpt = torch.load(DEFAULT_CHECKPOINT_PATH, map_location="cpu", weights_only=False)
    assert "OTHER" in ckpt.get("fallback_corridors", [])
    assert fc.model_source == ModelSource.trend_fallback

    SCRATCH.mkdir(parents=True, exist_ok=True)
    sample = forecast_corridor(Corridor.hormuz, df).model_dump(mode="json")
    (SCRATCH / "forecast_sample.json").write_text(json.dumps(sample, indent=2), encoding="utf-8")