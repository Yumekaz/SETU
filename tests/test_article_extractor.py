"""Tests for grounded article-derived signal metadata."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.signals.article_extractor import extract_article_metadata  # noqa: E402
from app.signals.config import load_config  # noqa: E402


def test_extracts_malacca_piracy_from_article_evidence() -> None:
    result = extract_article_metadata(
        title="Tanker hijacked near Strait of Malacca",
        content_text="Authorities reported piracy after an armed robbery near Malaysia.",
        published_at_iso="2026-07-08T09:30:00Z",
        config=load_config(),
    )

    assert result is not None
    assert result.corridor == "MALACCA"
    assert result.event_type == "PIRACY"
    assert result.event_date.isoformat() == "2026-07-08"
    assert result.severity > 0.5
    assert result.goldstein_scale < 0
    assert "hijacked" in result.evidence_terms


def test_rejects_article_without_corridor_evidence() -> None:
    result = extract_article_metadata(
        title="Technology company reports quarterly earnings",
        content_text="Revenue increased during the reporting period.",
        published_at_iso=None,
        config=load_config(),
    )
    assert result is None


def test_positive_diplomacy_has_positive_goldstein() -> None:
    result = extract_article_metadata(
        title="Red Sea ceasefire talks reach agreement",
        content_text="Diplomatic negotiation aims to protect shipping through the Red Sea.",
        published_at_iso="2026-07-09",
        config=load_config(),
    )
    assert result is not None
    assert result.event_type == "DIPLOMATIC"
    assert result.goldstein_scale > 0
