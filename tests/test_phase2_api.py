"""Phase 2 cascade API integration tests."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from app.database import get_db_path, init_db
from app.main import app
from fastapi.testclient import TestClient

SCRATCH = Path("/tmp/grok-goal-673d97933c7a/implementer")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "phase2.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:////{db_file}")
    monkeypatch.setenv("SETU_MC_N_SIMULATIONS", "100")
    monkeypatch.setenv("SETU_EXTRACTOR_MODE", "rules")
    init_db()
    return TestClient(app)


def test_get_graph_returns_cited_network(client: TestClient) -> None:
    response = client.get("/api/graph")
    assert response.status_code == 200
    data = response.json()
    node_ids = {n["node_id"] for n in data["nodes"]}
    assert "corridor_hormuz" in node_ids
    assert data["sources"]
    assert len(data["edges"]) >= 10


def test_cascade_simulate_persists_and_latest_reflects_result(client: TestClient) -> None:
    post = client.post(
        "/api/cascade/simulate",
        json={"corridor": "HORMUZ", "seed": 42, "n_simulations": 100},
    )
    assert post.status_code == 200
    created = post.json()
    assert created["corridor"] == "HORMUZ"
    assert created["price_impact_pct"]["p10"] <= created["price_impact_pct"]["p50"]

    latest = client.get("/api/cascade/results/latest")
    assert latest.status_code == 200
    latest_rows = latest.json()
    assert any(r["scenario_id"] == created["scenario_id"] for r in latest_rows)

    all_results = client.get("/api/cascade/results")
    assert all_results.status_code == 200
    assert len(all_results.json()) >= 1

    with sqlite3.connect(str(get_db_path())) as conn:
        count = conn.execute("SELECT COUNT(*) FROM cascade_results").fetchone()[0]
    assert count >= 1


def test_cascade_simulate_from_risk_uses_phase1_scores(client: TestClient) -> None:
    pipeline = client.post("/api/pipeline/run", json={"source": "cache"})
    assert pipeline.status_code == 200

    response = client.post("/api/cascade/simulate/from-risk", params={"seed": 42})
    assert response.status_code == 200
    data = response.json()
    assert "trigger_risk_score" in data
    assert data["trigger_risk_score"]["corridor"] == data["corridor"]
    assert data["corridor"] in {"HORMUZ", "BAB_EL_MANDEB", "MALACCA"}


def test_cascade_simulate_is_repeatable(client: TestClient) -> None:
    body = {"corridor": "MALACCA", "seed": 7, "n_simulations": 100}
    first = client.post("/api/cascade/simulate", json=body).json()
    second = client.post("/api/cascade/simulate", json=body).json()
    assert first["price_impact_pct"] == second["price_impact_pct"]


def test_cascade_results_latest_returns_one_per_corridor(client: TestClient) -> None:
    for seed in (42, 43):
        resp = client.post(
            "/api/cascade/simulate",
            json={"corridor": "HORMUZ", "seed": seed, "n_simulations": 50},
        )
        assert resp.status_code == 200

    latest = client.get("/api/cascade/results/latest").json()
    hormuz_rows = [r for r in latest if r["corridor"] == "HORMUZ"]
    assert len(hormuz_rows) == 1
    corridors = [r["corridor"] for r in latest]
    assert len(corridors) == len(set(corridors))


def test_simulate_other_corridor_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/cascade/simulate",
        json={"corridor": "OTHER", "seed": 42, "n_simulations": 10},
    )
    assert response.status_code == 422
    assert "not simulatable" in response.json()["detail"]


def test_verification_cascade_api_writes_scratch_evidence(client: TestClient) -> None:
    """Verification plan step 5: full API sequence + sqlite inspection to scratch."""
    graph_resp = client.get("/api/graph")
    pipeline_resp = client.post("/api/pipeline/run", json={"source": "cache"})
    simulate_resp = client.post(
        "/api/cascade/simulate",
        json={"corridor": "HORMUZ", "seed": 42, "n_simulations": 100},
    )
    from_risk_resp = client.post("/api/cascade/simulate/from-risk", params={"seed": 99})
    results_resp = client.get("/api/cascade/results")
    latest_resp = client.get("/api/cascade/results/latest")

    with sqlite3.connect(str(get_db_path())) as conn:
        sqlite_rows = conn.execute(
            "SELECT scenario_id, corridor, seed FROM cascade_results ORDER BY computed_at DESC"
        ).fetchall()

    evidence = {
        "get_graph": {"status": graph_resp.status_code, "body": graph_resp.json()},
        "post_pipeline_run": {"status": pipeline_resp.status_code},
        "post_cascade_simulate": {
            "status": simulate_resp.status_code,
            "body": simulate_resp.json(),
        },
        "post_cascade_simulate_from_risk": {
            "status": from_risk_resp.status_code,
            "body": from_risk_resp.json(),
        },
        "get_cascade_results": {
            "status": results_resp.status_code,
            "body": results_resp.json(),
        },
        "get_cascade_results_latest": {
            "status": latest_resp.status_code,
            "body": latest_resp.json(),
        },
        "sqlite_cascade_results": [
            {"scenario_id": r[0], "corridor": r[1], "seed": r[2]} for r in sqlite_rows
        ],
    }

    SCRATCH.mkdir(parents=True, exist_ok=True)
    (SCRATCH / "cascade_api.log").write_text(json.dumps(evidence, indent=2), encoding="utf-8")

    assert graph_resp.status_code == 200
    assert simulate_resp.status_code == 200
    assert from_risk_resp.status_code == 200
    assert results_resp.status_code == 200
    assert latest_resp.status_code == 200
    assert len(sqlite_rows) >= 1
    latest_body = latest_resp.json()
    latest_corridors = [r["corridor"] for r in latest_body]
    assert len(latest_corridors) == len(set(latest_corridors))
    hormuz_latest = [r for r in latest_body if r["corridor"] == "HORMUZ"]
    assert len(hormuz_latest) == 1
    latest_ids = {r["scenario_id"] for r in latest_body}
    sim_id = simulate_resp.json()["scenario_id"]
    risk_id = from_risk_resp.json()["scenario_id"]
    assert sim_id in latest_ids or risk_id in latest_ids
