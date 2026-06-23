"""Offline cache-only pipeline tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.signals.pipeline import run_pipeline

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = Path("/tmp/grok-goal-7dbdddf7e201/implementer")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "offline.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("SETU_EXTRACTOR_MODE", "rules")
    return TestClient(app)


def test_run_pipeline_cache_mode_never_calls_http(tmp_path, monkeypatch):
    import httpx

    db_file = tmp_path / "offline-pipeline.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("SETU_EXTRACTOR_MODE", "rules")

    def _block_http(*_args, **_kwargs):
        raise AssertionError("HTTP call attempted during cache-only pipeline")

    monkeypatch.setattr(httpx, "get", _block_http)
    monkeypatch.setattr(httpx.Client, "get", _block_http)
    result = run_pipeline(source="cache", reset=True)
    assert result.stats.input_rows >= 50


def test_api_pipeline_and_reads(client) -> None:
    run_resp = client.post("/api/pipeline/run", json={"source": "cache"})
    assert run_resp.status_code == 200
    run_body = run_resp.json()
    assert run_body["stats"]["input_rows"] >= 50

    signals = client.get("/api/signals").json()
    scores = client.get("/api/risk-scores").json()
    latest = client.get("/api/risk-scores/latest").json()

    assert len(signals) > 0
    assert len(scores) >= 3
    assert len(latest) >= 3
    assert {item["corridor"] for item in latest} >= {"HORMUZ", "BAB_EL_MANDEB", "MALACCA"}

    SCRATCH.mkdir(parents=True, exist_ok=True)
    (SCRATCH / "api_responses.log").write_text(
        json.dumps({"run": run_body, "signals_count": len(signals), "latest": latest}, indent=2),
        encoding="utf-8",
    )

    run_resp_2 = client.post("/api/pipeline/run", json={"source": "cache"})
    assert run_resp_2.json()["scores"] == run_body["scores"]