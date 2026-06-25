# Hormuz 2026 Backtest Results

## Section A — Hypothesis (locked before execution)

| Parameter | Locked value |
|-----------|--------------|
| Reference point date | 2026-03-11 |
| Reference point label | Reported Hormuz transit restriction (EIA anchor) |
| Risk threshold | 0.35 |
| Window | 2026-02-01 → 2026-06-30 |
| Seed / simulations | 42 / 200 |
| Headline formula | `lead_time_days = reference_point_date − first_threshold_crossing_date` |

**Hypothesis:** SETU's deterministic Hormuz risk score crosses the 0.35 threshold before the 2026-03-11 public closure anchor, yielding a positive `lead_time_days` on reproducible offline replay of the committed GDELT cache.

**Limitations (explicit):**

- N=1 sample — one real crisis, not statistical proof of general accuracy.
- GDELT cache uses strategic daily sampling (~55 rows); early-Feb signal density may be sparse.
- GRU inference may fall back to trend mode when lookback is insufficient at early dates.

## Section B — Results

| Field | Value |
|-------|-------|
| status | `no_crossing` |
| first_threshold_crossing_date | *(none — max Hormuz score 0.25 < threshold 0.35)* |
| lead_time_days | *(null)* |
| reference_point_date | 2026-03-11 |
| risk_threshold | 0.35 |
| max_observed_hormuz_score | 0.25 on 2026-02-14 |
| trajectory_days | 150 |
| seed / n_simulations | 42 / 200 |

**Interpretation:** On the committed offline GDELT cache, the deterministic Hormuz risk score does not reach the locked 0.35 threshold before the 2026-03-11 reference anchor. This is reported honestly — not tuned post-hoc. Sparse early-window signal density (see `docs/gru_training_report.md`) likely caps scores below the threshold.

**Secondary metric:** Not applicable (`no_crossing` — orchestrator chain not invoked).

**Reproducibility:** Two consecutive `run_backtest()` calls return identical `status`, `lead_time_days`, and `crossing_summary`.