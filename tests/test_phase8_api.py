"""Phase 8 submission demo path — health and full API walkthrough."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_file = tmp_path / "phase8.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:////{db_file}")
    monkeypatch.setenv("SETU_MC_N_SIMULATIONS", "50")
    monkeypatch.setenv("SETU_EXTRACTOR_MODE", "rules")
    import sys

    sys.path.insert(0, str(ROOT / "backend"))
    sys.path.insert(0, str(ROOT))
    from app.database import init_db
    from app.main import app

    init_db()
    return TestClient(app)


def test_health_phase8_submission_freeze(client: TestClient) -> None:
    assert client.get("/health").json() == {
        "status": "ok",
        "version": "1.0.0",
        "phase": 8,
    }


def test_demo_api_path_pipeline_to_recommendations(client: TestClient) -> None:
    """Mirrors live demo: pipeline → cascade → forecast → recommendations."""
    pipe = client.post("/api/pipeline/run", json={"source": "cache"})
    assert pipe.status_code == 200

    scores = client.get("/api/risk-scores/latest")
    assert scores.status_code == 200
    assert len(scores.json()) >= 3

    cascade = client.post(
        "/api/cascade/simulate",
        json={"corridor": "MALACCA", "n_simulations": 50},
    )
    assert cascade.status_code == 200
    body = cascade.json()
    assert body["corridor"] == "MALACCA"
    assert "price_impact_pct" in body
    assert "p50" in body["price_impact_pct"]

    forecast = client.post("/api/forecast/run")
    assert forecast.status_code == 200
    assert len(forecast.json()) >= 1

    rec = client.post("/api/recommendations/run?force=true")
    assert rec.status_code == 200
    assert len(rec.json().get("options", [])) >= 1