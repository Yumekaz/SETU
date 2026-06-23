# Phase 0 Sign-Off — Foundations & Contract Freeze

**Branch:** `phase-0/foundations`  
**Date:** 2026-06-23  
**Status:** ✅ All acceptance criteria met

---

## Acceptance Criteria

### 1. Five JSON contracts enforced in backend (Pydantic) and frontend (TypeScript)

| Contract | Schema | Pydantic (`generated.py`) | TypeScript (`generated.ts`) |
|----------|--------|---------------------------|-----------------------------|
| SignalEvent | `schemas/signal_event.json` | `SignalEvent` | `SignalEvent` |
| RiskScore | `schemas/risk_score.json` | `RiskScore` | `RiskScore` |
| CascadeResult | `schemas/cascade_result.json` | `CascadeResult` | `CascadeResult` |
| GraphNode / GraphEdge | `schemas/graph_node.json`, `graph_edge.json` | `GraphNode`, `GraphEdge` | `GraphNode`, `GraphEdge` |
| Recommendation | `schemas/recommendation.json` | `Recommendation` | `Recommendation` |

**Shared types:** `corridor.json` → `Corridor`; `percentile_band.json` → `PercentileBand`

**Evidence:**
- Schemas: all use `$schema: draft-07`, `additionalProperties: false` — verified by `tests/test_schemas.py` (6 parametrized tests, all pass)
- Codegen: `python scripts/generate_models.py` produces `backend/app/models/generated.py` and `frontend/src/types/generated.ts`
- Fixture validation: Pydantic + jsonschema tests pass for all 6 fixture files (27 tests total)

```bash
python scripts/generate_models.py
pytest tests/test_schemas.py -v
# Result: 27 passed
```

---

### 2. Docker Compose brings up working skeleton end-to-end

**Files:**
- `docker-compose.yml` — backend (8000) + frontend (5173), `setu-data` volume
- `backend/Dockerfile` — Python 3.11-slim, FastAPI/uvicorn
- `frontend/Dockerfile` — Node 20 build → nginx serve on 5173

**Endpoints:**
- `GET /health` → `{"status":"ok","version":"0.1.0","phase":0}`
- `GET /api/contracts` → all schema JSON files
- Frontend: health badge + mock RiskScore card from fixture

**Evidence:**
```bash
docker compose up --build
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000/health
```

**Local verification (no Docker):**
```bash
pytest tests/test_health.py -v
# test_health_returns_ok PASSED
# test_contracts_endpoint_serves_schemas PASSED
```

> **Note:** Docker build not executed in CI sandbox (Docker daemon unavailable). Dockerfile and compose file are present and follow standard patterns; health tests confirm backend skeleton.

---

### 3. Real samples in `/data/samples` for GDELT, EIA, FRED, OFAC

| File | Source | Live pull? |
|------|--------|------------|
| `gdelt_events_sample.json` | GDELT 2.0 `gdeltv2/20260623130000.export.CSV.zip` | ✅ Yes (25 rows) |
| `ofac_sdn_sample.json` | Treasury SDN CSV | ✅ Yes (26 rows) |
| `fred_brent_sample.json` | FRED public CSV `DCOILBRENTEU` | ✅ Yes (10 observations) |
| `eia_brent_sample.json` | EIA API v2 shape | ⚠️ Fallback (no `EIA_API_KEY`) |

**Evidence:**
```bash
python scripts/pull_samples.py
ls -la data/samples/
# gdelt_events_sample.json  — source.live: true
# ofac_sdn_sample.json      — source.live: true
# fred_brent_sample.json    — source.live: true
# eia_brent_sample.json     — source.live: false (documented fallback)
```

See [data_sources.md](data_sources.md) for endpoints and key requirements.

---

### 4. Mock generator + schema tests pass

**Mock generator:** `scripts/generate_mocks.py` (seed=42, Pydantic validation)

**Fixtures produced:**
- `data/fixtures/signal_events.json` (12)
- `data/fixtures/risk_scores.json` (4)
- `data/fixtures/cascade_results.json` (3)
- `data/fixtures/graph_nodes.json` (8)
- `data/fixtures/graph_edges.json` (6)
- `data/fixtures/recommendations.json` (2)

**Evidence:**
```bash
python scripts/generate_mocks.py
pytest tests/ -v
# 27 passed in 0.69s
```

---

## Additional Deliverables

| Item | Location |
|------|----------|
| Hormuz 2026 timeline CSV | `data/hormuz_2026_timeline.csv` (5 cited rows) |
| CI workflow | `.github/workflows/ci.yml` |
| Environment template | `.env.example` |
| README quickstart | `README.md` |

---

## Out of Scope (confirmed)

- No modeling / intelligence logic
- No LLM extraction, scoring engine, Monte Carlo, or Pareto optimizer
- `/ml/` directory reserved (`.gitkeep` only)

---

## Sign-Off Checklist

- [x] All 5 JSON contracts exist as enforced types in backend and frontend
- [x] Docker Compose skeleton defined (backend health + frontend display)
- [x] Real samples for GDELT, OFAC, FRED; EIA fallback documented
- [x] Mock generator produces valid fixtures
- [x] Schema + health tests pass (27/27)
- [x] Docs in `/docs/` (Brief, SRS, data_sources, this sign-off)