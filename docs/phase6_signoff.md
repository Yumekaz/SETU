# Phase 6 Sign-Off — Geospatial Frontend & Integration

**Branch:** `phase-6/geospatial-frontend`  
**Health:** `phase: 6`, `version: 0.7.0`

## Deliverables

| Item | Location |
|------|----------|
| Backtest replay feeds | `GET /api/backtest/trajectory`, `GET /api/backtest/timeline` |
| Map (Leaflet) | `frontend/src/components/MapView.tsx` |
| Dashboard + HITL | `frontend/src/components/Dashboard.tsx`, `RecommendationPanel.tsx` |
| Backtest replay UI | `frontend/src/components/BacktestReplay.tsx` |
| Cape route overlay (ASSUMPTION) | `frontend/src/geo/routes.ts` |
| Offline tiles script | `scripts/cache_demo_tiles.py` |

## SRS Section 16 AC reconciliation

| Criterion | Met | Notes |
|-----------|-----|-------|
| Live map coloring | Yes | `/api/graph` + `/api/risk-scores/latest` |
| Backtest replay E2E | Yes | Trajectory + timeline + scrub/play |
| Default dashboard populated | Yes | `ensureBaselineData` + polling |
| Unrehearsed scenario | Yes | MALACCA/BAB_EL_MANDEB cascade + orchestrator |

## Demo notes

- Serve via `docker compose up` or `vite preview` — not `file://` (ESM).
- Phase 5 honest result: `no_crossing` at 0.35 shown in replay headline panel.
- Cape polylines are static demo waypoints, not graph edge geometry.

## Out of scope (confirmed)

Mobile layout, modeling changes, live GDELT in browser.