"""Corridor pre-classifier tests."""

from __future__ import annotations

from app.signals.classify import classify_corridor, is_relevant_cameo


def test_hormuz_bbox_classification() -> None:
    row = {
        "ActionGeo_Lat": "26.5",
        "ActionGeo_Long": "56.5",
        "ActionGeo_FullName": "Strait of Hormuz",
        "EventCode": "190",
        "SOURCEURL": "https://example.com/a",
        "Actor1Name": "Iran",
        "Actor2Name": "Shipping",
    }
    assert classify_corridor(row) == "HORMUZ"
    assert is_relevant_cameo("190") is True


def test_malacca_keyword_classification() -> None:
    row = {
        "ActionGeo_Lat": "",
        "ActionGeo_Long": "",
        "ActionGeo_FullName": "Singapore Strait, Singapore",
        "EventCode": "141",
        "SOURCEURL": "https://example.com/b",
        "Actor1Name": "Malaysia",
        "Actor2Name": "Navy",
    }
    assert classify_corridor(row) == "MALACCA"