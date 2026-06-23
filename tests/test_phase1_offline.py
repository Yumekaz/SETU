"""Offline cache-only pipeline tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from app.main import app
from app.signals.pipeline import run_pipeline
from fastapi.testclient import TestClient

SCRATCH = Path("/tmp/grok-goal-7dbdddf7e201/implementer")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "offline.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:////{db_file}")
    monkeypatch.setenv("SETU_EXTRACTOR_MODE", "rules")
    return TestClient(app)


def _full_api_snapshot(client: TestClient) -> dict:
    return {
        "post_pipeline_run": client.post(
            "/api/pipeline/run", json={"source": "cache"}
        ).json(),
        "get_signals": client.get("/api/signals").json(),
        "get_risk_scores": client.get("/api/risk-scores").json(),
        "get_risk_scores_latest": client.get("/api/risk-scores/latest").json(),
    }


def test_run_pipeline_cache_mode_never_calls_http(tmp_path, monkeypatch):
    import httpx

    db_file = tmp_path / "offline-pipeline.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:////{db_file}")
    monkeypatch.setenv("SETU_EXTRACTOR_MODE", "rules")

    def _block_http(*_args, **_kwargs):
        raise AssertionError("HTTP call attempted during cache-only pipeline")

    monkeypatch.setattr(httpx, "get", _block_http)
    monkeypatch.setattr(httpx.Client, "get", _block_http)
    result = run_pipeline(source="cache", reset=True)
    assert result.stats.input_rows >= 50


def test_api_pipeline_and_reads_are_offline_and_deterministic(client) -> None:
    first = _full_api_snapshot(client)
    assert first["post_pipeline_run"]["stats"]["input_rows"] >= 50
    assert len(first["get_signals"]) > 0
    assert len(first["get_risk_scores"]) >= 3
    assert len(first["get_risk_scores_latest"]) >= 3
    assert {item["corridor"] for item in first["get_risk_scores_latest"]} >= {
        "HORMUZ",
        "BAB_EL_MANDEB",
        "MALACCA",
    }

    second = _full_api_snapshot(client)

    SCRATCH.mkdir(parents=True, exist_ok=True)
    (SCRATCH / "api_responses.log").write_text(
        json.dumps({"first_run": first, "second_run": second}, indent=2),
        encoding="utf-8",
    )

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
