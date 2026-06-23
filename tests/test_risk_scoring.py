"""Deterministic risk scoring tests."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from uuid import uuid4

from app.models.generated import SignalEvent, Trend7d
from app.signals.score import build_risk_scores, compute_trend_7d

ROOT_DATE = date(2026, 6, 23)


def _event(severity: float, *, days_ago: int = 0) -> SignalEvent:
    event_date = date.fromordinal(ROOT_DATE.toordinal() - days_ago)
    return SignalEvent.model_validate(
        {
            "event_id": str(uuid4()),
            "corridor": "HORMUZ",
            "event_type": "MILITARY",
            "severity": severity,
            "goldstein_scale": -8.0,
            "confidence": 0.9,
            "event_date": event_date,
            "ingested_at": datetime(2026, 6, 23, 12, 0, 0, tzinfo=timezone.utc),
            "source_url": "https://example.com/x",
            "raw_text_snippet": "Hormuz event",
        }
    )


def test_scores_are_bounded_and_deterministic() -> None:
    events = [_event(0.9), _event(0.5, days_ago=3)]
    first = build_risk_scores(events, score_date=ROOT_DATE)
    second = build_risk_scores(events, score_date=ROOT_DATE)
    assert json.dumps([s.model_dump(mode="json") for s in first]) == json.dumps(
        [s.model_dump(mode="json") for s in second]
    )
    for score in first:
        assert 0.0 <= score.score <= 1.0
        assert score.trend_7d in {Trend7d.rising, Trend7d.falling, Trend7d.stable}


def test_trend_labels() -> None:
    assert compute_trend_7d(0.5, 0.5) == Trend7d.stable
    assert compute_trend_7d(0.6, 0.4) == Trend7d.rising
    assert compute_trend_7d(0.3, 0.5) == Trend7d.falling