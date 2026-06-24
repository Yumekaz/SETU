"""Load checkpoint and produce RiskForecast trajectories."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import numpy as np
import pandas as pd
import torch

from app.forecast.config import DEFAULT_CHECKPOINT_PATH, HORIZON_DAYS, LOOKBACK_DAYS
from app.forecast.config import FEATURE_COLUMNS, LOOKBACK_DAYS
from app.forecast.dataset import corridor_one_hot, load_features_df
from app.forecast.fallback import build_trend_forecast, latest_row_for_corridor
from app.models.generated import Corridor, ForecastTrajectoryStep, ModelSource, PercentileBand, RiskForecast
from ml.forecast.gru_model import RiskGRUForecaster

ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _build_inference_tensor(
    df: pd.DataFrame, corridor: str, origin_date: date
) -> np.ndarray | None:
    dates = sorted({date.fromisoformat(str(d)[:10]) for d in df["date"].unique()})
    if origin_date not in dates:
        return None
    idx = dates.index(origin_date)
    if idx < LOOKBACK_DAYS - 1:
        return None
    lookback = dates[idx - LOOKBACK_DAYS + 1 : idx + 1]
    by_key = {
        (row["corridor"], date.fromisoformat(str(row["date"])[:10])): row
        for _, row in df.iterrows()
    }
    window_rows: list[np.ndarray] = []
    for lb in lookback:
        key = (corridor, lb)
        if key not in by_key:
            return None
        row = by_key[key]
        feats = [float(row[c]) for c in FEATURE_COLUMNS]
        window_rows.append(
            np.array(feats + corridor_one_hot(corridor).tolist(), dtype=np.float32)
        )
    return np.stack(window_rows)


def _load_checkpoint(path: Path) -> dict:
    return torch.load(path, map_location="cpu", weights_only=False)


def forecast_corridor(
    corridor: Corridor,
    df: pd.DataFrame,
    *,
    checkpoint_path: Path | None = None,
) -> RiskForecast:
    ckpt_path = checkpoint_path or DEFAULT_CHECKPOINT_PATH
    sub = df[df["corridor"] == corridor.value].copy()
    if sub.empty:
        latest_any = df.sort_values("date").iloc[-1]
        origin_date = date.fromisoformat(str(latest_any["date"])[:10])
        return build_trend_forecast(
            corridor,
            origin_date=origin_date,
            current_score=0.0,
            trend_7d="STABLE",
            training_data_through=origin_date,
        )

    sub["_d"] = pd.to_datetime(sub["date"])
    sub = sub.sort_values("_d")
    origin_date = date.fromisoformat(str(sub.iloc[-1]["date"])[:10])
    training_through = date.fromisoformat(str(sub.iloc[-1]["date"])[:10])

    if ckpt_path.exists():
        ckpt = _load_checkpoint(ckpt_path)
        training_through = date.fromisoformat(ckpt["training_data_through"])
        eligible = set(ckpt.get("eligible_corridors", []))
        if corridor.value not in eligible:
            row = latest_row_for_corridor(df, corridor.value)
            return build_trend_forecast(
                corridor,
                origin_date=origin_date,
                current_score=float(row["risk_score"]),
                trend_7d=str(row["trend_7d"]),
                training_data_through=training_through,
            )

        window = _build_inference_tensor(df, corridor.value, origin_date)
        if window is None:
            row = latest_row_for_corridor(df, corridor.value)
            return build_trend_forecast(
                corridor,
                origin_date=origin_date,
                current_score=float(row["risk_score"]),
                trend_7d=str(row["trend_7d"]),
                training_data_through=training_through,
            )

        model = RiskGRUForecaster()
        model.load_state_dict(ckpt["state_dict"])
        model.eval()
        with torch.no_grad():
            pred = model(torch.from_numpy(window[np.newaxis, ...]))[0].numpy()

        trajectory: list[ForecastTrajectoryStep] = []
        for step in range(HORIZON_DAYS):
            fd = origin_date + timedelta(days=step + 1)
            band = PercentileBand(
                p10=round(float(pred[step, 0]), 4),
                p50=round(float(pred[step, 1]), 4),
                p90=round(float(pred[step, 2]), 4),
            )
            trajectory.append(ForecastTrajectoryStep(forecast_date=fd, score_band=band))

        fid = uuid5(NAMESPACE_URL, f"setu-forecast-gru:{corridor.value}:{origin_date}")
        return RiskForecast(
            forecast_id=fid,
            corridor=corridor,
            origin_date=origin_date,
            horizon_days=HORIZON_DAYS,
            model_source=ModelSource.gru,
            training_data_through=training_through,
            trajectory=trajectory,
        )

    row = latest_row_for_corridor(df, corridor.value)
    return build_trend_forecast(
        corridor,
        origin_date=origin_date,
        current_score=float(row["risk_score"]),
        trend_7d=str(row["trend_7d"]),
        training_data_through=training_through,
    )


def run_all_forecasts(
    df: pd.DataFrame | None = None,
    *,
    features_path: Path | None = None,
    checkpoint_path: Path | None = None,
) -> list[RiskForecast]:
    from app.forecast.config import DEFAULT_FEATURES_PATH
    from app.signals.score import CORRIDOR_ORDER

    frame = df if df is not None else load_features_df(features_path or DEFAULT_FEATURES_PATH)
    return [
        forecast_corridor(corridor, frame, checkpoint_path=checkpoint_path)
        for corridor in CORRIDOR_ORDER
    ]


def highest_risk_forecast(forecasts: list[RiskForecast]) -> RiskForecast:
    from app.simulation.corridors import SUPPORTED_SIMULATION_CORRIDORS

    simulatable = [f for f in forecasts if f.corridor in SUPPORTED_SIMULATION_CORRIDORS]
    if not simulatable:
        raise ValueError("no simulatable forecasts")

    def day7_p50(fc: RiskForecast) -> float:
        return fc.trajectory[-1].score_band.p50

    return max(simulatable, key=day7_p50)