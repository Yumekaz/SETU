"""Phase 5 backtest API integration tests."""

from __future__ import annotations

import pytest
from app.backtest.repository import count_backtest_runs
from app.database import init_db
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "phase5.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:////{db_file}")
    monkeypatch.setenv("SETU_MC_N_SIMULATIONS", "50")
    monkeypatch.setenv("SETU_EXTRACTOR_MODE", "rules")
    init_db()
    return TestClient(app)


def test_backtest_config_locked_reference(client: TestClient) -> None:
    resp = client.get("/api/backtest/config")
    assert resp.status_code == 200
    body = resp.json()
    assert body["reference_point_date"] == "2026-03-11"
    assert body["risk_threshold"] == 0.35


def test_backtest_run_persists_and_matches_direct(client: TestClient) -> None:
    from app.backtest.run import run_backtest

    direct = run_backtest().to_dict()
    before = count_backtest_runs()
    resp = client.post("/api/backtest/run")
    assert resp.status_code == 200
    body = resp.json()
    assert count_backtest_runs() == before + 1
    assert body["lead_time_days"] == direct["lead_time_days"]
    assert body["status"] == direct["status"]
    assert "run_id" in body


def test_backtest_latest_after_run(client: TestClient) -> None:
    client.post("/api/backtest/run")
    latest = client.get("/api/backtest/latest")
    assert latest.status_code == 200
    assert latest.json()["reference_point_date"] == "2026-03-11"


def test_health_phase5(client: TestClient) -> None:
    health = client.get("/health")
    assert health.json() == {"status": "ok", "version": "0.6.0", "phase": 5}
