# Phase 2 Sign-Off — Network Graph + Monte Carlo Cascade

**Branch:** `phase-2/network-cascade`  
**Date:** 2026-06-24  
**Status:** Complete per SRS Section 12 and Appendix B acceptance criteria

---

## Acceptance Criteria

### 1. Cited India crude DAG with validation

| Item | Result |
|---|---|
| Graph source | `data/graph/india_crude_network.json` |
| Semantic IDs | `corridor_hormuz`, `port_mumbai`, `refinery_jamnagar`, `demand_*` (no `node_1` chain) |
| Citations | In-file `sources` + `docs/network_graph_sources.md` |
| Validation | Zero negative capacities, positive edge flows, all demand centers reachable (`test_graph_loader.py`) |

### 2. Monte Carlo cascade engine

| Component | Path |
|---|---|
| Graph loader | `backend/app/simulation/graph_loader.py` |
| Distributions | `data/config/corridor_distributions.yaml` |
| Propagation | `backend/app/simulation/propagate.py` (dependent-edge traversal + capacity caps) |
| Corridor allowlist | `backend/app/simulation/corridors.py` — OTHER returns 422 |
| Monte Carlo | `backend/app/simulation/monte_carlo.py` |

Hormuz directional check (seed=42, n=200): p50 price impact is **positive** and within order of magnitude of the Mar 2026 Brent anchor (~78→85 ≈ +8.8%). Observed p50 ≈ 6% — not forced to match exactly.

### 3. Convergence + determinism

- Script: `scripts/run_convergence_check.py` → `docs/monte_carlo_convergence.md`
- Chosen `n_simulations`: 500 (first step with <2% p50 drift vs prior)
- Identical corridor + seed + n → byte-identical `CascadeResult` (`test_monte_carlo.py`)

### 4. API + SQLite persistence

| Endpoint | Status |
|---|---|
| `GET /api/graph` | Returns cited network JSON |
| `POST /api/cascade/simulate` | Runs MC, persists to `cascade_results` |
| `POST /api/cascade/simulate/from-risk` | Triggers on highest Phase 1 `RiskScore` |
| `GET /api/cascade/results` | Lists stored results |
| `GET /api/cascade/results/latest` | Latest per corridor |

Health: `phase: 2`, `version: 0.3.0`

---

## Test Evidence

```bash
SETU_EXTRACTOR_MODE=rules SETU_MC_N_SIMULATIONS=500 pytest tests/ -v
```

Phase 2 tests: `test_graph_loader.py`, `test_propagate.py`, `test_monte_carlo.py`, `test_phase2_api.py`

---

## Out of Scope (confirmed not built)

Phase 3 GRU forecasting, Phase 4 Pareto/HITL, Phase 6 geospatial UI, refined-product modeling, LLM in simulation math.