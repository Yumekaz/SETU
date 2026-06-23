"""Determinism tests for Phase 1 pipeline."""

from __future__ import annotations

import json

import pytest
from app.signals.pipeline import run_pipeline


@pytest.fixture(autouse=True)
def _rules_mode(monkeypatch):
    monkeypatch.setenv("SETU_EXTRACTOR_MODE", "rules")


def test_pipeline_produces_identical_output_on_rerun(tmp_path, monkeypatch):
    db_file = tmp_path / "determinism.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")

    first = run_pipeline(source="cache", reset=True)
    second = run_pipeline(source="cache", reset=True)

    first_payload = {
        "events": [e.model_dump(mode="json") for e in first.events],
        "scores": [s.model_dump(mode="json") for s in first.scores],
    }
    second_payload = {
        "events": [e.model_dump(mode="json") for e in second.events],
        "scores": [s.model_dump(mode="json") for s in second.scores],
    }
    assert json.dumps(first_payload, sort_keys=True) == json.dumps(second_payload, sort_keys=True)
