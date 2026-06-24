"""SQLite persistence for cascade simulation results."""

from __future__ import annotations

import json
import sqlite3
from uuid import UUID

from app.database import get_db_path
from app.models.generated import CascadeResult


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(get_db_path()))
    conn.row_factory = sqlite3.Row
    return conn


def insert_cascade_result(conn: sqlite3.Connection, result: CascadeResult, *, seed: int) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO cascade_results (
            scenario_id, corridor, disruption_duration_days, n_simulations,
            price_impact_pct, refinery_throughput_impact_pct, spr_days_required,
            affected_downstream_nodes, seed, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(result.scenario_id),
            result.corridor.value,
            result.disruption_duration_days,
            result.n_simulations,
            json.dumps(result.price_impact_pct.model_dump()),
            json.dumps(result.refinery_throughput_impact_pct.model_dump()),
            json.dumps(result.spr_days_required.model_dump()),
            json.dumps(result.affected_downstream_nodes),
            seed,
            json.dumps(result.model_dump(mode="json")),
        ),
    )


def list_cascade_results(*, corridor: str | None = None, latest_only: bool = False) -> list[CascadeResult]:
    with _connect() as conn:
        if latest_only:
            rows = conn.execute(
                """
                SELECT payload_json FROM cascade_results AS cr
                WHERE rowid = (
                    SELECT rowid FROM cascade_results
                    WHERE corridor = cr.corridor
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
                f"SELECT payload_json FROM cascade_results {where} ORDER BY computed_at DESC",
                params,
            ).fetchall()

    results: list[CascadeResult] = []
    for row in rows:
        payload = json.loads(row["payload_json"])
        results.append(CascadeResult.model_validate(payload))
    return results


def get_cascade_result(scenario_id: str) -> CascadeResult | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT payload_json FROM cascade_results WHERE scenario_id = ?",
            (scenario_id,),
        ).fetchone()
    if row is None:
        return None
    return CascadeResult.model_validate(json.loads(row["payload_json"]))