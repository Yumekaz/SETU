"""Extraction and confidence-gate tests."""

from __future__ import annotations

import os

from app.models.generated import SignalEvent
from app.signals.extract import extract_signal


def _sample_row() -> dict[str, str]:
    return {
        "GLOBALEVENTID": "test-123",
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


def test_rules_extractor_produces_valid_signal_event() -> None:
    os.environ["SETU_EXTRACTOR_MODE"] = "rules"
    result = extract_signal(_sample_row())
    assert result.status == "accepted"
    assert result.event is not None
    SignalEvent.model_validate(result.event.model_dump(mode="json"))


def test_low_confidence_unknown_type_is_rejected() -> None:
    os.environ["SETU_EXTRACTOR_MODE"] = "rules"
    row = _sample_row()
    row["EventCode"] = "999"  # not in CAMEO allowlist
    result = extract_signal(row)
    assert result.status == "rejected"
    assert result.reason == "ingest_filter"


def test_non_english_source_rejected_by_ingest_filter() -> None:
    os.environ["SETU_EXTRACTOR_MODE"] = "rules"
    row = _sample_row()
    row["ActionGeo_FullName"] = "مضيق هرمز"
    row["Actor1Name"] = "إيران"
    row["SOURCEURL"] = "https://example.com/ar"
    result = extract_signal(row)
    assert result.status == "rejected"
    assert result.reason == "ingest_filter"
