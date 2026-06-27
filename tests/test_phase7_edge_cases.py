"""Phase 7 edge-case gap tests and unrehearsed BAB_EL_MANDEB flow."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from app.main import app
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "phase7.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:////{db_file}")
    monkeypatch.setenv("SETU_MC_N_SIMULATIONS", "50")
    monkeypatch.setenv("SETU_EXTRACTOR_MODE", "rules")
    from app.database import init_db

    init_db()
    return TestClient(app)


def _assert_percentile_band_ordered(band: dict) -> None:
    p10, p50, p90 = band["p10"], band["p50"], band["p90"]
    assert p10 <= p50 <= p90


def _run_bab_el_mandeb_flow(client: TestClient) -> dict:
    pipe = client.post("/api/pipeline/run", json={"source": "cache"})
    assert pipe.status_code == 200
    cascade = client.post(
        "/api/cascade/simulate",
        json={"corridor": "BAB_EL_MANDEB", "n_simulations": 50},
    )
    assert cascade.status_code == 200
    body = cascade.json()
    assert body["corridor"] == "BAB_EL_MANDEB"
    assert body.get("scenario_id")
    _assert_percentile_band_ordered(body["price_impact_pct"])
    fc = client.post("/api/forecast/run")
    assert fc.status_code == 200
    rec = client.post("/api/recommendations/run?force=true")
    assert rec.status_code == 200
    rec_body = rec.json()
    assert len(rec_body.get("options", [])) >= 1
    return {"cascade": body, "recommendation": rec_body}


def test_health_phase8(client: TestClient) -> None:
    assert client.get("/health").json() == {
        "status": "ok",
        "version": "1.0.0",
        "phase": 8,
    }


def test_unrehearsed_bab_el_mandeb_cascade_and_recs(client: TestClient) -> None:
    first = _run_bab_el_mandeb_flow(client)
    second = _run_bab_el_mandeb_flow(client)
    assert first["cascade"]["corridor"] == second["cascade"]["corridor"]
    assert len(first["recommendation"]["options"]) >= 1
    assert len(second["recommendation"]["options"]) >= 1


def test_recommendation_carries_inputs_as_of(client: TestClient) -> None:
    client.post("/api/pipeline/run", json={"source": "cache"})
    client.post(
        "/api/cascade/simulate",
        json={"corridor": "MALACCA", "n_simulations": 50},
    )
    client.post("/api/forecast/run")
    rec = client.post("/api/recommendations/run?force=true")
    assert rec.status_code == 200
    body = rec.json()
    assert "inputs_as_of" in body
    assert body["inputs_as_of"]
    assert "source_cascade_id" in body


def test_ingested_at_stored_as_utc() -> None:
    from app.signals.extract import extract_signal

    row = {
        "GLOBALEVENTID": "utc-test",
        "SQLDATE": "20260311",
        "EventCode": "190",
        "GoldsteinScale": "-8.0",
        "ActionGeo_FullName": "Strait of Hormuz, Iran (general), Iran",
        "ActionGeo_Lat": "26.5",
        "ActionGeo_Long": "56.5",
        "Actor1Name": "Iran",
        "Actor2Name": "Tanker",
        "SOURCEURL": "https://example.com/hormuz-event",
    }
    ingested = datetime(2026, 6, 23, 12, 0, 0, tzinfo=timezone.utc)
    result = extract_signal(row, ingested_at=ingested)
    assert result.status == "accepted"
    assert result.event is not None
    assert result.event.ingested_at.tzinfo is not None
    assert result.event.ingested_at.utcoffset() == timezone.utc.utcoffset(
        result.event.ingested_at
    )


def test_backtest_results_documents_n1_limitation() -> None:
    text = (ROOT / "docs" / "backtest_results.md").read_text(encoding="utf-8")
    assert "N=1" in text or "one real crisis" in text.lower()
    assert "limitation" in text.lower() or "Limitations" in text