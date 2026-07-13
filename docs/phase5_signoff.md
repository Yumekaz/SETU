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
| Limitations documented | Yes | N=1, 17-day baseline, place-name context limitation; 20-day calibrated lead-time result |
| PIT integrity | Yes | `filter_events_up_to`, `assert_events_visible_at`, `pit_diagnostics`, synthetic future-event test |
| Chain proof | Yes | At the locked 2026-02-10 crossing (`orchestrator_at_crossing`) |
| Health phase 5 / 0.6.0 | Yes | `test_phase5_api.py` |

## Locked-threshold result (honest)

- `status=crossed`, `lead_time_days=20`, first crossing score 0.578125 on 2026-02-10 at threshold 0.437501
- `orchestrator_summary` from the crossing-date chain
- Dense cache has 2,753 date-bounded candidate rows / 1,080 normalized events; PIT diagnostics exclude 377 future events at crossing

## Out of scope (confirmed)

Phase 6 replay UI, additional crises, threshold post-hoc tuning, live GDELT calls.
