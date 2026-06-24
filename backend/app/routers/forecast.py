"""Phase 3 risk forecast API routes."""

from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter

from app.database import get_db_path, init_db
from app.forecast.config import DEFAULT_FEATURES_PATH
from app.forecast.features import build_daily_features, write_features_parquet
from app.forecast.inference import run_all_forecasts
from app.forecast.repository import insert_risk_forecast, list_risk_forecasts
from app.models.generated import Corridor

router = APIRouter(prefix="/api", tags=["forecast"])


def _ensure_features() -> None:
    if not DEFAULT_FEATURES_PATH.exists():
        df = build_daily_features()
        write_features_parquet(df, DEFAULT_FEATURES_PATH)


@router.get("/forecast")
def get_forecasts(corridor: Corridor | None = None) -> list[dict[str, Any]]:
    init_db()
    corridor_value = corridor.value if corridor is not None else None
    forecasts = list_risk_forecasts(corridor=corridor_value, latest_only=False)
    return [f.model_dump(mode="json") for f in forecasts]


@router.get("/forecast/latest")
def get_forecasts_latest() -> list[dict[str, Any]]:
    init_db()
    forecasts = list_risk_forecasts(latest_only=True)
    return [f.model_dump(mode="json") for f in forecasts]


@router.post("/forecast/run")
def post_forecast_run() -> list[dict[str, Any]]:
    init_db()
    _ensure_features()
    forecasts = run_all_forecasts()
    with sqlite3.connect(str(get_db_path())) as conn:
        for fc in forecasts:
            insert_risk_forecast(conn, fc)
        conn.commit()
    return [f.model_dump(mode="json") for f in forecasts]