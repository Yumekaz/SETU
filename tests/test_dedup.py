"""Dedup tests."""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

from app.models.generated import SignalEvent
from app.signals.dedup import deduplicate_events


def _event(**overrides) -> SignalEvent:
    base = {
        "event_id": str(uuid4()),
        "corridor": "HORMUZ",
        "event_type": "MILITARY",
        "severity": 0.8,
        "goldstein_scale": -7.0,
        "confidence": 0.9,
        "event_date": date(2026, 3, 11),
        "ingested_at": datetime(2026, 6, 23, 12, 0, 0, tzinfo=timezone.utc),
        "source_url": "https://example.com/1",
        "raw_text_snippet": "Strait of Hormuz military incident near transit lane",
    }
    base.update(overrides)
    return SignalEvent.model_validate(base)


def test_dedup_drops_near_duplicate() -> None:
    a = _event(confidence=0.9)
    b = _event(
        event_id=str(uuid4()),
        confidence=0.7,
        raw_text_snippet="Strait of Hormuz military incident near transit lane",
    )
    kept, dropped = deduplicate_events([a, b])
    assert len(kept) == 1
    assert len(dropped) == 1
    assert kept[0].confidence == 0.9