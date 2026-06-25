"""Point-in-time integrity guards for backtest replay."""

from __future__ import annotations

from datetime import date
from typing import Any

from app.models.generated import SignalEvent


class LookaheadViolationError(ValueError):
    """Raised when future events would influence a score_date."""


def filter_events_up_to(events: list[SignalEvent], as_of: date) -> list[SignalEvent]:
    """Return only events visible at as_of (inclusive)."""
    return [e for e in events if e.event_date <= as_of]


def assert_events_visible_at(events: list[SignalEvent], as_of: date) -> None:
    """Fail if any event in the list would not be visible at as_of."""
    future = [e for e in events if e.event_date > as_of]
    if future:
        sample = future[0]
        raise LookaheadViolationError(
            f"event {sample.event_id} dated {sample.event_date} exceeds as_of {as_of}"
        )


def assert_no_future_events(events: list[SignalEvent], as_of: date) -> None:
    """Alias for assert_events_visible_at (legacy name used in docs/tests)."""
    assert_events_visible_at(events, as_of)


def events_for_score_date(events: list[SignalEvent], score_date: date) -> list[SignalEvent]:
    """Return PIT-visible events for a score_date and validate the cutoff."""
    visible = filter_events_up_to(events, score_date)
    assert_events_visible_at(visible, score_date)
    return visible


def pit_diagnostics(events: list[SignalEvent], as_of: date) -> dict[str, Any]:
    """Structured proof that only events with event_date <= as_of are visible."""
    visible = filter_events_up_to(events, as_of)
    assert_events_visible_at(visible, as_of)
    excluded = [e for e in events if e.event_date > as_of]
    max_visible = max((e.event_date for e in visible), default=None)
    return {
        "as_of": as_of.isoformat(),
        "total_events_in_cache": len(events),
        "visible_events": len(visible),
        "excluded_future_events": len(excluded),
        "max_visible_event_date": max_visible.isoformat() if max_visible else None,
        "pit_ok": len(excluded) == len(events) - len(visible),
        "sample_visible_event_dates": sorted({e.event_date.isoformat() for e in visible})[-5:],
    }