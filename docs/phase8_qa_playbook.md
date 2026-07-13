# Phase 8 Q&A Playbook

Prepared answers for judge probes (SRS §18 Task 4).

## Why not Kpler / Vortexa / Windward?

Those platforms **surface risk signals** from vessel and cargo data. SETU produces a **prescriptive, constraint-optimized recommendation** with quantified cascade impacts (supply shortfall, price, SPR days) and a reproducible historical replay. The current N=1 replay crosses 20 days before its reference point, but does not claim broad validated accuracy.

## How do you prevent LLM hallucinations affecting scores?

1. **GBNF-constrained extraction** — structured JSON only (`ml/grammars/signal_event.gbnf`)
2. **Confidence threshold** — low-confidence events rejected or typed UNKNOWN
3. **Deterministic downstream** — risk scores, Monte Carlo, Pareto, and orchestrator are pure code; no LLM in the decision layer
4. **Demo path default** — `SETU_EXTRACTOR_MODE=rules` for reproducible offline demo

## Isn't one historical crisis (N=1) too small to validate?

**Yes — we say so explicitly.** The replay crosses on 2026-02-10, 20 days before the 2026-03-02 reference point, using a 0.437501 threshold derived from a separate 17-day baseline. This is N=1 evidence with a short-baseline caveat, not statistical proof across crises. See `docs/backtest_results.md` and `docs/known_limitations.md` KL-05/KL-11.

## Why did February 28 not cross but March 2 did?

The score is intentionally based on same-day, source-deduplicated evidence for the selected corridor. The February 28 source set did not contain enough direct Hormuz evidence to cross the independently locked threshold. By March 2, direct closure reporting created a stronger, corroborated corridor signal. Earlier decayed signals are retained in the broader system context, but they are not allowed to substitute for direct same-day corridor evidence in this replay metric.

## What if GDELT or the network fails during the demo?

Show **offline path**: `POST /api/pipeline/run` with `{"source":"cache"}` reads the committed replay cache. Full stack runs without live API keys. Optional: disable Wi-Fi and refresh the overview.

## Why should India care?

~88% crude imports; Hormuz, Bab-el-Mandeb, and Malacca are single points of failure. SETU ties **geopolitical signals → graph cascade → procurement options** for national energy security decisions under time pressure.

## Are the route waypoints live vessel tracks?

No. They are static reference waypoints used to make the routing decision legible; the route comparison and risk data are backend-driven. SETU does not claim AIS-level vessel tracking (`docs/known_limitations.md`, KL-02).
