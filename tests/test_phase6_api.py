"""Phase 6 backtest feed + health API tests."""

from __future__ import annotations

import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "phase6.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:////{db_file}")
    monkeypatch.setenv("SETU_MC_N_SIMULATIONS", "50")
    monkeypatch.setenv("SETU_EXTRACTOR_MODE", "rules")
    from app.database import init_db

    init_db()
    return TestClient(app)


def test_health_phase6(client: TestClient) -> None:
    assert client.get("/health").json() == {
        "status": "ok",
        "version": "1.0.0",
        "phase": 8,
    }


def test_backtest_trajectory_full_window(client: TestClient) -> None:
    first = client.get("/api/backtest/trajectory")
    second = client.get("/api/backtest/trajectory")
    assert first.status_code == 200
    body = first.json()
    assert body["corridor"] == "HORMUZ"
    assert body["window_start"] == "2026-02-01"
    assert body["window_end"] == "2026-06-30"
    points = body["points"]
    assert len(points) >= 140
    assert points[0]["date"] == "2026-02-01"
    assert points[-1]["date"] == "2026-06-30"
    assert all(isinstance(p["score"], (int, float)) for p in points)
    assert first.json() == second.json()


def test_default_dashboard_populated(client: TestClient) -> None:
    pipe = client.post("/api/pipeline/run", json={"source": "cache"})
    assert pipe.status_code == 200
    forecasts = client.get("/api/forecast/latest").json()
    if len(forecasts) == 0:
        fc = client.post("/api/forecast/run")
        assert fc.status_code == 200
        forecasts = client.get("/api/forecast/latest").json()
    assert len(forecasts) >= 1
    assert forecasts[0]["trajectory"]
    assert len(forecasts[0]["trajectory"]) >= 1
    scores = client.get("/api/risk-scores/latest").json()
    assert len(scores) >= 3
    corridors = {s["corridor"] for s in scores}
    assert {"HORMUZ", "BAB_EL_MANDEB", "MALACCA"} <= corridors


def _assert_percentile_band_ordered(band: dict) -> None:
    assert "p10" in band
    assert "p50" in band
    assert "p90" in band
    p10, p50, p90 = band["p10"], band["p50"], band["p90"]
    assert isinstance(p10, (int, float))
    assert isinstance(p50, (int, float))
    assert isinstance(p90, (int, float))
    assert p10 <= p50 <= p90


def test_unrehearsed_malacca_cascade_and_recs(client: TestClient) -> None:
    client.post("/api/pipeline/run", json={"source": "cache"})
    client.post("/api/forecast/run")
    cascade = client.post(
        "/api/cascade/simulate",
        json={"corridor": "MALACCA", "n_simulations": 50},
    )
    assert cascade.status_code == 200
    body = cascade.json()
    assert body["corridor"] == "MALACCA"
    assert body.get("scenario_id")
    _assert_percentile_band_ordered(body["price_impact_pct"])
    _assert_percentile_band_ordered(body["refinery_throughput_impact_pct"])
    _assert_percentile_band_ordered(body["spr_days_required"])
    fc_after = client.post("/api/forecast/run")
    assert fc_after.status_code == 200
    rec = client.post("/api/recommendations/run?force=true")
    assert rec.status_code == 200
    rec_body = rec.json()
    assert len(rec_body.get("options", [])) >= 1


def test_backtest_timeline_cited_rows(client: TestClient) -> None:
    first = client.get("/api/backtest/timeline")
    second = client.get("/api/backtest/timeline")
    assert first.status_code == 200
    rows = first.json()
    assert 8 <= len(rows) <= 12
    for row in rows:
        assert row["source_url"].strip()
        assert row["date"]
        assert row["event_type"]
    assert first.json() == second.json()
