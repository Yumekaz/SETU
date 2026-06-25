"""Backtest lookahead integrity tests."""

from __future__ import annotations

from datetime import date

import pytest
from app.backtest.integrity import (
    LookaheadViolationError,
    assert_no_future_events,
    filter_events_up_to,
)
from app.models.generated import Corridor, SignalEvent


def _event(event_date: date) -> SignalEvent:
    from datetime import datetime, timezone
    from uuid import uuid4

    return SignalEvent(
        event_id=uuid4(),
        corridor=Corridor.hormuz,
        event_type="MILITARY",
        severity=0.8,
        goldstein_scale=5.0,
        confidence=0.9,
        event_date=event_date,
        ingested_at=datetime(2026, 6, 23, 12, 0, 0, tzinfo=timezone.utc),
        source_url="https://example.com/event",
        raw_text_snippet="test event",
    )


def test_filter_events_up_to_excludes_future() -> None:
    events = [_event(date(2026, 2, 1)), _event(date(2026, 3, 15))]
    visible = filter_events_up_to(events, date(2026, 2, 28))
    assert len(visible) == 1
    assert visible[0].event_date == date(2026, 2, 1)


def test_assert_no_future_events_raises() -> None:
    events = [_event(date(2026, 4, 1))]
    with pytest.raises(LookaheadViolationError):
        assert_no_future_events(events, date(2026, 3, 1))
