"""Fixed prompts for constrained SignalEvent field extraction."""

from __future__ import annotations

EXTRACTION_SYSTEM = (
    "You extract structured fields from geopolitical event snippets. "
    "Return only the requested JSON fields. Do not invent facts."
)


def build_extraction_prompt(*, snippet: str, corridor: str) -> str:
    return (
        f"Corridor (pre-classified): {corridor}\n"
        f"Snippet:\n{snippet}\n\n"
        "Extract corridor, event_type, severity (0-1), confidence (0-1), "
        "and event_date (YYYY-MM-DD) supported by the snippet."
    )