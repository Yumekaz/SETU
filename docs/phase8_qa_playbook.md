# Phase 8 Q&A Playbook

Prepared answers for judge probes (SRS §18 Task 4).

## Why not Kpler / Vortexa / Windward?

Those platforms **surface risk signals** from vessel and cargo data. SETU produces a **prescriptive, constraint-optimized recommendation** with quantified cascade impacts (supply shortfall, price, SPR days) and backtest-validated lead-time framing. Monitoring vs decision support.

## How do you prevent LLM hallucinations affecting scores?

1. **GBNF-constrained extraction** — structured JSON only (`ml/grammars/signal_event.gbnf`)
2. **Confidence threshold** — low-confidence events rejected or typed UNKNOWN
3. **Deterministic downstream** — risk scores, Monte Carlo, Pareto, and orchestrator are pure code; no LLM in the decision layer
4. **Demo path default** — `SETU_EXTRACTOR_MODE=rules` for reproducible offline demo

## Isn't one historical crisis (N=1) too small to validate?

**Yes — we say so explicitly.** Backtest headline shows `no_crossing` at threshold 0.35 for the locked Hormuz 2026 window. We claim **directional credibility** and **pipeline integrity**, not statistical proof across many crises. See `docs/backtest_results.md` and `docs/known_limitations.md` KL-05.

## What if GDELT or the network fails during the demo?

Show **offline path**: `POST /api/pipeline/run` with `{"source":"cache"}` reads `data/samples/gdelt_hormuz_backtest.json`. Full stack runs without live API keys. Optional: disable Wi-Fi and refresh dashboard.

## Why should India care?

~88% crude imports; Hormuz, Bab-el-Mandeb, and Malacca are single points of failure. SETU ties **geopolitical signals → graph cascade → procurement options** for national energy security decisions under time pressure.

## Cape route overlay?

Labeled **demo ASSUMPTION** in UI — static waypoints for narrative, not graph edge geometry (`docs/phase6_signoff.md`).