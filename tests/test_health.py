"""Backend health endpoint tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.main import app  # noqa: E402

EXPECTED_SCHEMAS = {
    "cascade_result",
    "corridor",
    "forecast_trajectory_step",
    "graph_edge",
    "graph_node",
    "percentile_band",
    "recommendation",
    "risk_forecast",
    "risk_score",
    "signal_event",
}


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok", "version": "0.6.0", "phase": 5}


def test_contracts_endpoint_serves_schemas(client: TestClient) -> None:
    response = client.get("/api/contracts")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 10
    assert set(data.keys()) == EXPECTED_SCHEMAS
    assert "corridor" in data
    assert "percentile_band" in data
    assert "signal_event" in data
    assert data["signal_event"]["additionalProperties"] is False
    assert data["cascade_result"]["properties"]["price_impact_pct"]["$ref"] == (
        "percentile_band.json"
    )
