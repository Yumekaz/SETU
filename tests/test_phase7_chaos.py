"""Phase 7 chaos / failure-mode tests on real shipped entry points."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest
from app.main import app
from app.signals.extract import extract_signal
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "phase7_chaos.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:////{db_file}")
    monkeypatch.setenv("SETU_MC_N_SIMULATIONS", "50")
    monkeypatch.setenv("SETU_EXTRACTOR_MODE", "rules")
    from app.database import init_db

    init_db()
    return TestClient(app)


def test_corrupt_graph_returns_422_not_traceback(client: TestClient, tmp_path, monkeypatch) -> None:
    bad = tmp_path / "bad_graph.json"
    bad.write_text("{not valid json", encoding="utf-8")
    monkeypatch.setenv("SETU_GRAPH_PATH", str(bad))
    resp = client.get("/api/graph")
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert "graph load failed" in detail
    assert "Traceback" not in detail


def test_invalid_corridor_returns_422_with_supported_list(client: TestClient) -> None:
    resp = client.post(
        "/api/cascade/simulate",
        json={"corridor": "OTHER", "n_simulations": 50},
    )
    assert resp.status_code == 422
    assert "supported" in resp.json()["detail"].lower() or "OTHER" in resp.json()["detail"]


def test_recommendation_missing_cascade_returns_404(client: TestClient) -> None:
    missing = str(uuid4())
    resp = client.post(
        "/api/recommendations/generate/from-cascade",
        params={"scenario_id": missing},
    )
    assert resp.status_code == 404
    assert "cascade not found" in resp.json()["detail"]


def test_malformed_extraction_batch_rejects_without_crash() -> None:
    os.environ["SETU_EXTRACTOR_MODE"] = "rules"
    bad_row = {"GLOBALEVENTID": "bad", "SQLDATE": "not-a-date"}
    result = extract_signal(bad_row)
    assert result.status == "rejected"


def test_pipeline_run_survives_malformed_batch(client: TestClient, monkeypatch) -> None:
    from app.signals import pipeline as pipeline_mod

    def _bad_rows(_cache_path=None):
        return [{"GLOBALEVENTID": "bad-row", "SQLDATE": "not-a-date"}]

    monkeypatch.setattr(pipeline_mod, "load_backtest_cache", _bad_rows)
    resp = client.post("/api/pipeline/run", json={"source": "cache"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["stats"]["rejected_events"] >= 1
