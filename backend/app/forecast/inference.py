"""Load checkpoint and produce RiskForecast trajectories."""

from __future__ import annotations

import json
import logging
import pickle
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import numpy as np
import pandas as pd
import torch

from app.forecast.config import (
    CORRIDOR_ORDER,
    DEFAULT_CHECKPOINT_PATH,
    FEATURE_COLUMNS,
    HORIZON_DAYS,
    LOOKBACK_DAYS,
)
from app.forecast.dataset import corridor_one_hot, load_features_df
from app.forecast.fallback import build_trend_forecast, latest_row_for_corridor
from app.models.generated import (
    Corridor,
    ForecastTrajectoryStep,
    ModelSource,
    PercentileBand,
    RiskForecast,
)
from ml.forecast.gru_model import RiskGRUForecaster

logger = logging.getLogger(__name__)

_REQUIRED_META_KEYS = frozenset({"training_data_through", "eligible_corridors"})


@dataclass(frozen=True)
class LoadedCheckpoint:
    model: RiskGRUForecaster | None
    training_data_through: date | None
    eligible_corridors: frozenset[str]
    valid: bool


def _parse_training_through(raw: object) -> date:
    return date.fromisoformat(str(raw)[:10])


def _load_checkpoint(path: Path) -> LoadedCheckpoint:
    """Load checkpoint; degrade gracefully on missing or corrupt files."""
    invalid = LoadedCheckpoint(None, None, frozenset(), False)
    if not path.exists():
        return invalid

    meta_path = path.parent / "model_meta.json"
    try:
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if not _REQUIRED_META_KEYS <= meta.keys():
                logger.warning("checkpoint metadata missing required keys: %s", meta_path)
                return invalid
            state = torch.load(path, map_location="cpu", weights_only=True)
        else:
            ckpt = torch.load(path, map_location="cpu", weights_only=False)
            if not {"state_dict", "training_data_through", "eligible_corridors"} <= ckpt.keys():
                logger.warning("legacy checkpoint missing required keys: %s", path)
                return invalid
            meta = {
                "training_data_through": ckpt["training_data_through"],
                "eligible_corridors": ckpt["eligible_corridors"],
            }
            state = ckpt["state_dict"]

        model = RiskGRUForecaster()
        model.load_state_dict(state)
        model.eval()
        training_through = _parse_training_through(meta["training_data_through"])
        eligible = frozenset(str(c) for c in meta["eligible_corridors"])
        return LoadedCheckpoint(model, training_through, eligible, True)
    except (
        OSError,
        pickle.UnpicklingError,
        KeyError,
        RuntimeError,
        json.JSONDecodeError,
        ValueError,
        TypeError,
    ) as exc:
        logger.warning("failed to load checkpoint %s: %s", path, exc)
        return invalid


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


def _latest_date_in_frame(df: pd.DataFrame) -> date:
    return max(date.fromisoformat(str(d)[:10]) for d in df["date"].unique())


def _phase1_score_for_corridor(corridor: Corridor, df: pd.DataFrame) -> tuple[date, float, str]:
    """Resolve score/trend from Phase 1 scoring when parquet rows are absent."""
    from app.forecast.features import extract_events_from_cache
    from app.signals.score import build_risk_scores

    origin_date = _latest_date_in_frame(df) if len(df) else date.today()
    events = extract_events_from_cache()
    prior_date = origin_date - timedelta(days=7)
    prior_scores = {
        s.corridor: s.score
        for s in build_risk_scores(events, score_date=prior_date)
    }
    scores = build_risk_scores(events, score_date=origin_date, prior_scores=prior_scores)
    for score in scores:
        if score.corridor == corridor:
            return origin_date, float(score.score), score.trend_7d.value
    return origin_date, 0.0, "STABLE"


def _trend_fallback_missing_rows(
    corridor: Corridor,
    df: pd.DataFrame,
    *,
    training_data_through: date | None,
) -> RiskForecast:
    """Graceful TREND_FALLBACK when a corridor has no feature parquet rows."""
    logger.warning(
        "no feature rows for corridor %s; using Phase 1 score fallback",
        corridor.value,
    )
    origin_date, current_score, trend_7d = _phase1_score_for_corridor(corridor, df)
    training_through = training_data_through or origin_date
    return build_trend_forecast(
        corridor,
        origin_date=origin_date,
        current_score=current_score,
        trend_7d=trend_7d,
        training_data_through=training_through,
        feature_data_through=origin_date,
    )


def _trend_from_row(
    corridor: Corridor,
    row: pd.Series,
    *,
    training_data_through: date,
) -> RiskForecast:
    origin_date = date.fromisoformat(str(row["date"])[:10])
    return build_trend_forecast(
        corridor,
        origin_date=origin_date,
        current_score=float(row["risk_score"]),
        trend_7d=str(row["trend_7d"]),
        training_data_through=training_data_through,
        feature_data_through=origin_date,
    )


def forecast_corridor(
    corridor: Corridor,
    df: pd.DataFrame,
    *,
    checkpoint_path: Path | None = None,
    loaded: LoadedCheckpoint | None = None,
) -> RiskForecast:
    ckpt_path = checkpoint_path or DEFAULT_CHECKPOINT_PATH
    bundle = loaded if loaded is not None else _load_checkpoint(ckpt_path)

    sub = df[df["corridor"] == corridor.value].copy()
    if sub.empty:
        return _trend_fallback_missing_rows(
            corridor,
            df,
            training_data_through=bundle.training_data_through,
        )

    sub["_d"] = pd.to_datetime(sub["date"])
    sub = sub.sort_values("_d")
    origin_date = date.fromisoformat(str(sub.iloc[-1]["date"])[:10])
    training_through = bundle.training_data_through or origin_date

    if not bundle.valid or bundle.model is None:
        row = latest_row_for_corridor(df, corridor.value)
        return _trend_from_row(
            corridor,
            row,
            training_data_through=training_through,
        )

    if corridor.value not in bundle.eligible_corridors:
        row = latest_row_for_corridor(df, corridor.value)
        return _trend_from_row(
            corridor,
            row,
            training_data_through=training_through,
        )

    window = _build_inference_tensor(df, corridor.value, origin_date)
    if window is None:
        row = latest_row_for_corridor(df, corridor.value)
        return _trend_from_row(
            corridor,
            row,
            training_data_through=training_through,
        )

    with torch.no_grad():
        pred = bundle.model(torch.from_numpy(window[np.newaxis, ...]))[0].numpy()

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
        feature_data_through=origin_date,
        trajectory=trajectory,
    )


def run_all_forecasts(
    df: pd.DataFrame | None = None,
    *,
    features_path: Path | None = None,
    checkpoint_path: Path | None = None,
) -> list[RiskForecast]:
    from app.forecast.config import DEFAULT_FEATURES_PATH

    frame = df if df is not None else load_features_df(features_path or DEFAULT_FEATURES_PATH)
    ckpt_path = checkpoint_path or DEFAULT_CHECKPOINT_PATH
    bundle = _load_checkpoint(ckpt_path)
    return [
        forecast_corridor(
            Corridor(corridor),
            frame,
            checkpoint_path=ckpt_path,
            loaded=bundle,
        )
        for corridor in CORRIDOR_ORDER
    ]


def highest_risk_forecast(forecasts: list[RiskForecast]) -> RiskForecast:
    """Pick simulatable corridor with highest peak p50 across the 7-day horizon."""
    from app.simulation.corridors import SUPPORTED_SIMULATION_CORRIDORS

    simulatable = [f for f in forecasts if f.corridor in SUPPORTED_SIMULATION_CORRIDORS]
    if not simulatable:
        raise ValueError("no simulatable forecasts")

    def ranking_key(fc: RiskForecast) -> tuple[float, str]:
        peak = max(step.score_band.p50 for step in fc.trajectory)
        return (peak, fc.corridor.value)

    return max(simulatable, key=ranking_key)
