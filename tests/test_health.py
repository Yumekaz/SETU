"""Backend health endpoint tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.main import app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok", "version": "0.1.0", "phase": 0}


def test_contracts_endpoint_serves_schemas(client: TestClient) -> None:
    response = client.get("/api/contracts")
    assert response.status_code == 200
    data = response.json()
    assert "signal_event" in data
    assert "risk_score" in data
    assert "cascade_result" in data
    assert "graph_node" in data
    assert "graph_edge" in data
    assert "recommendation" in data
    assert data["signal_event"]["additionalProperties"] is False