"""Template-based grounded intelligence briefing generator (no LLM free-narration).

Every claim and figure in the briefing traces directly to per-event calculations
and underlying database records.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from app.models.generated import RiskScore, SignalEvent
from app.signals.score import per_event_contribution

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ContributingFactor:
    event_type: str
    event_date: str
    contribution_pct: float
    goldstein_scale: float
    source_url: str
    snippet: str


@dataclass(frozen=True)
class IntelligenceBriefing:
    corridor: str
    risk_level: str  # LOW | MODERATE | HIGH | CRITICAL
    score: float
    trend: str  # RISING | FALLING | STABLE
    headline: str
    contributing_factors: list[ContributingFactor]
    recommended_posture: str
    generated_at: str


def get_risk_level(score: float) -> str:
    """Map normalized 0-1 score to deterministic risk level."""
    if score >= 0.65:
        return "CRITICAL"
    if score >= 0.35:
        return "HIGH"
    if score >= 0.15:
        return "MODERATE"
    return "LOW"


def get_recommended_posture(risk_level: str) -> str:
    """Map risk level to deterministic operational posture recommendation."""
    postures = {
        "LOW": "Maintain standard procurement schedule. No immediate action required.",
        "MODERATE": "Monitor developments closely. Pre-position alternative supplier contacts.",
        "HIGH": "Activate contingency planning. Evaluate rerouting and SPR drawdown options.",
        "CRITICAL": "Immediate action required. Execute approved mitigation strategy.",
    }
    return postures.get(risk_level, postures["LOW"])


def generate_briefing(
    risk_score: RiskScore,
    events: list[SignalEvent],
) -> IntelligenceBriefing:
    """Generate a fully grounded intelligence briefing for a single corridor's risk score."""
    corridor_key = risk_score.corridor.value
    score_val = risk_score.score
    trend_val = risk_score.trend_7d.value

    from app.signals.config import load_config
    cfg = load_config()

    # Filter events for this corridor on or before score date
    relevant_events = [
        e
        for e in events
        if (
            e.corridor.value == corridor_key
            and e.event_date <= risk_score.score_date
            and e.confidence >= cfg.scoring.confidence_threshold
        )
    ]

    level = get_risk_level(score_val)
    posture = get_recommended_posture(level)

    # Compute per-event contributions
    contrib_list: list[tuple[SignalEvent, float]] = []
    for e in relevant_events:
        c = per_event_contribution(
            e,
            score_date=risk_score.score_date,
            config=cfg.scoring,
            event_type_weights=cfg.event_type_weights,
        )
        if c > 0:
            contrib_list.append((e, c))

    contrib_list.sort(key=lambda item: item[1], reverse=True)
    top_5 = contrib_list[:5]

    total_top_contrib = sum(c for _, c in top_5)

    factors: list[ContributingFactor] = []
    for e, c in top_5:
        pct = (c / total_top_contrib * 100.0) if total_top_contrib > 0 else 0.0
        factors.append(
            ContributingFactor(
                event_type=e.event_type.value,
                event_date=e.event_date.isoformat(),
                contribution_pct=round(pct, 1),
                goldstein_scale=e.goldstein_scale,
                source_url=str(e.source_url),
                snippet=e.raw_text_snippet[:120],
            )
        )

    # Construct headline template
    if factors:
        top_f = factors[0]
        headline = (
            f"{corridor_key} corridor risk is {level} at {score_val:.0%}, {trend_val} over 7 days. "
            f"Primary driver: {top_f.event_type} event on {top_f.event_date} "
            f"(Goldstein {top_f.goldstein_scale:+.1f}, contributing "
            f"{top_f.contribution_pct:.0f}% of top signals)."
        )
    else:
        headline = (
            f"{corridor_key} corridor risk is {level} at {score_val:.0%}, {trend_val} over 7 days. "
            "No active threat signals detected."
        )

    return IntelligenceBriefing(
        corridor=corridor_key,
        risk_level=level,
        score=round(score_val, 4),
        trend=trend_val,
        headline=headline,
        contributing_factors=factors,
        recommended_posture=posture,
        generated_at=(
            datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        ),
    )


def generate_all_briefings(
    scores: list[RiskScore],
    events: list[SignalEvent],
) -> list[IntelligenceBriefing]:
    """Generate briefings for all corridors present in scores."""
    briefings: list[IntelligenceBriefing] = []
    for s in scores:
        briefings.append(generate_briefing(s, events))
    return briefings
