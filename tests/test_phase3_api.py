"""Phase 3 forecast API integration tests."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from app.database import get_db_path, init_db
from app.main import app
from fastapi.testclient import TestClient

SCRATCH = Path("/tmp/grok-goal-87d4d5399344/implementer")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "phase3.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:////{db_file}")
    monkeypatch.setenv("SETU_MC_N_SIMULATIONS", "50")
    monkeypatch.setenv("SETU_EXTRACTOR_MODE", "rules")
    init_db()
    return TestClient(app)


def test_forecast_run_and_latest(client: TestClient) -> None:
    run = client.post("/api/forecast/run")
    assert run.status_code == 200
    body = run.json()
    assert len(body) >= 3
    assert all(len(f["trajectory"]) == 7 for f in body)

    latest = client.get("/api/forecast/latest")
    assert latest.status_code == 200
    corridors = [r["corridor"] for r in latest.json()]
    assert len(corridors) == len(set(corridors))


def test_cascade_from_forecast(client: TestClient) -> None:
    client.post("/api/forecast/run")
    resp = client.post("/api/cascade/simulate/from-forecast", params={"seed": 42})
    assert resp.status_code == 200
    data = resp.json()
    assert "trigger_forecast" in data
    assert data["corridor"] == data["trigger_forecast"]["corridor"]
    assert "price_impact_pct" in data


def test_verification_forecast_api_writes_scratch(client: TestClient) -> None:
    health = client.get("/health")
    contracts = client.get("/api/contracts")
    run = client.post("/api/forecast/run")
    latest = client.get("/api/forecast/latest")
    list_all = client.get("/api/forecast")
    cascade = client.post("/api/cascade/simulate/from-forecast", params={"seed": 7})

    with sqlite3.connect(str(get_db_path())) as conn:
        count = conn.execute("SELECT COUNT(*) FROM risk_forecasts").fetchone()[0]

    evidence = {
        "health": {"status": health.status_code, "body": health.json()},
        "contracts_keys": sorted(contracts.json().keys()),
        "forecast_run_status": run.status_code,
        "forecast_latest": latest.json(),
        "forecast_list_len": len(list_all.json()),
        "from_forecast": cascade.json(),
        "sqlite_forecast_rows": count,
    }
    SCRATCH.mkdir(parents=True, exist_ok=True)
    (SCRATCH / "forecast_api.log").write_text(json.dumps(evidence, indent=2), encoding="utf-8")

    assert health.json() == {"status": "ok", "version": "0.4.0", "phase": 3}
    assert "risk_forecast" in contracts.json()
    assert count >= 1
    assert cascade.status_code == 200