"""Tests for grounded XAI intelligence briefing generator and edge cases EC-59 to EC-61."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.models.generated import Corridor, RiskScore, Trend7d  # noqa: E402
from app.signals.briefing import (  # noqa: E402
    generate_all_briefings,
    generate_briefing,
    get_recommended_posture,
    get_risk_level,
)


def test_risk_level_boundaries_ec_61() -> None:
    assert get_risk_level(0.0) == "LOW"
    assert get_risk_level(0.14) == "LOW"
    assert get_risk_level(0.15) == "MODERATE"
    assert get_risk_level(0.34) == "MODERATE"
    assert get_risk_level(0.35) == "HIGH"
    assert get_risk_level(0.64) == "HIGH"
    assert get_risk_level(0.65) == "CRITICAL"
    assert get_risk_level(1.0) == "CRITICAL"


def test_recommended_posture_mapping() -> None:
    assert "standard" in get_recommended_posture("LOW").lower()
    assert "contingency" in get_recommended_posture("HIGH").lower()
    assert "immediate" in get_recommended_posture("CRITICAL").lower()


def test_briefing_with_no_events_ec_59() -> None:
    score = RiskScore(
        corridor=Corridor.hormuz,
        score=0.10,
        score_date=date(2026, 6, 1),
        contributing_event_ids=[],
        trend_7d=Trend7d.stable,
    )
    b = generate_briefing(score, events=[])
    assert b.corridor == "HORMUZ"
    assert b.risk_level == "LOW"
    assert b.score == 0.10
    assert b.contributing_factors == []
    assert "No active threat signals" in b.headline


def test_generate_all_briefings() -> None:
    score1 = RiskScore(
        corridor=Corridor.hormuz,
        score=0.40,
        score_date=date(2026, 6, 1),
        contributing_event_ids=[],
        trend_7d=Trend7d.rising,
    )
    score2 = RiskScore(
        corridor=Corridor.malacca,
        score=0.05,
        score_date=date(2026, 6, 1),
        contributing_event_ids=[],
        trend_7d=Trend7d.stable,
    )
    briefings = generate_all_briefings([score1, score2], events=[])
    assert len(briefings) == 2
    assert briefings[0].risk_level == "HIGH"
    assert briefings[1].risk_level == "LOW"
