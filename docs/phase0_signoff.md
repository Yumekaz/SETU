# Phase 0 Sign-Off — Foundations & Contract Freeze

**Branch:** `main` (merged from `phase-0/foundations`)  
**Date:** 2026-06-23 (updated after review fixes)  
**Status:** Phase 0 plumbing complete; see SRS AC reconciliation below

---

## Acceptance Criteria

### 1. Five JSON contracts enforced in backend (Pydantic) and frontend (TypeScript)

| Contract | Schema | Pydantic | TypeScript |
|----------|--------|----------|------------|
| SignalEvent | `signal_event.json` | `SignalEvent` | `SignalEvent` |
| RiskScore | `risk_score.json` | `RiskScore` | `RiskScore` |
| CascadeResult | `cascade_result.json` | `CascadeResult` | `CascadeResult` (uses `PercentileBand`) |
| GraphNode / GraphEdge | `graph_node.json`, `graph_edge.json` | `GraphNode`, `GraphEdge` | `GraphNode`, `GraphEdge` |
| Recommendation | `recommendation.json` | `Recommendation` | `Recommendation` + `RecommendationOption[]` |

**Shared types:** `corridor.json`, `percentile_band.json`

**Evidence:**
```bash
python scripts/generate_models.py
pytest tests/test_schemas.py tests/test_health.py -v
# Contracts endpoint returns exactly 8 schemas
# TypeScript emitter resolves $ref → PercentileBand, RecommendationOption[]
```

---

### 2. Docker Compose brings up working skeleton end-to-end

**Path fixes applied (review):**
- `SCHEMAS_DIR=/schemas` env var (Docker) vs `ROOT/schemas` (local)
- `DATABASE_URL=sqlite:////data/setu.db` → volume-mounted `/data/setu.db`
- Frontend Dockerfile: `COPY data/fixtures ./data/fixtures` for `../../data/fixtures` import

**Files:** `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`

**Local verification (without Docker):**
```bash
pytest tests/test_health.py -v
# test_health_returns_ok PASSED
# test_contracts_endpoint_serves_schemas PASSED (len==8)
```

**Docker verification:** Not run in implementation environment (no Docker daemon). User should run:
```bash
docker compose up --build
```

---

### 3. Real samples in `/data/samples` for GDELT, EIA, FRED, OFAC

| File | Source | `source.live` |
|------|--------|---------------|
| `gdelt_events_sample.json` | GDELT 2.0 `gdeltv2/` export | `true` when network available; fallback otherwise |
| `ofac_sdn_sample.json` | Treasury SDN CSV | `true` when network available; documented fallback |
| `fred_brent_sample.json` | FRED public CSV `DCOILBRENTEU` | `true` (CSV, no key) |
| `eia_brent_sample.json` | EIA API v2 Brent (`PET.RBRTE.R2`) | `true` — live pull 2026-06-23 |
| `eia_india_imports_sample.json` | EIA API v2 India imports | `true` — live pull 2026-06-23 |

**Assessment:** All five sources committed with `source.live: true` after `EIA_API_KEY` configured in local `.env` (not committed). Each puller is isolated with per-source `try/except`.

---

### 4. Mock generator + schema tests pass

**Generator:** `scripts/generate_mocks.py` — seed=42, `FREEZE_DATE=2026-06-23`

| Fixture | Count |
|---------|-------|
| `signal_events.json` | 24 |
| `risk_scores.json` | 4 |
| `graph_nodes.json` | 12 |
| `graph_edges.json` | 10 |
| `cascade_results.json` | 3 |
| `recommendations.json` | 2 |

**Evidence:**
```bash
python scripts/generate_mocks.py
pytest tests/ -v
# Includes test_generate_mocks.py: determinism, percentile ordering, min counts
```

---

## Additional Deliverables

| Item | Location | Notes |
|------|----------|-------|
| Hormuz timeline | `data/hormuz_2026_timeline.csv` | Columns: date, event_type, description, source_url, brent_usd, notes |
| CI | `.github/workflows/ci.yml` | ruff, pytest, npm ci, lint, build, docker compose build |
| ML placeholder | `ml/README.md` | Phase 3 reserved |
| API client | `frontend/src/api/client.ts` | Health fetch extracted from HealthBadge |
| Graph schema mins | `graph_node.json`, `graph_edge.json` | `minimum: 0` on capacity/flow/penalty |

---

## Out of Scope (confirmed)

No modeling / intelligence logic. `/ml/` contains README placeholder only.

---

## SRS Section 10 — Verbatim AC Reconciliation

| Verbatim SRS acceptance criterion | Met? | Notes |
|---|---|---|
| "All 5 JSON contracts exist as enforced types in both backend and frontend." | **Yes** | Codegen from `/schemas/`; 32+ tests validate fixtures |
| "Docker Compose brings up a working empty skeleton end to end (frontend can hit a backend health-check endpoint)." | **Structure yes; runtime unverified here** | Path fixes applied; `docker compose up --build` must be run on demo machine |
| "Real, successful sample pulls from GDELT, EIA, FRED, and OFAC are committed as fixtures in `/data/samples`." | **Yes** | All five `data/samples/*.json` files committed with `source.live: true` (verified 2026-06-23) |
| "Mock data generator produces valid fixtures against the frozen schemas." | **Yes** | `generate_mocks.py` + `test_generate_mocks.py` + `test_schemas.py` |

## Sign-Off Checklist

- [x] All 5 JSON contracts enforced in backend and frontend
- [x] Docker Compose skeleton with corrected paths (runtime verify on demo machine)
- [x] Samples for GDELT, OFAC, FRED, EIA Brent, EIA India imports — all live pulls committed
- [x] Mock generator deterministic with 20+ events, 10+ nodes
- [x] Schema + health + generate_mocks + phase0 artifact tests pass
- [x] Hormuz timeline: 5 cited rows (`data/hormuz_2026_timeline.csv`)
- [x] Docs in `/docs/` updated honestly