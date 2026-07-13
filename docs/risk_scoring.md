# SETU Risk Scoring — Phase 1

Deterministic per-corridor risk scores. **The LLM never contributes to scoring** — it only extracts structured fields upstream.

## Inputs

- Accepted `SignalEvent` records (confidence ≥ threshold, not `UNKNOWN`)
- Score date (`score_date`, UTC date)
- Prior corridor score (7 days earlier) for trend

## Per-event contribution

For each event `e` on score date `D`:

```
days_since = max((D - e.event_date).days, 0)
recency    = exp(-days_since / RECENCY_TAU)

gold_norm  = min(|e.goldstein_scale| / 10, 1.0)
type_w     = EVENT_TYPE_WEIGHTS[e.event_type]

raw = (W_SEV * e.severity + W_GOLD * gold_norm + W_TYPE * type_w) * recency
contribution = min(raw, CAP_SINGLE)
```

## Corridor score

1. Keep events where `e.corridor == corridor` and `e.event_date == D`.
2. Deduplicate GDELT's multiple event rows per source URL, retaining the highest capped contribution for that source.
3. Combine the remaining independent source contributions with a noisy-OR:

```
score = 1 - Π(1 - contribution_source)
```

This keeps `CAP_SINGLE` as an outlier dampener for one event/source, while
allowing corroborating independent sources to raise corridor risk above 0.25.

## 7-day trend

Compare current score to score 7 days prior:

| Condition | `trend_7d` |
|---|---|
| No prior score | `STABLE` |
| `|current - prior| < TREND_EPS` | `STABLE` |
| `current > prior` | `RISING` |
| `current < prior` | `FALLING` |

## Default weights (from `data/config/corridors.yaml`)

| Parameter | Value | Rationale |
|---|---|---|
| `W_SEV` | 0.45 | Extracted severity is primary signal |
| `W_GOLD` | 0.30 | GDELT Goldstein is auditable |
| `W_TYPE` | 0.25 | Event-type prior (military > diplomatic) |
| `RECENCY_TAU` | 14 days | Half-life for relevance decay |
| `CAP_SINGLE` | 0.25 | Per-event/source outlier dampening; not a corridor-score ceiling |
| `CONFIDENCE_THRESHOLD` | 0.5 | Hallucination gate — sub-threshold events excluded |
| `TREND_EPS` | 0.03 | Stable band for trend label |
| `TOP_K` | 5 | Top contributing events cap |

### Event-type weights

| Type | Weight |
|---|---|
| MILITARY | 1.0 |
| SANCTION | 0.9 |
| PIRACY | 0.85 |
| INFRASTRUCTURE | 0.75 |
| DIPLOMATIC | 0.6 |
| ACCIDENT | 0.5 |
| UNKNOWN | 0.3 |

## Implementation

- Formula: [`backend/app/signals/score.py`](../backend/app/signals/score.py)
- Config: [`data/config/corridors.yaml`](../data/config/corridors.yaml)
