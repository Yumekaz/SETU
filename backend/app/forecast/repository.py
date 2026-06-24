"""SQLite persistence for risk forecasts."""

from __future__ import annotations

import json
import sqlite3

from app.database import get_db_path
from app.models.generated import RiskForecast


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(get_db_path()))
    conn.row_factory = sqlite3.Row
    return conn


def insert_risk_forecast(conn: sqlite3.Connection, forecast: RiskForecast) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO risk_forecasts (
            forecast_id, corridor, origin_date, model_source, payload_json
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            str(forecast.forecast_id),
            forecast.corridor.value,
            forecast.origin_date.isoformat(),
            forecast.model_source.value,
            json.dumps(forecast.model_dump(mode="json")),
        ),
    )


def list_risk_forecasts(
    *, corridor: str | None = None, latest_only: bool = False
) -> list[RiskForecast]:
    with _connect() as conn:
        if latest_only:
            rows = conn.execute(
                """
                SELECT payload_json FROM risk_forecasts AS rf
                WHERE rowid = (
                    SELECT rowid FROM risk_forecasts
                    WHERE corridor = rf.corridor
                    ORDER BY datetime(computed_at) DESC, rowid DESC
                    LIMIT 1
                )
                ORDER BY corridor
                """
            ).fetchall()
        else:
            clauses: list[str] = []
            params: list[str] = []
            if corridor:
                clauses.append("corridor = ?")
                params.append(corridor)
            where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
            rows = conn.execute(
                f"SELECT payload_json FROM risk_forecasts {where} ORDER BY computed_at DESC",
                params,
            ).fetchall()

    out: list[RiskForecast] = []
    for row in rows:
        out.append(RiskForecast.model_validate(json.loads(row["payload_json"])))
    return out
