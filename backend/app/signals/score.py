"""Deterministic per-corridor risk scoring and 7-day trend (LLM never scores)."""

from __future__ import annotations

import math
from datetime import date, timedelta

from app.models.generated import Corridor, RiskScore, SignalEvent, Trend7d
from app.signals.config import AppConfig, ScoringConfig, load_config

CORRIDOR_ORDER = (
    Corridor.hormuz,
    Corridor.bab_el_mandeb,
    Corridor.malacca,
)


def _event_type_weight(event_type: str, config: AppConfig) -> float:
    return config.event_type_weights.get(event_type, config.event_type_weights.get("UNKNOWN", 0.3))


def per_event_contribution(
    event: SignalEvent,
    *,
    score_date: date,
    config: ScoringConfig,
    event_type_weights: dict[str, float],
) -> float:
    """Weighted contribution with recency decay; capped per event."""
    days_since = max((score_date - event.event_date).days, 0)
    recency = math.exp(-days_since / config.recency_tau_days)
    gold_norm = min(abs(event.goldstein_scale) / 10.0, 1.0)
    type_weight = event_type_weights.get(event.event_type.value, event_type_weights.get("UNKNOWN", 0.3))
    raw = (
        config.w_sev * event.severity
        + config.w_gold * gold_norm
        + config.w_type * type_weight
    ) * recency
    return min(raw, config.cap_single_event)


def compute_corridor_score(
    events: list[SignalEvent],
    *,
    corridor: Corridor,
    score_date: date,
    config: AppConfig | None = None,
) -> tuple[float, list[SignalEvent]]:
    cfg = config or load_config()
    relevant = [
        e
        for e in events
        if e.corridor == corridor and e.confidence >= cfg.scoring.confidence_threshold
    ]
    if not relevant:
        return 0.0, []

    contributions = [
        (
            per_event_contribution(
                event,
                score_date=score_date,
                config=cfg.scoring,
                event_type_weights=cfg.event_type_weights,
            ),
            event,
        )
        for event in relevant
        if event.event_date <= score_date
    ]
    if not contributions:
        return 0.0, []

    contributions.sort(key=lambda item: item[0], reverse=True)
    top_k = contributions[: cfg.scoring.top_k_events]
    mean_top = sum(value for value, _ in top_k) / len(top_k)

    window_start = score_date - timedelta(days=7)
    window_values = [
        value
        for value, event in contributions
        if window_start <= event.event_date <= score_date
    ]
    if window_values:
        sorted_vals = sorted(window_values)
        mid = len(sorted_vals) // 2
        if len(sorted_vals) % 2:
            median = sorted_vals[mid]
        else:
            median = (sorted_vals[mid - 1] + sorted_vals[mid]) / 2
    else:
        median = mean_top

    score = 0.6 * mean_top + 0.4 * median
    return min(max(score, 0.0), 1.0), [event for _, event in top_k]


def compute_trend_7d(
    current_score: float,
    prior_score: float | None,
    *,
    config: ScoringConfig | None = None,
) -> Trend7d:
    cfg = config if config is not None else load_config().scoring
    if prior_score is None:
        return Trend7d.stable
    delta = current_score - prior_score
    if abs(delta) < cfg.trend_stable_epsilon:
        return Trend7d.stable
    return Trend7d.rising if delta > 0 else Trend7d.falling


def build_risk_scores(
    events: list[SignalEvent],
    *,
    score_date: date | None = None,
    prior_scores: dict[Corridor, float] | None = None,
    config: AppConfig | None = None,
) -> list[RiskScore]:
    cfg = config or load_config()
    as_of = score_date or max((e.event_date for e in events), default=date.today())
    prior = prior_scores or {}

    results: list[RiskScore] = []
    for corridor in CORRIDOR_ORDER:
        score, contributors = compute_corridor_score(events, corridor=corridor, score_date=as_of, config=cfg)
        trend = compute_trend_7d(score, prior.get(corridor), config=cfg.scoring)
        results.append(
            RiskScore(
                corridor=corridor,
                score=round(score, 6),
                score_date=as_of,
                contributing_event_ids=[event.event_id for event in contributors],
                trend_7d=trend,
            )
        )
    return results