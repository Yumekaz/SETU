"""Tests for mock fixture generator determinism and structure."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = ROOT / "data" / "fixtures"
SCRIPT = ROOT / "scripts" / "generate_mocks.py"


def _run_generate_mocks() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def _load_fixture(name: str) -> list:
    with (FIXTURES_DIR / f"{name}.json").open() as f:
        return json.load(f)


def test_generate_mocks_is_deterministic() -> None:
    """Running generate_mocks.py twice yields identical fixture bytes."""
    _run_generate_mocks()
    first = {
        p.name: p.read_bytes()
        for p in sorted(FIXTURES_DIR.glob("*.json"))
    }

    _run_generate_mocks()
    second = {
        p.name: p.read_bytes()
        for p in sorted(FIXTURES_DIR.glob("*.json"))
    }

    assert first == second


def test_signal_events_meets_minimum_count() -> None:
    _run_generate_mocks()
    events = _load_fixture("signal_events")
    assert len(events) >= 20


def test_graph_nodes_meets_minimum_count() -> None:
    _run_generate_mocks()
    nodes = _load_fixture("graph_nodes")
    assert len(nodes) >= 10


def test_cascade_percentile_ordering() -> None:
    _run_generate_mocks()
    cascades = _load_fixture("cascade_results")
    assert len(cascades) > 0

    for cascade in cascades:
        for field in (
            "price_impact_pct",
            "refinery_throughput_impact_pct",
            "spr_days_required",
        ):
            band = cascade[field]
            assert band["p10"] <= band["p50"] <= band["p90"], (
                f"{field} ordering violated: {band}"
            )


def test_freeze_date_used_in_fixtures() -> None:
    _run_generate_mocks()
    scores = _load_fixture("risk_scores")
    assert all(s["score_date"] == "2026-06-23" for s in scores)

    events = _load_fixture("signal_events")
    assert all(e["ingested_at"].startswith("2026-06-") for e in events)
