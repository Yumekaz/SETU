# Hormuz 2026 Backtest Results

## Section A — Threshold and reference point (locked before dense-cache replay)

| Parameter | Locked value |
|-----------|--------------|
| Reference point date | 2026-03-02 |
| Reference point label | EIA-dated closure of the Strait of Hormuz |
| Risk threshold | 0.35 |
| Replay window | 2026-02-01 → 2026-06-30 |
| Evidence coverage | Six-hour samples from 2026-01-15 → 2026-03-02 (2,753 accepted GDELT rows; 1,831 normalized SignalEvents) |
| Seed / simulations | 42 / 200 |
| Headline formula | `lead_time_days = reference_point_date − first_threshold_crossing_date` |

**Hypothesis:** SETU's deterministic Hormuz risk score crosses the 0.35 threshold before the 2026-03-02 public closure anchor, yielding a positive `lead_time_days` on reproducible offline replay of the committed GDELT cache.

The original sparse cache was replaced with a denser, date-bounded GDELT cache after its schema and coverage limitations were identified. The threshold, reference date, seed, and simulation count were not changed for this replay.

**Limitations (explicit):**

- N=1 sample — one real crisis, not statistical proof of general accuracy.
- This is a targeted lead-time test: evidence ends at the locked 2026-03-02 reference point. Scores after that point do not support a forward-looking claim.
- GRU inference may fall back to trend mode when lookback is insufficient at early dates.

## Section B — Results

| Field | Value |
|-------|-------|
| status | `no_crossing` |
| first_threshold_crossing_date | *(none — max Hormuz score 0.25 < threshold 0.35)* |
| lead_time_days | *(null)* |
| reference_point_date | 2026-03-02 |
| risk_threshold | 0.35 |
| max_observed_hormuz_score | 0.25; first observed on 2026-02-01 |
| trajectory_days | 150 |
| seed / n_simulations | 42 / 200 |

**Interpretation:** On the committed dense offline GDELT cache, the deterministic Hormuz risk score does not reach the locked 0.35 threshold before the **2026-03-02** reference anchor. `2026-03-11` is a separate configured ground-truth comparison date; it is not the lead-time anchor. This is reported without post-hoc threshold tuning. The run therefore does **not** demonstrate positive historical lead time at the locked threshold.

**Chain proof at peak (not a crossing claim):** Because `status=no_crossing`, the harness runs forecast → cascade → orchestrator at the trajectory peak (2026-02-01, score 0.25). Response fields: `orchestrator_at_peak`, `orchestrator_summary`, `pit_integrity`, `trajectory_peak`. PIT diagnostics at peak: `pit_ok=true`, `visible_events=678`, and `excluded_future_events=1,196`; the chain therefore demonstrably excludes later cached events. Headline `lead_time_days` remains null.

**Chain-at-crossing proof (sub-test only):** `test_run_backtest_with_lower_threshold_invokes_chain` uses threshold 0.2 (not in config) to prove full chain at crossing: `status=crossed`, `orchestrator_at_crossing` populated, `lead_time_days` computed.

**Secondary metric:** Not applicable for headline lead time (`no_crossing`). Ground-truth comparison runs only when threshold is crossed.

**Reproducibility:** Two consecutive `run_backtest()` calls return identical `status`, `lead_time_days`, `trajectory_peak`, and `orchestrator_at_peak`.
