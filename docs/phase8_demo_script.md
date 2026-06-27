# Phase 8 Demo Script

Timed walkthrough for **live presentation** and **video recording**. Target viewport: 1280px+.

## Prerequisites

```bash
bash scripts/demo-up.sh
# or local dev — see docs/phase8_solo_runbook.md
bash scripts/demo_preflight.sh   # must print PREFLIGHT=PASS
```

Open http://localhost:5173 → **Dashboard** tab.

---

## Full script (~11 min)

### A. Baseline dashboard — Time budget: 2 min

| Step | Action | Talk track |
|------|--------|------------|
| A1 | Show health badge (phase 8, v1.0.0) | SETU is decision support, not a monitoring dashboard |
| A2 | Corridor score grid | Four corridors scored from cached GDELT + rules extraction |
| A3 | Risk trend chart | Historical replay of daily scores |
| A4 | Forecast bands panel | p10/p50/p90 — honest uncertainty, not fake precision |

### B. Live disruption — Time budget: 3 min

| Step | Action | Talk track |
|------|--------|------------|
| B1 | Select corridor (HORMUZ or current highest) | Trigger a disruption scenario |
| B2 | Click **Run cascade + orchestrator** | Monte Carlo graph propagation → percentile bands |
| B3 | Cascade bands panel | Supply shortfall, price impact, SPR days |
| B4 | Recommendation panel | Pareto-feasible options with HITL approve/dismiss |
| B5 | (If asked) Mention GBNF + confidence gate | LLM extracts; deterministic code scores and decides |

### C. Backtest replay — Time budget: 4 min

| Step | Action | Talk track |
|------|--------|------------|
| C1 | Switch to **Backtest Replay** tab | Credibility climax — real Hormuz 2026 window |
| C2 | Scrub timeline / press Play | Point-in-time scores vs news events |
| C3 | Headline panel (`no_crossing` at 0.35) | We report honestly: N=1 crisis, modest lead-time claim |
| C4 | Map overlay | Corridor risk coloring synced to replay date |

### D. Unrehearsed scenario — Time budget: 2 min

| Step | Action | Talk track |
|------|--------|------------|
| D1 | Return to **Dashboard** | Prove robustness, not a single rehearsed corridor |
| D2 | Select **BAB_EL_MANDEB** (backup: MALACCA) | Different corridor, same pipeline |
| D3 | Run scenario | Show non-empty cascade + ≥1 recommendation option |

---

## Short script (~7 min) — EC-36 time overrun

Skip A3 trend deep-dive. Compress C to 2 min (scrub to headline only, skip full play). Keep D.

| Beat | Time budget |
|------|-------------|
| A baseline | 1.5 min |
| B disruption | 2.5 min |
| C backtest | 2 min |
| D unrehearsed | 1 min |

---

## Video recording notes

- Record at 1920×1080 or 1280×720, 1280px min width in browser
- Narrate talk-track column; pause 2s on score grid and recommendation options
- End on backtest honesty line: "We claim decision support with documented limitations"