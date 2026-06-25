"""Point-in-time integrity guards for backtest replay."""

from __future__ import annotations

from datetime import date

from app.models.generated import SignalEvent


class LookaheadViolationError(ValueError):
    """Raised when future events would influence a score_date."""


def filter_events_up_to(events: list[SignalEvent], as_of: date) -> list[SignalEvent]:
    """Return only events visible at as_of (inclusive)."""
    return [e for e in events if e.event_date <= as_of]


def assert_no_future_events(events: list[SignalEvent], score_date: date) -> None:
    """Fail if any event used would violate PIT cutoff."""
    future = [e for e in events if e.event_date > score_date]
    if future:
        sample = future[0]
        raise LookaheadViolationError(
            f"event {sample.event_id} dated {sample.event_date} exceeds score_date {score_date}"
        )
