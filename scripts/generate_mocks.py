#!/usr/bin/env python3
"""Generate validated mock fixtures for SETU data contracts (seed=42)."""

from __future__ import annotations

import json
import random
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = ROOT / "data" / "fixtures"
FRONTEND_FIXTURES_DIR = ROOT / "frontend" / "data" / "fixtures"

# Frozen anchor date for deterministic output regardless of run date
FREEZE_DATE = date(2026, 6, 23)
FREEZE_DATETIME = datetime(2026, 6, 23, 12, 0, 0, tzinfo=timezone.utc)

# Add backend to path for Pydantic models
sys.path.insert(0, str(ROOT / "backend"))

from app.models.generated import (  # noqa: E402
    CascadeResult,
    Corridor,
    GraphEdge,
    GraphNode,
    Recommendation,
    RiskForecast,
    RiskScore,
    SignalEvent,
)
from app.simulation.graph_loader import load_network_graph  # noqa: E402
from app.simulation.monte_carlo import run_cascade  # noqa: E402

RNG = random.Random(42)

CORRIDORS = ["HORMUZ", "BAB_EL_MANDEB", "MALACCA", "OTHER"]
EVENT_TYPES = [
    "MILITARY",
    "SANCTION",
    "ACCIDENT",
    "PIRACY",
    "DIPLOMATIC",
    "INFRASTRUCTURE",
    "UNKNOWN",
]
TRENDS = ["RISING", "FALLING", "STABLE"]
STATUSES = ["PENDING_APPROVAL", "APPROVED", "REJECTED", "EXPIRED"]

SIGNAL_EVENT_COUNT = 24
GRAPH_PATH = ROOT / "data" / "graph" / "india_crude_network.json"


def _uid() -> str:
    return str(uuid.UUID(int=RNG.getrandbits(128)))


def _date(days_ago: int = 0) -> str:
    return (FREEZE_DATE - timedelta(days=days_ago)).isoformat()


def _datetime(days_ago: int = 0) -> str:
    dt = FREEZE_DATETIME - timedelta(days=days_ago)
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _ordered_percentiles() -> dict[str, float]:
    """Return p10 <= p50 <= p90 percentile band."""
    p10 = round(RNG.uniform(1.0, 8.0), 2)
    p50 = round(RNG.uniform(p10, p10 + 12.0), 2)
    p90 = round(RNG.uniform(p50, p50 + 20.0), 2)
    return {"p10": p10, "p50": p50, "p90": p90}


def generate_signal_events(n: int = SIGNAL_EVENT_COUNT) -> list[SignalEvent]:
    events = []
    for i in range(n):
        events.append(
            SignalEvent(
                event_id=_uid(),
                corridor=RNG.choice(CORRIDORS),
                event_type=RNG.choice(EVENT_TYPES),
                severity=round(RNG.uniform(0.1, 0.95), 3),
                goldstein_scale=round(RNG.uniform(-8.0, 8.0), 2),
                confidence=round(RNG.uniform(0.55, 0.99), 3),
                event_date=_date(RNG.randint(0, 30)),
                ingested_at=_datetime(RNG.randint(0, 5)),
                source_url=f"https://example.com/source/{i + 1}",
                raw_text_snippet=(
                    f"Mock signal event {i + 1}: corridor disruption report "
                    f"for SETU Phase 0 fixture validation."
                )[:500],
            )
        )
    return events


def generate_risk_scores(events: list[SignalEvent], n: int = 4) -> list[RiskScore]:
    scores = []
    for corridor in CORRIDORS[:n]:
        related = [e.event_id for e in events if e.corridor == corridor][:3]
        scores.append(
            RiskScore(
                corridor=corridor,
                score=round(RNG.uniform(0.15, 0.85), 3),
                score_date=_date(0),
                contributing_event_ids=related or [_uid()],
                trend_7d=RNG.choice(TRENDS),
            )
        )
    return scores


def generate_cascade_results() -> list[CascadeResult]:
    """Deterministic cascade fixtures from the cited network graph."""
    corridors = [Corridor.hormuz, Corridor.bab_el_mandeb, Corridor.malacca]
    results: list[CascadeResult] = []
    for i, corridor in enumerate(corridors):
        results.append(
            run_cascade(
                corridor,
                n_simulations=200,
                seed=42 + i,
                network=load_network_graph(GRAPH_PATH),
            )
        )
    return results


def generate_graph_nodes() -> list[GraphNode]:
    return load_network_graph(GRAPH_PATH).nodes


def generate_graph_edges() -> list[GraphEdge]:
    return load_network_graph(GRAPH_PATH).edges


def generate_risk_forecasts() -> list[RiskForecast]:
    from app.forecast.config import DEFAULT_FEATURES_PATH
    from app.forecast.features import build_daily_features, write_features_parquet
    from app.forecast.inference import run_all_forecasts

    if not DEFAULT_FEATURES_PATH.exists():
        write_features_parquet(build_daily_features(), DEFAULT_FEATURES_PATH)
    return run_all_forecasts()


def generate_recommendations(n: int = 2) -> list[Recommendation]:
    recs = []
    for i in range(n):
        corridor = CORRIDORS[i % 3]
        options = []
        for j in range(3):
            options.append(
                {
                    "option_id": f"opt_{i + 1}_{j + 1}",
                    "description": (
                        f"Option {j + 1}: reroute / reserve / supplier mix "
                        f"response for {corridor}"
                    ),
                    "cost_score": round(RNG.uniform(0.1, 0.9), 3),
                    "time_score": round(RNG.uniform(0.1, 0.9), 3),
                    "risk_score": round(RNG.uniform(0.1, 0.9), 3),
                    "is_pareto_optimal": j < 2,
                }
            )
        recs.append(
            Recommendation(
                recommendation_id=_uid(),
                generated_at=_datetime(0),
                trigger_corridor=corridor,
                options=options,
                status=RNG.choice(STATUSES[:2]),
                operator_note=None if i == 0 else "Mock operator review note",
            )
        )
    return recs


def write_fixture(name: str, data: list) -> Path:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    FRONTEND_FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    payload = [item.model_dump(mode="json") for item in data]
    text = json.dumps(payload, indent=2)
    out = FIXTURES_DIR / f"{name}.json"
    out.write_text(text, encoding="utf-8")
    (FRONTEND_FIXTURES_DIR / f"{name}.json").write_text(text, encoding="utf-8")
    print(f"Wrote {out} ({len(data)} records)")
    return out


def main() -> int:
    print(f"Generating mock fixtures (seed=42, freeze_date={FREEZE_DATE})...")

    events = generate_signal_events()
    scores = generate_risk_scores(events)
    cascades = generate_cascade_results()
    nodes = generate_graph_nodes()
    edges = generate_graph_edges()
    recommendations = generate_recommendations()
    forecasts = generate_risk_forecasts()

    for _label, items, model in [
        ("signal_events", events, SignalEvent),
        ("risk_scores", scores, RiskScore),
        ("cascade_results", cascades, CascadeResult),
        ("risk_forecasts", forecasts, RiskForecast),
        ("graph_nodes", nodes, GraphNode),
        ("graph_edges", edges, GraphEdge),
        ("recommendations", recommendations, Recommendation),
    ]:
        for item in items:
            model.model_validate(item.model_dump())

    write_fixture("signal_events", events)
    write_fixture("risk_scores", scores)
    write_fixture("cascade_results", cascades)
    write_fixture("risk_forecasts", forecasts)
    write_fixture("graph_nodes", nodes)
    write_fixture("graph_edges", edges)
    write_fixture("recommendations", recommendations)

    print("All fixtures validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
