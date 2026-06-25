"""Phase 4 recommendations API integration tests."""

from __future__ import annotations

import json
import sqlite3

import pytest
from app.database import get_db_path, init_db
from app.main import app
from app.models.generated import CascadeResult, Status
from app.orchestrator.repository import count_recommendations
from app.simulation.repository import insert_cascade_result
from fastapi.testclient import TestClient

ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "phase4.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:////{db_file}")
    monkeypatch.setenv("SETU_MC_N_SIMULATIONS", "50")
    monkeypatch.setenv("SETU_EXTRACTOR_MODE", "rules")
    init_db()
    return TestClient(app)


def _seed_cascade(client: TestClient) -> CascadeResult:
    rows = json.loads((ROOT / "data/fixtures/cascade_results.json").read_text())
    cascade = CascadeResult.model_validate(rows[0])
    with sqlite3.connect(str(get_db_path())) as conn:
        insert_cascade_result(conn, cascade, seed=42)
        conn.commit()
    return cascade


def test_recommendations_from_cascade_and_approve(client: TestClient) -> None:
    cascade = _seed_cascade(client)
    gen = client.post(
        "/api/recommendations/generate/from-cascade",
        params={"scenario_id": str(cascade.scenario_id)},
    )
    assert gen.status_code == 200
    body = gen.json()
    assert body["status"] == Status.pending_approval.value
    assert body["source_cascade_id"] == str(cascade.scenario_id)
    assert "inputs_as_of" in body
    assert len(body["options"]) >= 2
    assert any(o["is_pareto_optimal"] for o in body["options"])

    rec_id = body["recommendation_id"]
    approve = client.post(
        f"/api/recommendations/{rec_id}/approve",
        json={"operator_note": "Approved for demo"},
    )
    assert approve.status_code == 200
    assert approve.json()["status"] == Status.approved.value


def test_hysteresis_blocks_second_run(client: TestClient) -> None:
    cascade = _seed_cascade(client)
    first = client.post(
        "/api/recommendations/generate/from-cascade",
        params={"scenario_id": str(cascade.scenario_id)},
    )
    assert first.status_code == 200
    second = client.post(
        "/api/recommendations/generate/from-cascade",
        params={"scenario_id": str(cascade.scenario_id)},
    )
    assert second.status_code == 409


def test_force_allows_second_run_append_only(client: TestClient) -> None:
    cascade = _seed_cascade(client)
    client.post(
        "/api/recommendations/generate/from-cascade",
        params={"scenario_id": str(cascade.scenario_id)},
    )
    second = client.post(
        "/api/recommendations/generate/from-cascade",
        params={"scenario_id": str(cascade.scenario_id), "force": True},
    )
    assert second.status_code == 200
    assert count_recommendations() == 2


def test_reject_invalid_status(client: TestClient) -> None:
    cascade = _seed_cascade(client)
    gen = client.post(
        "/api/recommendations/generate/from-cascade",
        params={"scenario_id": str(cascade.scenario_id)},
    )
    rec_id = gen.json()["recommendation_id"]
    client.post(
        f"/api/recommendations/{rec_id}/approve",
        json={"operator_note": "ok"},
    )
    reject = client.post(
        f"/api/recommendations/{rec_id}/reject",
        json={"operator_note": "too late"},
    )
    assert reject.status_code == 422


def test_list_latest_after_generate(client: TestClient) -> None:
    cascade = _seed_cascade(client)
    client.post(
        "/api/recommendations/generate/from-cascade",
        params={"scenario_id": str(cascade.scenario_id)},
    )
    latest = client.get("/api/recommendations/latest")
    assert latest.status_code == 200
    assert len(latest.json()) == 1
