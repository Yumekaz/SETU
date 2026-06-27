"""Phase 3 risk forecast API routes."""

from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter

from app.database import get_db_path, init_db
from app.forecast.repository import insert_risk_forecast, list_risk_forecasts
from app.models.generated import Corridor

router = APIRouter(prefix="/api", tags=["forecast"])


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
    from app.forecast.features import ensure_features_parquet
    from app.forecast.inference import run_all_forecasts

    init_db()
    ensure_features_parquet()
    forecasts = run_all_forecasts()
    with sqlite3.connect(str(get_db_path())) as conn:
        for fc in forecasts:
            insert_risk_forecast(conn, fc)
        conn.commit()
    return [f.model_dump(mode="json") for f in forecasts]
