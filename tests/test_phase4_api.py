"""Phase 4 recommendations API integration tests."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

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


def test_list_recommendations_history(client: TestClient) -> None:
    cascade = _seed_cascade(client)
    client.post(
        "/api/recommendations/generate/from-cascade",
        params={"scenario_id": str(cascade.scenario_id)},
    )
    history = client.get("/api/recommendations")
    assert history.status_code == 200
    rows = history.json()
    assert len(rows) == 1
    assert rows[0]["source_cascade_id"] == str(cascade.scenario_id)


def test_recommendations_run_resolves_seeded_cascade(client: TestClient) -> None:
    cascade = _seed_cascade(client)
    run = client.post("/api/recommendations/run")
    assert run.status_code == 200
    body = run.json()
    assert body["source_cascade_id"] == str(cascade.scenario_id)
    assert body["status"] == Status.pending_approval.value


def test_expire_stale_pending_on_list(client: TestClient) -> None:
    cascade = _seed_cascade(client)
    gen = client.post(
        "/api/recommendations/generate/from-cascade",
        params={"scenario_id": str(cascade.scenario_id)},
    )
    assert gen.status_code == 200
    rec_id = gen.json()["recommendation_id"]
    with sqlite3.connect(str(get_db_path())) as conn:
        conn.execute(
            """
            UPDATE recommendations
            SET computed_at = datetime('now', '-48 hours')
            WHERE recommendation_id = ?
            """,
            (rec_id,),
        )
        conn.commit()
    listing = client.get("/api/recommendations")
    assert listing.status_code == 200
    match = [r for r in listing.json() if r["recommendation_id"] == rec_id]
    assert len(match) == 1
    assert match[0]["status"] == Status.expired.value
    assert "Expired" in match[0]["operator_note"]


def _legacy_recommendations_payload() -> dict:
    rows = json.loads((ROOT / "data/fixtures/recommendations.json").read_text())
    return rows[0]


def _create_populated_legacy_recommendations_db(db_file: Path) -> str:
    """Create a pre-Phase-4 recommendations table with one pending row."""
    payload = _legacy_recommendations_payload()
    conn = sqlite3.connect(str(db_file))
    conn.execute(
        """
        CREATE TABLE recommendations (
            recommendation_id TEXT PRIMARY KEY,
            trigger_corridor TEXT NOT NULL,
            status TEXT NOT NULL,
            source_cascade_id TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        INSERT INTO recommendations (
            recommendation_id, trigger_corridor, status, source_cascade_id, payload_json
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            payload["recommendation_id"],
            payload["trigger_corridor"],
            payload["status"],
            payload["source_cascade_id"],
            json.dumps(payload),
        ),
    )
    conn.commit()
    conn.close()
    return payload["recommendation_id"]


def test_recommendations_migration_on_populated_legacy_table(
    tmp_path, monkeypatch
) -> None:
    """ALTER succeeds on a legacy table that already has recommendation rows."""
    from app.database import migrate_recommendations_computed_at

    db_file = tmp_path / "legacy_populated.db"
    rec_id = _create_populated_legacy_recommendations_db(db_file)

    conn = sqlite3.connect(str(db_file))
    migrated = migrate_recommendations_computed_at(conn)
    conn.commit()
    cols = {row[1] for row in conn.execute("PRAGMA table_info(recommendations)")}
    computed_at = conn.execute(
        "SELECT computed_at FROM recommendations WHERE recommendation_id = ?",
        (rec_id,),
    ).fetchone()[0]
    conn.close()

    assert migrated is True
    assert "computed_at" in cols
    assert computed_at is not None


def test_init_db_migrates_populated_legacy_recommendations_table(
    tmp_path, monkeypatch
) -> None:
    db_file = tmp_path / "legacy_init.db"
    rec_id = _create_populated_legacy_recommendations_db(db_file)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:////{db_file}")

    init_db()

    with sqlite3.connect(str(db_file)) as conn:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(recommendations)")}
        computed_at = conn.execute(
            "SELECT computed_at FROM recommendations WHERE recommendation_id = ?",
            (rec_id,),
        ).fetchone()[0]
    assert "computed_at" in cols
    assert computed_at is not None


def test_migrated_legacy_db_new_insert_computed_at_and_expire(
    tmp_path, monkeypatch
) -> None:
    """Full migrated write path: legacy table → init_db → new insert → expire."""
    db_file = tmp_path / "legacy_new_insert.db"
    legacy_rec_id = _create_populated_legacy_recommendations_db(db_file)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:////{db_file}")
    monkeypatch.setenv("SETU_MC_N_SIMULATIONS", "50")
    monkeypatch.setenv("SETU_EXTRACTOR_MODE", "rules")
    init_db()

    rows = json.loads((ROOT / "data/fixtures/cascade_results.json").read_text())
    legacy_cascade = CascadeResult.model_validate(rows[0])
    new_cascade = CascadeResult.model_validate(rows[1])
    assert legacy_cascade.corridor != new_cascade.corridor
    with sqlite3.connect(str(get_db_path())) as conn:
        insert_cascade_result(conn, new_cascade, seed=43)
        conn.commit()

    client = TestClient(app)
    gen = client.post(
        "/api/recommendations/generate/from-cascade",
        params={"scenario_id": str(new_cascade.scenario_id)},
    )
    assert gen.status_code == 200
    new_rec_id = gen.json()["recommendation_id"]
    assert new_rec_id != legacy_rec_id

    with sqlite3.connect(str(db_file)) as conn:
        new_computed_at = conn.execute(
            "SELECT computed_at FROM recommendations WHERE recommendation_id = ?",
            (new_rec_id,),
        ).fetchone()[0]
        conn.execute(
            """
            UPDATE recommendations
            SET computed_at = datetime('now', '-48 hours')
            WHERE recommendation_id = ?
            """,
            (new_rec_id,),
        )
        conn.commit()

    assert new_computed_at is not None

    listing = client.get("/api/recommendations")
    assert listing.status_code == 200
    by_id = {r["recommendation_id"]: r for r in listing.json()}
    assert by_id[new_rec_id]["status"] == Status.expired.value
    assert "Expired" in by_id[new_rec_id]["operator_note"]
    assert by_id[legacy_rec_id]["status"] == Status.pending_approval.value
