# Phase 3 Sign-Off — GRU Forecasting Layer

**Branch:** `phase-3/gru-forecast`  
**Date:** 2026-06-24  
**Status:** Complete per SRS Section 13 and Appendix D

---

## Acceptance Criteria

### 1. Daily feature engineering

| Item | Result |
|---|---|
| Script | `scripts/build_forecast_dataset.py` |
| Output | `data/forecast/daily_features.parquet` (600 rows, 4 corridors) |
| Columns | `date`, `corridor`, `risk_score`, `goldstein_aggregate`, `event_count`, `price_lag` |
| Sources | Cached GDELT backtest + `hormuz_2026_timeline.csv` Brent anchors |

### 2. GRU training + leakage guard

| Item | Result |
|---|---|
| Model | Shared 2-layer GRU (hidden 64, dropout 0.2) |
| Loss | Quantile pinball (p10/p50/p90) |
| Checkpoint | `data/checkpoints/gru/model.pt` + `model_meta.json` |
| Leakage test | `tests/test_chronological_split.py` (build-failing) |
| Routing | GRU: `HORMUZ` only; `TREND_FALLBACK`: BAB_EL_MANDEB, MALACCA, OTHER |

### 3. RiskForecast contract + cascade feed

| Schema | `schemas/risk_forecast.json` |
| API | `GET/POST /api/forecast/*`, `POST /api/cascade/simulate/from-forecast` |
| Health | `phase: 3`, `version: 0.4.0` |

### 4. Training report

- `docs/gru_training_report.md` — loss curve, corridor routing, Hormuz-heavy honesty statement

---

## Test Evidence

```bash
SETU_EXTRACTOR_MODE=rules SETU_MC_N_SIMULATIONS=50 pytest tests/ -v
# 117 passed (2 consecutive runs)
```

Phase 3 tests: `test_forecast_features.py`, `test_chronological_split.py`, `test_gru_model.py`, `test_forecast_inference.py`, `test_phase3_api.py`

---

## Out of Scope (confirmed not built)

Phase 4 Pareto/HITL, Phase 5 backtest harness, Phase 6 map UI, >7-day forecasts, LLM in forecasting.