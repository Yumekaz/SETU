# Cascade Model — Phase 2

Deterministic NetworkX + NumPy math (no LLM). Implementation: [`backend/app/simulation/`](../backend/app/simulation/).

## Duration sampling

Triangular distributions per corridor in [`data/config/corridor_distributions.yaml`](../data/config/corridor_distributions.yaml).

## Single-draw metrics (Appendix B)

1. **Shortfall:** traverse corridor-dependent edges from the chokepoint; propagate shock with per-node capacity caps; `S = flow_lost(c) × (duration_days / 30)`
2. **Price impact %:** `elasticity × log(1 + S / total_demand)` — elasticity default 8.0; capped at 50%
3. **Refinery throughput impact %:** propagated refinery node losses (capacity-capped) scaled by duration — capped at 100%
4. **SPR days required:** `S / spr_draw_rate` — draw rate 0.35 mbpd (ASSUMPTION); capped at 365 days

## Monte Carlo aggregation

`n_simulations` duration draws → percentile bands p10/p50/p90 per metric.

## Hormuz directional anchor

Timeline Brent: ~78.20 (2026-02-28) → ~85.10 (2026-03-11) ≈ **+8.8%**.

Phase 2 does not force exact match — AC requires **positive p50** in the Hormuz directionally consistent band documented in [`docs/phase2_signoff.md`](phase2_signoff.md).