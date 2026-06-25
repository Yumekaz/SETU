# Procurement Orchestrator — Phase 4

Deterministic option generation and Pareto filtering per SRS Section 14 and Appendix C.

## Option templates

For trigger corridor `c` and `CascadeResult` bands:

| Type | Feasibility | time_score | cost_score | risk_score |
|------|-------------|------------|------------|------------|
| Reroute | `max(alt_route_penalty_days) > 0` on graph edges for `c` | `penalty / max_penalty_days_cap` | `penalty * flow * 0.1 / cap` | `price_p50 / max_price_cap` |
| SPR drawdown | `spr_days_required.p50 <= spr_reserve_days_available` | `spr_days / reserve_days` | `spr_days * spr_unit_cost_proxy` | `throughput_p50 / max_throughput_cap` |
| Corridor mix | alt corridors exist with penalties | `avg_penalty * 0.6 / cap` | `avg_penalty * mix_shift_cost_proxy / cap` | `price_p50 * 0.7 / max_price_cap` |

All scores clamped to `[0, 1]`; lower is better.

Config: [`data/config/orchestrator.yaml`](../data/config/orchestrator.yaml)

## Pareto (Appendix C)

- A dominates B if `cost, time, risk` are all `<=` and at least one strict `<`.
- Frontier sorted by `risk_score` ascending, then `time_score` ascending.

## Infeasibility

When zero candidates pass hard constraints → `status: NO_FEASIBLE_OPTION`, `options: []`, non-null `operator_note`.

## Hysteresis

Both `new_risk` (from `trigger_risk_score`) and `prior_risk` (from stored recommendation) use `min(option.risk_score)` over feasible candidates on the same cascade inputs. New recommendation blocked (HTTP 409) when a `PENDING_APPROVAL` exists for the same corridor and `|new_risk - prior_risk| < hysteresis_risk_delta`. Use `?force=true` for demo rehearsal only.

## Expiry

`PENDING_APPROVAL` rows older than `pending_ttl_hours` transition to `EXPIRED` on list/latest reads.

## Provenance

Every `Recommendation` carries `source_cascade_id`, optional `source_forecast_id`, and `inputs_as_of`.