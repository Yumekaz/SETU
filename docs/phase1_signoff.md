# Phase 1 Sign-Off — Signal Intelligence Layer

**Branch:** `phase-1/signal-intelligence`  
**Date:** 2026-06-23  
**Status:** Complete per SRS Section 11 acceptance criteria

---

## Acceptance Criteria

### 1. ≥90% valid `SignalEvent` from 50+ Hormuz-window GDELT rows

| Metric | Result |
|---|---|
| Backtest cache | `data/samples/gdelt_hormuz_backtest.json` (55 rows) |
| Accepted extractions | 55/55 (100%) via rules fallback |
| Low-confidence handling | Rejected rows logged to `extraction_log` (tested in `test_extraction.py`) |

### 2. Deterministic risk scoring + documented formula

- Implementation: `backend/app/signals/score.py`
- Documentation: `docs/risk_scoring.md`
- Re-run identical batch → identical `RiskScore` JSON (`test_phase1_determinism.py`)

### 3. Offline cache pipeline + SQLite + API

| Endpoint | Status |
|---|---|
| `POST /api/pipeline/run` | Populates DB from cache, no network |
| `GET /api/signals` | Returns persisted events with audit fields |
| `GET /api/risk-scores` | Returns per-corridor scores |
| `GET /api/risk-scores/latest` | HORMUZ, BAB_EL_MANDEB, MALACCA |

### 4. GBNF + llama-cpp-python + rules fallback

| Component | Path |
|---|---|
| GBNF grammar | `ml/grammars/signal_event.gbnf` |
| LLM runner | `ml/extraction/llama_runner.py` |
| Rules fallback | `backend/app/signals/rules_extractor.py` |
| Config | `data/config/corridors.yaml` |
| Model download | `scripts/download_model.py` → gitignored `data/models/` |

CI uses `SETU_EXTRACTOR_MODE=rules`. Local LLM path: set `SETU_LLM_MODEL_PATH` after `python scripts/download_model.py`.

---

## Test Evidence

```bash
SETU_EXTRACTOR_MODE=rules pytest tests/ -v
# 52 passed
```

Phase 1 tests: `test_gdelt_ingest.py`, `test_corridor_classify.py`, `test_extraction.py`, `test_dedup.py`, `test_risk_scoring.py`, `test_phase1_pipeline.py`, `test_phase1_determinism.py`, `test_phase1_offline.py`, `test_phase1_llm.py`

---

## Out of Scope (confirmed not built)

- GKG ingestion, AIS, non-English sources, frontend map, cascade/GRU layers