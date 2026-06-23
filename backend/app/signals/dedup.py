"""Deduplicate SignalEvent records before scoring."""

from __future__ import annotations

from datetime import date, timedelta

from app.models.generated import SignalEvent


def _token_set(text: str) -> set[str]:
    return {token for token in text.lower().split() if len(token) > 2}


def jaccard_similarity(a: str, b: str) -> float:
    set_a = _token_set(a)
    set_b = _token_set(b)
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def _date_window(event_date: date, days: int = 1) -> tuple[date, date]:
    return event_date - timedelta(days=days), event_date + timedelta(days=days)


def is_duplicate(candidate: SignalEvent, existing: SignalEvent, *, similarity_threshold: float = 0.8) -> bool:
    if candidate.corridor != existing.corridor:
        return False
    if candidate.event_type != existing.event_type:
        return False
    start, end = _date_window(candidate.event_date)
    if not (start <= existing.event_date <= end):
        return False
    return jaccard_similarity(candidate.raw_text_snippet, existing.raw_text_snippet) >= similarity_threshold


def deduplicate_events(events: list[SignalEvent]) -> tuple[list[SignalEvent], list[SignalEvent]]:
    """Return (kept, dropped) sorted by confidence descending."""
    sorted_events = sorted(events, key=lambda e: e.confidence, reverse=True)
    kept: list[SignalEvent] = []
    dropped: list[SignalEvent] = []

    for event in sorted_events:
        if any(is_duplicate(event, prior) for prior in kept):
            dropped.append(event)
        else:
            kept.append(event)

    kept.sort(key=lambda e: (e.event_date, str(e.event_id)))
    return kept, dropped