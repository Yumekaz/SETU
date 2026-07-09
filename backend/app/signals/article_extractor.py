"""Deterministic, auditable extraction of risk metadata from article text."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timezone

from app.signals.config import AppConfig


@dataclass(frozen=True)
class ArticleSignalMetadata:
    corridor: str
    event_type: str
    cameo_code: str
    severity: float
    goldstein_scale: float
    confidence: float
    event_date: date
    evidence_terms: tuple[str, ...]


EVENT_PATTERNS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "MILITARY",
        "190",
        (
            "missile",
            "airstrike",
            "strike",
            "strikes",
            "attack",
            "attacked",
            "projectile",
            "drone",
            "warship",
            "navy",
            "military",
            "conflict",
            "blockade",
        ),
    ),
    (
        "SANCTION",
        "160",
        ("sanction", "embargo", "export ban", "designation", "trade restriction"),
    ),
    (
        "PIRACY",
        "090",
        ("piracy", "pirate", "hijack", "hijacked", "armed robbery", "vessel seized"),
    ),
    (
        "INFRASTRUCTURE",
        "080",
        (
            "port closure",
            "pipeline outage",
            "terminal outage",
            "shipping disruption",
            "damaged port",
            "canal closure",
        ),
    ),
    ("ACCIDENT", "070", ("collision", "explosion", "oil spill", "fire", "grounding", "accident")),
    (
        "DIPLOMATIC",
        "040",
        (
            "ceasefire",
            "negotiation",
            "diplomatic",
            "talks",
            "agreement",
            "warning",
            "tension",
        ),
    ),
)

ESCALATION_TERMS = {
    "blockade",
    "airstrike",
    "strike",
    "strikes",
    "missile",
    "attack",
    "attacked",
    "projectile",
    "warship",
    "hijacked",
    "vessel seized",
    "port closure",
    "canal closure",
    "explosion",
}
POSITIVE_DIPLOMACY_TERMS = {"ceasefire", "agreement", "negotiation", "talks"}


def _contains_term(text: str, term: str) -> bool:
    return re.search(rf"\b{re.escape(term)}\b", text) is not None


def _parse_article_date(value: str | None) -> date:
    if not value:
        return datetime.now(timezone.utc).date()
    normalized = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).date()
    except ValueError:
        try:
            return date.fromisoformat(normalized[:10])
        except ValueError:
            return datetime.now(timezone.utc).date()


def extract_article_metadata(
    *,
    title: str,
    content_text: str,
    published_at_iso: str | None,
    config: AppConfig,
) -> ArticleSignalMetadata | None:
    """Return grounded metadata only when corridor and event evidence are present."""
    title_text = title.lower()
    combined = f"{title} {content_text}".lower()

    corridor_hits: list[tuple[str, list[str]]] = []
    for corridor, spec in config.corridors.items():
        hits = [term for term in spec.keywords if _contains_term(combined, term)]
        if hits:
            corridor_hits.append((corridor, hits))
    if not corridor_hits:
        return None
    corridor, matched_corridor_terms = max(corridor_hits, key=lambda item: len(item[1]))

    event_hits: list[tuple[str, str, list[str]]] = []
    for event_type, cameo_code, patterns in EVENT_PATTERNS:
        hits = [term for term in patterns if _contains_term(combined, term)]
        if hits:
            event_hits.append((event_type, cameo_code, hits))
    if not event_hits:
        return None
    event_type, cameo_code, matched_event_terms = max(event_hits, key=lambda item: len(item[2]))

    unique_evidence = tuple(dict.fromkeys(matched_corridor_terms + matched_event_terms))
    escalation_count = sum(term in ESCALATION_TERMS for term in matched_event_terms)
    severity = min(0.35 + 0.08 * len(matched_event_terms) + 0.12 * escalation_count, 0.95)

    title_evidence = sum(_contains_term(title_text, term) for term in unique_evidence)
    confidence = min(
        0.52
        + 0.05 * min(len(matched_corridor_terms), 3)
        + 0.06 * min(len(matched_event_terms), 3)
        + 0.03 * min(title_evidence, 2),
        0.92,
    )

    positive_diplomacy = event_type == "DIPLOMATIC" and any(
        term in POSITIVE_DIPLOMACY_TERMS for term in matched_event_terms
    )
    goldstein = severity * (5.0 if positive_diplomacy else -10.0)

    return ArticleSignalMetadata(
        corridor=corridor,
        event_type=event_type,
        cameo_code=cameo_code,
        severity=round(severity, 3),
        goldstein_scale=round(goldstein, 2),
        confidence=round(confidence, 3),
        event_date=_parse_article_date(published_at_iso),
        evidence_terms=unique_evidence[:8],
    )
