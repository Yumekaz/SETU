# Hormuz 2026 Backtest Model — Phase 5

## Point-in-time replay

For each `score_date` in `[window_start, window_end]`:

1. Filter GDELT-derived `SignalEvent` rows to `event_date <= score_date` via `filter_events_up_to()`.
2. Build `prior_scores` from events visible through `score_date - 7 days` (separate filter — no lookahead for 7-day trend).
3. Run `build_risk_scores()` (same engine as Phase 1 / feature replay).
4. Record Hormuz corridor score for the day.

No shared `daily_features.parquet` or SQLite score tables are written during replay.

## Headline metric

- **Reference point (source-verified):** `2026-03-02` — EIA-dated closure of the Strait of Hormuz.
- **Threshold (locked):** `0.35` in `data/config/backtest.yaml`.
- **First crossing:** earliest date where Hormuz score ≥ threshold.
- **Lead time:** `reference_point_date - first_crossing_date` (integer days). **Null when no crossing.**

## Chain execution (crossing or peak)

**When threshold is crossed:** on `first_crossing_date`:

1. `filter_events_up_to(events, crossing_date)` then `build_daily_features(events, end=crossing_date)`.
2. `forecast_corridor(HORMUZ, features)` — GRU or trend fallback per Phase 3 rules.
3. `run_cascade(HORMUZ, seed, n_simulations)` — Monte Carlo with fixed seed.
4. `run_orchestrator(cascade, network, forecast)` — Pareto options.

Result stored in `orchestrator_at_crossing`; `orchestrator_summary` points here.

**When threshold is not crossed (locked run):** on trajectory **peak** date (highest Hormuz score in window):

Same four steps, using events visible through peak date. Result stored in `orchestrator_at_peak`; `orchestrator_summary` points here. This is **chain proof only** — headline `lead_time_days` remains null.

## Secondary metric

Compare generated option_ids at crossing against the `2026-03-18` timeline row (SPR drawdown / Cape reroute discussions). Assessment is qualitative (`partial_match` / `no_match`), not a fabricated accuracy score. Runs only when threshold is crossed.

## Integrity

- `assert_events_visible_at()` / `assert_no_future_events()` fail if any event with `event_date > as_of` would be used.
- `pit_diagnostics(events, as_of)` returns structured proof: visible count, excluded future count, max visible date, `pit_ok`.
- `events_for_score_date()` filters and validates in one call.
- Replay uses separate prior/current filters before every score call.
- **Cache caveat:** committed `gdelt_hormuz_backtest.json` max `event_date` is 2026-02-14, so real-cache chain runs show `excluded_future_events=0`. Lookahead exclusion within the replay window is proven by unit tests that inject synthetic future events (see `test_replay_excludes_injected_future_events`).

## Limitations

- N=1 historical crisis — directional evidence only.
- Sparse GDELT sampling in early Feb may delay crossing detection; gaps documented in `backtest_results.md`.
- Threshold is not tuned post-hoc to maximize lead time.
- Default locked run (`no_crossing` at 0.35) does not produce a positive lead-time claim.
