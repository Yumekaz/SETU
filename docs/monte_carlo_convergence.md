# Monte Carlo Convergence — Phase 2

Hormuz corridor, seed=42, triangular duration distribution.
Chosen `n_simulations`: **500** (first n where p50 drift vs prior step < 2.0%).

| n_simulations | p10 price % | p50 price % | p90 price % | p50 drift vs prev % |
|---:|---:|---:|---:|---:|
| 100 | 4.2450 | 6.0113 | 7.2078 |  |
| 500 | 4.1504 | 6.0864 | 7.5201 | 1.25 |
| 1000 | 4.1504 | 6.0864 | 7.5823 | 0.00 |
| 2000 | 4.1504 | 6.0864 | 7.5823 | 0.00 |

## Hormuz directional check

Hormuz p50 price impact (6.09%) is **positive** and within order of magnitude of the Mar 2026 Brent anchor (~8.8%); not an exact match by design.

CI uses `SETU_MC_N_SIMULATIONS=500` for speed; production default is 1000.
