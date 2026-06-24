"""Trend-based forecast fallback for sparse corridors."""

from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid5, NAMESPACE_URL, UUID

import pandas as pd

from app.forecast.config import HORIZON_DAYS
from app.models.generated import Corridor, ForecastTrajectoryStep, ModelSource, PercentileBand, RiskForecast


def _clamp_score(v: float) -> float:
    return max(0.0, min(1.0, v))


def trend_step(current: float, trend: str, day_offset: int, *, delta: float = 0.02) -> float:
    if trend == "RISING":
        return _clamp_score(current + delta * day_offset)
    if trend == "FALLING":
        return _clamp_score(current - delta * day_offset)
    return current


def build_trend_forecast(
    corridor: Corridor,
    *,
    origin_date: date,
    current_score: float,
    trend_7d: str,
    training_data_through: date,
) -> RiskForecast:
    trajectory: list[ForecastTrajectoryStep] = []
    for step in range(1, HORIZON_DAYS + 1):
        fd = origin_date + timedelta(days=step)
        p50 = round(trend_step(current_score, trend_7d, step), 4)
        spread = 0.05
        band = PercentileBand(
            p10=round(_clamp_score(p50 - spread), 4),
            p50=p50,
            p90=round(_clamp_score(p50 + spread), 4),
        )
        trajectory.append(ForecastTrajectoryStep(forecast_date=fd, score_band=band))

    fid = uuid5(NAMESPACE_URL, f"setu-forecast-fallback:{corridor.value}:{origin_date}")
    return RiskForecast(
        forecast_id=fid,
        corridor=corridor,
        origin_date=origin_date,
        horizon_days=HORIZON_DAYS,
        model_source=ModelSource.trend_fallback,
        training_data_through=training_data_through,
        trajectory=trajectory,
    )


def latest_row_for_corridor(df: pd.DataFrame, corridor: str) -> pd.Series:
    sub = df[df["corridor"] == corridor].copy()
    sub["_d"] = pd.to_datetime(sub["date"])
    return sub.sort_values("_d").iloc[-1]