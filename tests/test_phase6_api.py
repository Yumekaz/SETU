"""Phase 6 backtest feed + health API tests."""

from __future__ import annotations

import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "phase6.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:////{db_file}")
    monkeypatch.setenv("SETU_MC_N_SIMULATIONS", "50")
    monkeypatch.setenv("SETU_EXTRACTOR_MODE", "rules")
    from app.database import init_db

    init_db()
    return TestClient(app)


def test_health_phase6(client: TestClient) -> None:
    assert client.get("/health").json() == {
        "status": "ok",
        "version": "0.7.0",
        "phase": 6,
    }


def test_backtest_trajectory_full_window(client: TestClient) -> None:
    first = client.get("/api/backtest/trajectory")
    second = client.get("/api/backtest/trajectory")
    assert first.status_code == 200
    body = first.json()
    assert body["corridor"] == "HORMUZ"
    assert body["window_start"] == "2026-02-01"
    assert body["window_end"] == "2026-06-30"
    points = body["points"]
    assert len(points) >= 140
    assert points[0]["date"] == "2026-02-01"
    assert points[-1]["date"] == "2026-06-30"
    assert all(isinstance(p["score"], (int, float)) for p in points)
    assert first.json() == second.json()


def test_backtest_timeline_cited_rows(client: TestClient) -> None:
    first = client.get("/api/backtest/timeline")
    second = client.get("/api/backtest/timeline")
    assert first.status_code == 200
    rows = first.json()
    assert 8 <= len(rows) <= 12
    for row in rows:
        assert row["source_url"].strip()
        assert row["date"]
        assert row["event_type"]
    assert first.json() == second.json()