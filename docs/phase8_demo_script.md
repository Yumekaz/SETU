# Phase 8 Demo Script

Timed walkthrough for **live presentation** and **video recording**. Target viewport: 1280px+.

## Prerequisites

```bash
bash scripts/demo-up.sh
# or local dev — see docs/phase8_solo_runbook.md
bash scripts/demo_preflight.sh   # must print PREFLIGHT=PASS
```

Open http://localhost:5173 → **Overview**.

---

## Full script (~11 min)

### A. Historical evidence — Time budget: 3 min

| Step | Action | Talk track |
|------|--------|------------|
| A1 | Switch to **Scenario replay** | Start with independently reproducible evidence, not a claim about a polished interface |
| A2 | Scrub to 2026-02-10 | SETU crosses its pre-locked threshold at 0.578125 |
| A3 | Show the reference event | That is 20 days before EIA's publicly reported March 2 Hormuz closure |
| A4 | State the boundary | The threshold came from a separate 17-day baseline; this is N=1 evidence, not broad accuracy proof |

### B. Operational response workflow — Time budget: 3 min

| Step | Action | Talk track |
|------|--------|------------|
| B1 | Switch to **Overview** and select corridor (HORMUZ or current highest) | The evidence layer feeds an operational decision workflow |
| B2 | Click **Run cascade + orchestrator** | Monte Carlo graph propagation → percentile bands |
| B3 | Cascade bands panel | Supply shortfall, price impact, SPR days |
| B4 | Recommendation panel | Pareto-feasible options with HITL approve/dismiss |
| B5 | (If asked) Mention GBNF + confidence gate | LLM extracts; deterministic code scores and decides |

### C. Situation awareness — Time budget: 2 min

| Step | Action | Talk track |
|------|--------|------------|
| C1 | Switch to **Maritime network** | Tie the decision to a real physical corridor |
| C2 | Change corridor focus | Dynamic route comparison and risk coloring refresh from the backend |
| C3 | Map overlay | Static route waypoints communicate route geometry; they are not asserted to be live vessel tracks |

### D. Alternate-corridor scenario — Time budget: 2 min

| Step | Action | Talk track |
|------|--------|------------|
| D1 | Return to **Overview** | Prove the pipeline is not limited to one corridor |
| D2 | Select **BAB_EL_MANDEB** (backup: MALACCA) | Different corridor, same pipeline |
| D3 | Run scenario | Show non-empty cascade + ≥1 recommendation option |

---

## Short script (~7 min) — EC-36 time overrun

Keep A2–A4, compress B to the cascade and recommendation panels, then keep D.

| Beat | Time budget |
|------|-------------|
| A historical evidence | 2 min |
| B operational response | 2.5 min |
| C maritime context | 1.5 min |
| D unrehearsed | 1 min |

---

## Video recording notes

- Record at 1920×1080 or 1280×720, 1280px min width in browser
- Narrate talk-track column; pause 2s on score grid and recommendation options
- End on the evidence boundary: "This is a reproducible N=1 result with a short baseline, and the limitations are documented."
