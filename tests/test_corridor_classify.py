"""Corridor pre-classifier tests."""

from __future__ import annotations

from app.signals.classify import (
    classify_corridor,
    has_valid_source_url,
    is_relevant_cameo,
)


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


def test_dubai_city_geocode_is_not_hormuz_evidence() -> None:
    """A broad Gulf bbox must not turn routine Dubai news into Hormuz risk."""
    row = {
        "ActionGeo_Lat": "25.2048",
        "ActionGeo_Long": "55.2708",
        "ActionGeo_FullName": "Dubai, United Arab Emirates",
        "EventCode": "141",
        "SOURCEURL": "https://example.com/dubai-business",
        "Actor1Name": "Dubai company",
        "Actor2Name": "Investor",
    }
    assert classify_corridor(row) is None
    assert is_relevant_cameo("141") is False


def test_ras_al_khaimah_geocode_without_waterway_terms_is_not_hormuz() -> None:
    row = {
        "ActionGeo_Lat": "25.7895",
        "ActionGeo_Long": "55.9432",
        "ActionGeo_FullName": "Ras Al Khaimah, United Arab Emirates",
        "EventCode": "172",
        "SOURCEURL": "https://example.com/local-uae-story",
        "Actor1Name": "United Arab Emirates",
        "Actor2Name": "Local authority",
    }
    assert classify_corridor(row) is None


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


def test_shifted_gdelt_row_without_url_is_not_auditable() -> None:
    assert has_valid_source_url({"SOURCEURL": "112.5"}) is False
    assert has_valid_source_url({"SOURCEURL": "https://example.com/report"}) is True
