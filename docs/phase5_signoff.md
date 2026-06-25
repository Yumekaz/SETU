# Phase 5 Sign-Off — Historical Backtest Harness

## Deliverables

| Item | Location |
|------|----------|
| Locked config | `data/config/backtest.yaml` |
| Timeline (11 cited rows) | `data/hormuz_2026_timeline.csv` |
| Backtest package | `backend/app/backtest/` |
| API | `POST /api/backtest/run`, `GET /api/backtest/config`, `GET /api/backtest/latest` |
| Results doc | `docs/backtest_results.md` (Section A before run, Section B after) |
| Model doc | `docs/backtest_model.md` |

## SRS Section 15 AC reconciliation

| Criterion | Met | Notes |
|-----------|-----|-------|
| Cited timeline 8–12 rows | Yes | 11 rows, all with `source_url` |
| Reproducible harness | Yes | `test_backtest_pipeline.py` |
| Reference locked before run | Yes | Section A + `backtest.yaml` |
| Limitations documented | Yes | N=1, sparse cache, `no_crossing` at 0.35 |
| PIT integrity | Yes | `filter_events_up_to`, `assert_events_visible_at`, `pit_diagnostics`, synthetic future-event test |
| Chain proof | Yes | At peak when `no_crossing` (`orchestrator_at_peak`); at crossing in sub-threshold test (0.2) |
| Health phase 5 / 0.6.0 | Yes | `test_phase5_api.py` |

## Locked-threshold result (honest)

- `status=no_crossing`, `lead_time_days=null`, peak score 0.25 on 2026-02-14
- `orchestrator_summary` from peak-date chain (not a crossing claim)
- Cache max event_date 2026-02-14; PIT exclusion beyond that proven synthetically

## Out of scope (confirmed)

Phase 6 replay UI, additional crises, threshold post-hoc tuning, live GDELT calls.