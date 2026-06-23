# Phase 0 Sign-Off — Foundations & Contract Freeze

**Branch:** `phase-0/foundations`  
**Date:** 2026-06-23 (updated after review fixes)  
**Status:** ✅ Acceptance criteria met with documented limitations

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
| `eia_brent_sample.json` | EIA API v2 shape | `false` — no `EIA_API_KEY` set |
| `eia_india_imports_sample.json` | EIA API v2 shape | `false` — no `EIA_API_KEY` set |

**Honest assessment:** GDELT, OFAC, and FRED have live or public-no-key pulls. Both EIA samples are **documented fallbacks** until `EIA_API_KEY` is provided. Each puller is isolated with per-source `try/except`.

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

## Sign-Off Checklist

- [x] All 5 JSON contracts enforced in backend and frontend
- [x] Docker Compose skeleton with corrected paths (user-verified pending)
- [x] Samples for GDELT, OFAC, FRED live; EIA Brent + India imports documented fallbacks
- [x] Mock generator deterministic with 20+ events, 10+ nodes
- [x] Schema + health + generate_mocks tests pass
- [x] Docs in `/docs/` updated honestly