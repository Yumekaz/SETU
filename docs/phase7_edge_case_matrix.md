# Phase 7 Edge-Case Matrix

Maps SRS Sections 11–16 and §19 master register to test evidence or known limitations.

## Summary

| Status | Count |
|--------|-------|
| PASS | 41 |
| DEFERRED | 1 |

## Register

| ID | Category | SRS ref | Handling | Evidence | Status |
|----|----------|---------|----------|----------|--------|
| EC-01 | ingestion | §11 GBNF malformed JSON | Reject + log, no partial pass | tests/test_extraction.py | PASS |
| EC-02 | ingestion | §11 LLM hallucination | Confidence gate / UNKNOWN | tests/test_extraction.py | PASS |
| EC-03 | ingestion | §11 Duplicate events | Dedup before scoring | tests/test_dedup.py | PASS |
| EC-04 | ingestion | §11 Non-English text | Ingest filter rejects | tests/test_extraction.py | PASS |
| EC-05 | ingestion | §11 GDELT API downtime | Offline cache / SQLite | tests/test_phase1_offline.py | PASS |
| EC-06 | ingestion | §11 Outlier event skew | CAP_SINGLE dampening | tests/test_risk_scoring.py, docs/risk_scoring.md | PASS |
| EC-07 | ingestion | §11 Timezone mismatch | UTC normalization at ingest | tests/test_phase7_edge_cases.py | PASS |
| EC-08 | ingestion | §11 OFAC snapshot drift | Pinned snapshot ingest | tests/test_phase1_pipeline.py | PASS |
| EC-09 | modeling | §12 Disconnected graph | Surfaced as warning/loss | tests/test_graph_loader.py | PASS |
| EC-10 | modeling | §12 Zero/negative capacity | Fail at validate | tests/test_graph_loader.py | PASS |
| EC-11 | modeling | §12 MC non-convergence | Convergence check | tests/test_monte_carlo.py, docs/monte_carlo_convergence.md | PASS |
| EC-12 | modeling | §12 Thin corridor data | Wider conservative distribution | tests/test_propagate.py | PASS |
| EC-13 | modeling | §12 Extreme output clip | Bounded at model boundary | tests/test_monte_carlo.py | PASS |
| EC-14 | modeling | §12 Circular flow loops | DAG traversal terminates | tests/test_graph_loader.py | PASS |
| EC-15 | modeling | §13 Sparse data / NaN | Trend fallback corridors | tests/test_forecast_inference.py, tests/test_gru_model.py | PASS |
| EC-16 | modeling | §13 Chronological leakage | Automated split test | tests/test_chronological_split.py | PASS |
| EC-17 | modeling | §13 Single-crisis overfit | Honest limitation in docs | tests/test_phase7_edge_cases.py, docs/backtest_results.md | PASS |
| EC-18 | modeling | §13 Nonsense forecast band | Sanity on band width | tests/test_forecast_inference.py | PASS |
| EC-19 | decision | §14 No feasible option | NO_FEASIBLE_OPTION state | tests/test_orchestrator_options.py | PASS |
| EC-20 | decision | §14 Pareto tie-break | Deterministic sort | tests/test_pareto.py | PASS |
| EC-21 | decision | §14 Recommendation flapping | Hysteresis guard | tests/test_orchestrator_hysteresis.py, tests/test_phase4_api.py | PASS |
| EC-22 | decision | §14 Expired pending rec | EXPIRED status | tests/test_phase4_api.py | PASS |
| EC-23 | decision | §14 Stale upstream inputs | inputs_as_of on Recommendation | tests/test_phase7_edge_cases.py | PASS |
| EC-24 | backtest | §15 Ground-truth ambiguity | Locked reference point | docs/backtest_results.md, tests/test_backtest_metrics.py | PASS |
| EC-25 | backtest | §15 N=1 sample honesty | Explicit limitations section | tests/test_phase7_edge_cases.py | PASS |
| EC-26 | backtest | §15 Data gaps early window | Documented in backtest_results | docs/backtest_results.md | PASS |
| EC-27 | backtest | §15 Hindsight bias | Locked inclusion criteria | tests/test_backtest_integrity.py | PASS |
| EC-28 | frontend | §16 Live network failure | Full offline cache path | tests/test_phase1_offline.py, architecture | PASS |
| EC-29 | frontend | §16 Map tile failure | Offline tile fallback | frontend/src/components/MapView.tsx, scripts/cache_demo_tiles.py | PASS |
| EC-30 | frontend | §16 Unrehearsed scenario | MALACCA + BAB_EL_MANDEB flows | tests/test_phase6_api.py, tests/test_phase7_edge_cases.py | PASS |
| EC-31 | frontend | §16 Empty default state | ensureBaselineData bootstrap | tests/test_phase6_api.py, frontend Dashboard.test.tsx | PASS |
| EC-32 | frontend | §16 Multi-presenter handoff | SQLite single source | docs/known_limitations.md KL-07 | DEFERRED |
| EC-33 | process | §19 Secrets in repo | Automated scan gate | scripts/scan_secrets.py | PASS |
| EC-34 | process | §19 Non-reproducible env | Docker repro script | scripts/verify_docker_repro.sh | PASS |
| EC-35 | process | §19 Schema drift | Frozen schemas + tests/test_schemas.py | tests/test_schemas.py | PASS |
| EC-36 | process | §19 Demo time overrun | Short script time budgets | docs/phase8_demo_script.md | PASS |
| EC-37 | process | §19 Key personnel absent | Solo runbook + rehearsal log | docs/phase8_solo_runbook.md | PASS |
| EC-38 | chaos | §17 Corrupt graph | 422 graph load failed | tests/test_phase7_chaos.py | PASS |
| EC-39 | chaos | §17 Malformed extraction batch | Pipeline completes, rejects logged | tests/test_phase7_chaos.py | PASS |
| EC-40 | chaos | §17 Invalid corridor | 422 supported list | tests/test_phase7_chaos.py | PASS |
| EC-41 | chaos | §17 Missing cascade rec | 404 not 500 | tests/test_phase7_chaos.py | PASS |
| EC-42 | chaos | §17 Backend unreachable UI | Bootstrap/polling error state | frontend/src/components/Dashboard.test.tsx | PASS |

## Machine-readable rows

Format: `id|status|evidence`

```
EC-01|PASS|tests/test_extraction.py
EC-02|PASS|tests/test_extraction.py
EC-03|PASS|tests/test_dedup.py
EC-04|PASS|tests/test_extraction.py
EC-05|PASS|tests/test_phase1_offline.py
EC-06|PASS|tests/test_risk_scoring.py
EC-07|PASS|tests/test_phase7_edge_cases.py
EC-08|PASS|tests/test_phase1_pipeline.py
EC-09|PASS|tests/test_graph_loader.py
EC-10|PASS|tests/test_graph_loader.py
EC-11|PASS|tests/test_monte_carlo.py
EC-12|PASS|tests/test_propagate.py
EC-13|PASS|tests/test_monte_carlo.py
EC-14|PASS|tests/test_graph_loader.py
EC-15|PASS|tests/test_forecast_inference.py
EC-16|PASS|tests/test_chronological_split.py
EC-17|PASS|tests/test_phase7_edge_cases.py
EC-18|PASS|tests/test_forecast_inference.py
EC-19|PASS|tests/test_orchestrator_options.py
EC-20|PASS|tests/test_pareto.py
EC-21|PASS|tests/test_orchestrator_hysteresis.py
EC-22|PASS|tests/test_phase4_api.py
EC-23|PASS|tests/test_phase7_edge_cases.py
EC-24|PASS|tests/test_backtest_metrics.py
EC-25|PASS|tests/test_phase7_edge_cases.py
EC-26|PASS|docs/backtest_results.md
EC-27|PASS|tests/test_backtest_integrity.py
EC-28|PASS|tests/test_phase1_offline.py
EC-29|PASS|frontend/src/components/MapView.tsx
EC-30|PASS|tests/test_phase7_edge_cases.py
EC-31|PASS|tests/test_phase6_api.py
EC-32|DEFERRED|docs/known_limitations.md#KL-07
EC-33|PASS|scripts/scan_secrets.py
EC-34|PASS|scripts/verify_docker_repro.sh
EC-35|PASS|tests/test_schemas.py
EC-36|PASS|docs/phase8_demo_script.md
EC-37|PASS|docs/phase8_solo_runbook.md
EC-38|PASS|tests/test_phase7_chaos.py
EC-39|PASS|tests/test_phase7_chaos.py
EC-40|PASS|tests/test_phase7_chaos.py
EC-41|PASS|tests/test_phase7_chaos.py
EC-42|PASS|frontend/src/components/Dashboard.test.tsx
```