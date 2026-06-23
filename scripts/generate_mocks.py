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

# Frozen anchor date for deterministic output regardless of run date
FREEZE_DATE = date(2026, 6, 23)
FREEZE_DATETIME = datetime(2026, 6, 23, 12, 0, 0, tzinfo=timezone.utc)

# Add backend to path for Pydantic models
sys.path.insert(0, str(ROOT / "backend"))

from app.models.generated import (  # noqa: E402
    CascadeResult,
    GraphEdge,
    GraphNode,
    Recommendation,
    RiskScore,
    SignalEvent,
)

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
GRAPH_NODE_COUNT = 12


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


def generate_cascade_results(n: int = 3) -> list[CascadeResult]:
    results = []
    for i in range(n):
        corridor = CORRIDORS[i % len(CORRIDORS)]
        results.append(
            CascadeResult(
                scenario_id=_uid(),
                corridor=corridor,
                disruption_duration_days=RNG.randint(3, 21),
                n_simulations=1000,
                price_impact_pct=_ordered_percentiles(),
                refinery_throughput_impact_pct=_ordered_percentiles(),
                spr_days_required=_ordered_percentiles(),
                affected_downstream_nodes=[
                    f"port_{corridor.lower()}",
                    "refinery_mumbai",
                    "demand_north",
                ],
            )
        )
    return results


def generate_graph_nodes(n: int = GRAPH_NODE_COUNT) -> list[GraphNode]:
    nodes = []
    coords = [
        (26.5, 56.5, "Hormuz Strait", "CORRIDOR"),
        (12.6, 43.3, "Bab-el-Mandeb", "CORRIDOR"),
        (1.3, 103.8, "Malacca Strait", "CORRIDOR"),
        (18.9, 72.8, "JNPT Mumbai", "PORT"),
        (13.1, 80.3, "Chennai Port", "PORT"),
        (22.5, 69.7, "Kandla Port", "PORT"),
        (19.0, 73.0, "Mumbai Refinery Complex", "REFINERY"),
        (13.0, 80.2, "Chennai Refinery", "REFINERY"),
        (28.6, 77.2, "North India Demand Hub", "DEMAND_CENTER"),
        (17.4, 78.5, "South India Demand Hub", "DEMAND_CENTER"),
        (25.2, 55.3, "Gulf Production Aggregate", "PRODUCTION_FIELD"),
        (30.0, 48.0, "Arabian Production Aggregate", "PRODUCTION_FIELD"),
    ]
    for i in range(min(n, len(coords))):
        lat, lon, name, node_type = coords[i]
        nodes.append(
            GraphNode(
                node_id=f"node_{i + 1}",
                node_type=node_type,
                name=name,
                lat=lat,
                lon=lon,
                capacity_mbpd=round(RNG.uniform(0.5, 5.0), 2),
            )
        )
    return nodes


def generate_graph_edges(nodes: list[GraphNode], n: int = 10) -> list[GraphEdge]:
    edges = []
    for i in range(min(n, len(nodes) - 1)):
        edges.append(
            GraphEdge(
                source=nodes[i].node_id,
                target=nodes[i + 1].node_id,
                flow_mbpd=round(RNG.uniform(0.3, 2.5), 2),
                corridor_dependency=RNG.choice(CORRIDORS),
                alt_route_penalty_days=round(RNG.uniform(5.0, 25.0), 1),
            )
        )
    return edges


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
    out = FIXTURES_DIR / f"{name}.json"
    payload = [item.model_dump(mode="json") for item in data]
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out} ({len(data)} records)")
    return out


def main() -> int:
    print(f"Generating mock fixtures (seed=42, freeze_date={FREEZE_DATE})...")

    events = generate_signal_events()
    scores = generate_risk_scores(events)
    cascades = generate_cascade_results()
    nodes = generate_graph_nodes()
    edges = generate_graph_edges(nodes)
    recommendations = generate_recommendations()

    for _label, items, model in [
        ("signal_events", events, SignalEvent),
        ("risk_scores", scores, RiskScore),
        ("cascade_results", cascades, CascadeResult),
        ("graph_nodes", nodes, GraphNode),
        ("graph_edges", edges, GraphEdge),
        ("recommendations", recommendations, Recommendation),
    ]:
        for item in items:
            model.model_validate(item.model_dump())

    write_fixture("signal_events", events)
    write_fixture("risk_scores", scores)
    write_fixture("cascade_results", cascades)
    write_fixture("graph_nodes", nodes)
    write_fixture("graph_edges", edges)
    write_fixture("recommendations", recommendations)

    print("All fixtures validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())