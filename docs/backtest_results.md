# Hormuz 2026 Backtest Results

## Section A — Final calibrated protocol (locked before final evaluation)

| Parameter | Locked value |
|-----------|--------------|
| Reference point date | 2026-03-02 |
| Reference point label | EIA-dated closure of the Strait of Hormuz |
| Risk threshold | 0.437501 |
| Replay window | 2026-02-01 → 2026-06-30 |
| Evidence coverage | Six-hour samples from 2026-01-15 → 2026-03-02 (2,753 date-bounded GDELT candidate rows; 1,080 normalized SignalEvents after relevance gates) |
| Seed / simulations | 42 / 200 |
| Headline formula | `lead_time_days = reference_point_date − first_threshold_crossing_date` |

**Protocol:** SETU's deterministic Hormuz risk score is evaluated against a 0.437501 threshold derived only from the separate Jan 15–31 baseline (≤5% target; 0/17 observed baseline alerts). The Feb 1–Mar 2 evaluation window is not used to choose that threshold.

The original sparse cache was replaced with a denser, date-bounded GDELT cache after its schema and coverage limitations were identified. City-level UAE/Dubai bbox false positives were removed, CAMEO protest root 14 was excluded from military risk, and the scorer now source-deduplicates capped same-day evidence before noisy-OR aggregation. The threshold was then calibrated from the held-out baseline and locked before this final evaluation.

**Limitations (explicit):**

- N=1 sample — one real crisis, not statistical proof of general accuracy.
- This is a targeted lead-time test: evidence ends at the locked 2026-03-02 reference point. Scores after that point do not support a forward-looking claim.
- GRU inference may fall back to trend mode when lookback is insufficient at early dates.

## Section B — Results

| Field | Value |
|-------|-------|
| status | `crossed` |
| first_threshold_crossing_date | 2026-02-10 |
| lead_time_days | 20 |
| reference_point_date | 2026-03-02 |
| risk_threshold | 0.437501 |
| crossing_score | 0.578125 |
| max_observed_hormuz_score | 0.816089 on 2026-03-02 |
| trajectory_days | 150 |
| seed / n_simulations | 42 / 200 |

**Interpretation:** On the committed dense offline GDELT cache, the deterministic Hormuz risk score first reaches the baseline-derived locked threshold on **2026-02-10**, 20 days before the **2026-03-02** reference anchor. `2026-03-11` is a separate ground-truth recommendation-comparison date; it is not the lead-time anchor. This is one historical case with a short 17-day baseline, not a broad claim of detection accuracy.

**Calibration:** A separate Jan 15–31 baseline, held apart from the Feb 1–Mar 2 evaluation window, has a maximum daily score of 0.437500. The locked 0.437501 threshold produces 0/17 baseline alerts at the ≤5% target. See `docs/threshold_calibration.md`.

**Chain proof at crossing:** The harness runs forecast → cascade → orchestrator on 2026-02-10, not at the later peak. `orchestrator_at_crossing` and `orchestrator_summary` contain the three generated options. PIT diagnostics at crossing: `pit_ok=true`, `visible_events=703`, `excluded_future_events=377`, and `max_visible_event_date=2026-02-10`.

**Regression crossing proof:** `test_run_backtest_with_lower_threshold_invokes_chain` exercises a second crossing configuration; the locked run itself now also populates `orchestrator_at_crossing`.

**Secondary metric:** The generated `spr_draw_hormuz` option is a qualitative `partial_match` with the 2026-03-11 IEA emergency-reserve action. This is not presented as a quantitative recommendation-accuracy score.

**Reproducibility:** Two consecutive `run_backtest()` calls return identical `status`, `lead_time_days`, `trajectory_peak`, and `orchestrator_at_crossing`.
