"""Structural checks for Phase 0 deliverables (real files, no mocks)."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HORMUZ_CSV = ROOT / "data" / "hormuz_2026_timeline.csv"
SCHEMAS_DIR = ROOT / "schemas"
SAMPLES_DIR = ROOT / "data" / "samples"
FIXTURES_DIR = ROOT / "data" / "fixtures"

EXPECTED_SAMPLES = {
    "gdelt_events_sample.json",
    "ofac_sdn_sample.json",
    "fred_brent_sample.json",
    "eia_brent_sample.json",
    "eia_india_imports_sample.json",
}

EXPECTED_FIXTURES = {
    "signal_events.json",
    "risk_scores.json",
    "cascade_results.json",
    "graph_nodes.json",
    "graph_edges.json",
    "recommendations.json",
}


def test_hormuz_timeline_has_eight_to_twelve_cited_rows() -> None:
    """Phase 5: 8–12 cited timeline rows for backtest ground truth."""
    assert HORMUZ_CSV.exists()
    with HORMUZ_CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert 8 <= len(rows) <= 12, f"expected 8-12 data rows, got {len(rows)}"
    for i, row in enumerate(rows, start=1):
        assert row.get("source_url", "").startswith("http"), f"row {i} missing source_url"
        assert row.get("date"), f"row {i} missing date"


def test_schemas_dir_has_ten_files() -> None:
    schemas = sorted(p.name for p in SCHEMAS_DIR.glob("*.json"))
    assert len(schemas) == 10


def test_samples_and_fixtures_present() -> None:
    sample_names = {p.name for p in SAMPLES_DIR.glob("*.json")}
    fixture_names = {p.name for p in FIXTURES_DIR.glob("*.json")}
    assert EXPECTED_SAMPLES <= sample_names
    assert EXPECTED_FIXTURES <= fixture_names


def test_samples_contain_no_raw_api_keys() -> None:
    """Committed samples must not embed live API keys (only REDACTED placeholders)."""
    key_pattern = re.compile(r'"(?:api_key|apikey)"\s*:\s*"(?!REDACTED")[^"]{8,}"')
    for path in SAMPLES_DIR.glob("*.json"):
        text = path.read_text(encoding="utf-8")
        assert not key_pattern.search(text), f"{path.name} contains a non-redacted API key"
        if "api_key" in text:
            data = json.loads(text)
            raw = json.dumps(data)
            assert "REDACTED" in raw or '"api_key"' not in raw, path.name
