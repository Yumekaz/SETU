# Hormuz 2026 Backtest Model — Phase 5

## Point-in-time replay

For each `score_date` in `[window_start, window_end]`:

1. Filter GDELT-derived `SignalEvent` rows to `event_date <= score_date`.
2. Run `build_risk_scores()` (same engine as Phase 1 / feature replay).
3. Record Hormuz corridor score for the day.

No shared `daily_features.parquet` or SQLite score tables are written during replay.

## Headline metric

- **Reference point (locked):** `2026-03-11` — reported Hormuz transit restriction (EIA anchor).
- **Threshold (locked):** `0.35` in `data/config/backtest.yaml`.
- **First crossing:** earliest date where Hormuz score ≥ threshold.
- **Lead time:** `reference_point_date - first_crossing_date` (integer days).

## Chain at crossing

On `first_crossing_date`:

1. `build_daily_features(events, end=crossing_date)` — features truncated to PIT.
2. `forecast_corridor(HORMUZ, features)` — GRU or trend fallback per Phase 3 rules.
3. `run_cascade(HORMUZ, seed, n_simulations)` — Monte Carlo with fixed seed.
4. `run_orchestrator(cascade, network, forecast)` — Pareto options.

## Secondary metric

Compare generated option_ids at crossing against the `2026-03-18` timeline row (SPR drawdown / Cape reroute discussions). Assessment is qualitative (`partial_match` / `no_match`), not a fabricated accuracy score.

## Integrity

`assert_no_future_events()` fails if any event with `event_date > score_date` would be used. Replay uses `filter_events_up_to()` before every score call.

## Limitations

- N=1 historical crisis — directional evidence only.
- Sparse GDELT sampling in early Feb may delay crossing detection; gaps documented in `backtest_results.md`.
- Threshold is not tuned post-hoc to maximize lead time.