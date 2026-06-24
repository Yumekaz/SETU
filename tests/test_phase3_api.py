"""Phase 3 forecast API integration tests."""

from __future__ import annotations

import sqlite3

import pytest
from app.database import get_db_path, init_db
from app.main import app
from fastapi.testclient import TestClient


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
    assert len(body) >= 4
    assert all(len(f["trajectory"]) == 7 for f in body)
    assert all("feature_data_through" in f for f in body)

    latest = client.get("/api/forecast/latest")
    assert latest.status_code == 200
    corridors = [r["corridor"] for r in latest.json()]
    assert len(corridors) == len(set(corridors))


def test_forecast_invalid_corridor_returns_422(client: TestClient) -> None:
    resp = client.get("/api/forecast", params={"corridor": "INVALID"})
    assert resp.status_code == 422


def test_cascade_from_forecast(client: TestClient) -> None:
    client.post("/api/forecast/run")
    resp = client.post("/api/cascade/simulate/from-forecast", params={"seed": 42})
    assert resp.status_code == 200
    data = resp.json()
    assert "trigger_forecast" in data
    assert data["corridor"] == data["trigger_forecast"]["corridor"]
    assert "price_impact_pct" in data


def test_cascade_from_forecast_404_without_forecasts(client: TestClient) -> None:
    resp = client.post("/api/cascade/simulate/from-forecast", params={"seed": 42})
    assert resp.status_code == 404


@pytest.mark.parametrize("n_simulations", [0, -1])
def test_cascade_from_forecast_invalid_n_simulations_returns_422(
    client: TestClient, n_simulations: int
) -> None:
    client.post("/api/forecast/run")
    resp = client.post(
        "/api/cascade/simulate/from-forecast",
        params={"seed": 42, "n_simulations": n_simulations},
    )
    assert resp.status_code == 422


@pytest.mark.parametrize("n_simulations", [0, -1])
def test_cascade_from_risk_invalid_n_simulations_returns_422(
    client: TestClient, n_simulations: int
) -> None:
    client.post("/api/pipeline/run", json={"source": "cache"})
    resp = client.post(
        "/api/cascade/simulate/from-risk",
        params={"seed": 42, "n_simulations": n_simulations},
    )
    assert resp.status_code == 422


def test_forecast_api_health_and_contracts(client: TestClient) -> None:
    health = client.get("/health")
    contracts = client.get("/api/contracts")
    run = client.post("/api/forecast/run")
    cascade = client.post("/api/cascade/simulate/from-forecast", params={"seed": 7})

    with sqlite3.connect(str(get_db_path())) as conn:
        count = conn.execute("SELECT COUNT(*) FROM risk_forecasts").fetchone()[0]

    assert health.json() == {"status": "ok", "version": "0.4.0", "phase": 3}
    assert "risk_forecast" in contracts.json()
    assert count >= 1
    assert run.status_code == 200
    assert cascade.status_code == 200