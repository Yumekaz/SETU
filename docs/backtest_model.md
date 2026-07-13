# Hormuz 2026 Backtest Model — Phase 5

## Point-in-time replay

For each `score_date` in `[window_start, window_end]`:

1. Filter GDELT-derived `SignalEvent` rows to `event_date <= score_date` via `filter_events_up_to()`.
2. Build `prior_scores` from events visible through `score_date - 7 days` (separate filter — no lookahead for 7-day trend).
3. Run `build_risk_scores()`: it uses same-day, source-deduplicated capped contributions combined with noisy-OR.
4. Record Hormuz corridor score for the day.

No shared `daily_features.parquet` or SQLite score tables are written during replay.

## Headline metric

- **Reference point (source-verified):** `2026-03-02` — EIA-dated closure of the Strait of Hormuz.
- **Separate comparison date:** `2026-03-11` is only used for the optional qualitative recommendation comparison after a crossing; it is not the lead-time anchor.
- **Threshold (locked):** `0.437501` in `data/config/backtest.yaml`, derived before final evaluation from the Jan 15–31 baseline at a ≤5% target (0 observed alerts in 17 days).
- **First crossing:** earliest date where Hormuz score ≥ threshold.
- **Lead time:** `reference_point_date - first_crossing_date` (integer days). **Null when no crossing.**

## Chain execution (crossing or peak)

**When threshold is crossed:** on `first_crossing_date`:

1. `filter_events_up_to(events, crossing_date)` then `build_daily_features(events, end=crossing_date)`.
2. `forecast_corridor(HORMUZ, features)` — GRU or trend fallback per Phase 3 rules.
3. `run_cascade(HORMUZ, seed, n_simulations)` — Monte Carlo with fixed seed.
4. `run_orchestrator(cascade, network, forecast)` — Pareto options.

Result stored in `orchestrator_at_crossing`; `orchestrator_summary` points here.

**When threshold is not crossed:** on trajectory **peak** date (highest Hormuz score in window):

Same four steps, using events visible through peak date. Result stored in `orchestrator_at_peak`; `orchestrator_summary` points here. This is **chain proof only** — headline `lead_time_days` remains null.

## Secondary metric

Compare generated option_ids at crossing against the configured `2026-03-11` timeline row. Assessment is qualitative (`partial_match` / `no_match`), not a fabricated accuracy score. Runs only when threshold is crossed.

## Integrity

- `assert_events_visible_at()` / `assert_no_future_events()` fail if any event with `event_date > as_of` would be used.
- `pit_diagnostics(events, as_of)` returns structured proof: visible count, excluded future count, max visible date, `pit_ok`.
- `events_for_score_date()` filters and validates in one call.
- Replay uses separate prior/current filters before every score call.
- **Cache coverage:** committed `gdelt_hormuz_backtest_dense.json` contains six-hour GDELT samples through the locked `2026-03-02` reference date. The lead-time claim uses only this pre-reference evidence. Point-in-time diagnostics on the locked run exclude future cached events (and unit tests also inject synthetic future events).

## Limitations

- N=1 historical crisis — directional evidence only.
- One historical replay and a 17-day baseline cannot establish broad detection accuracy or stable false-positive rates.
- Threshold was derived from the separate baseline, not tuned against the Feb–Mar evaluation outcome.
- Place-name anchors near Hormuz still need richer maritime-context disambiguation (see KL-11).
