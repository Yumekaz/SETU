"""Forecast inference and fallback tests."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
import torch

from app.forecast.config import DEFAULT_CHECKPOINT_PATH, DEFAULT_FEATURES_PATH
from app.forecast.dataset import load_features_df
from app.forecast.features import build_daily_features
from app.forecast.inference import (
    forecast_corridor,
    highest_risk_forecast,
    run_all_forecasts,
)
from app.models.generated import Corridor, ForecastTrajectoryStep, ModelSource, PercentileBand, RiskForecast


def test_inference_returns_valid_trajectory() -> None:
    df = load_features_df(DEFAULT_FEATURES_PATH)
    fc = forecast_corridor(Corridor.hormuz, df)
    assert len(fc.trajectory) == 7
    for step in fc.trajectory:
        assert step.score_band.p10 <= step.score_band.p50 <= step.score_band.p90
    assert fc.feature_data_through == fc.origin_date


def test_run_all_forecasts_deterministic() -> None:
    df = load_features_df(DEFAULT_FEATURES_PATH)
    a = [f.model_dump(mode="json") for f in run_all_forecasts(df)]
    b = [f.model_dump(mode="json") for f in run_all_forecasts(df)]
    assert a == b


def test_run_all_forecasts_includes_other() -> None:
    df = load_features_df(DEFAULT_FEATURES_PATH)
    corridors = {f.corridor for f in run_all_forecasts(df)}
    assert Corridor.other in corridors


def test_other_corridor_uses_trend_fallback_with_actual_scores() -> None:
    df = build_daily_features()
    assert not df[df["corridor"] == "OTHER"].empty
    fc = forecast_corridor(Corridor.other, df)
    row = df[df["corridor"] == "OTHER"].sort_values("date").iloc[-1]
    assert fc.model_source == ModelSource.trend_fallback
    assert fc.origin_date == date.fromisoformat(str(row["date"])[:10])
    assert fc.feature_data_through == fc.origin_date
    meta_path = DEFAULT_CHECKPOINT_PATH.parent / "model_meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        assert "OTHER" in meta.get("fallback_corridors", [])
    else:
        ckpt = torch.load(DEFAULT_CHECKPOINT_PATH, map_location="cpu", weights_only=False)
        assert "OTHER" in ckpt.get("fallback_corridors", [])


def test_missing_corridor_rows_falls_back_to_trend() -> None:
    df = load_features_df(DEFAULT_FEATURES_PATH)
    df_no_other = df[df["corridor"] != "OTHER"].copy()
    fc = forecast_corridor(Corridor.other, df_no_other)
    assert fc.model_source == ModelSource.trend_fallback
    assert fc.corridor == Corridor.other
    assert len(fc.trajectory) == 7


def test_run_all_forecasts_with_partial_parquet() -> None:
    df = load_features_df(DEFAULT_FEATURES_PATH)
    df_no_other = df[df["corridor"] != "OTHER"]
    forecasts = run_all_forecasts(df_no_other)
    assert len(forecasts) == 4
    other_fc = next(f for f in forecasts if f.corridor == Corridor.other)
    assert other_fc.model_source == ModelSource.trend_fallback


def test_corrupt_checkpoint_falls_back_to_trend(tmp_path: Path) -> None:
    df = load_features_df(DEFAULT_FEATURES_PATH)
    bad_ckpt = tmp_path / "model.pt"
    bad_ckpt.write_bytes(b"not-a-checkpoint")
    fc = forecast_corridor(Corridor.hormuz, df, checkpoint_path=bad_ckpt)
    assert fc.model_source == ModelSource.trend_fallback


def test_partial_checkpoint_missing_keys_falls_back(tmp_path: Path) -> None:
    df = load_features_df(DEFAULT_FEATURES_PATH)
    ckpt = tmp_path / "model.pt"
    torch.save({"state_dict": {}}, ckpt)
    fc = forecast_corridor(Corridor.hormuz, df, checkpoint_path=ckpt)
    assert fc.model_source == ModelSource.trend_fallback


def test_highest_risk_forecast_uses_peak_horizon_p50() -> None:
    def _fc(corridor: Corridor, p50s: list[float]) -> RiskForecast:
        steps = [
            ForecastTrajectoryStep(
                forecast_date=date(2026, 6, 1),
                score_band=PercentileBand(p10=0.1, p50=p50s[0], p90=0.5),
            ),
            ForecastTrajectoryStep(
                forecast_date=date(2026, 6, 2),
                score_band=PercentileBand(p10=0.2, p50=p50s[1], p90=0.6),
            ),
        ]
        return RiskForecast(
            forecast_id="00000000-0000-0000-0000-000000000001",
            corridor=corridor,
            origin_date=date(2026, 5, 31),
            horizon_days=2,
            model_source=ModelSource.gru,
            training_data_through=date(2026, 5, 16),
            feature_data_through=date(2026, 5, 31),
            trajectory=steps,
        )

    hormuz = _fc(Corridor.hormuz, [0.3, 0.4])
    bab = _fc(Corridor.bab_el_mandeb, [0.9, 0.2])
    picked = highest_risk_forecast([hormuz, bab])
    assert picked.corridor == Corridor.bab_el_mandeb