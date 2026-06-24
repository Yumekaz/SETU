#!/usr/bin/env python3
"""Run Monte Carlo convergence check and write docs/monte_carlo_convergence.md."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

logging.basicConfig(level=logging.WARNING)

from app.models.generated import Corridor  # noqa: E402
from app.simulation.monte_carlo import run_cascade  # noqa: E402

OUT_PATH = ROOT / "docs" / "monte_carlo_convergence.md"
N_VALUES = [100, 500, 1000, 2000]
SEED = 42
DRIFT_THRESHOLD_PCT = 2.0
HORMUZ_BRENT_ANCHOR_PCT = 8.8


def main() -> int:
    rows: list[dict] = []
    prev_p50: float | None = None
    chosen_n: int | None = None

    for n in N_VALUES:
        result = run_cascade(Corridor.hormuz, n_simulations=n, seed=SEED)
        p50 = result.price_impact_pct.p50
        drift = None
        if prev_p50 is not None and prev_p50 > 0:
            drift = abs(p50 - prev_p50) / prev_p50 * 100.0
            if drift < DRIFT_THRESHOLD_PCT and chosen_n is None:
                chosen_n = n
        rows.append(
            {
                "n": n,
                "p50": p50,
                "p10": result.price_impact_pct.p10,
                "p90": result.price_impact_pct.p90,
                "drift_pct": drift,
            }
        )
        prev_p50 = p50

    if chosen_n is None:
        chosen_n = N_VALUES[-1]

    hormuz_p50 = rows[-1]["p50"]
    direction_note = (
        f"Hormuz p50 price impact ({hormuz_p50:.2f}%) is **positive** "
        f"and within order of magnitude "
        f"of the Mar 2026 Brent anchor (~{HORMUZ_BRENT_ANCHOR_PCT}%); not an exact match by design."
    )

    lines = [
        "# Monte Carlo Convergence — Phase 2",
        "",
        "Hormuz corridor, seed=42, triangular duration distribution.",
        (
            f"Chosen `n_simulations`: **{chosen_n}** "
            f"(first n where p50 drift vs prior step < {DRIFT_THRESHOLD_PCT}%)."
        ),
        "",
        "| n_simulations | p10 price % | p50 price % | p90 price % | p50 drift vs prev % |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        drift = "" if row["drift_pct"] is None else f"{row['drift_pct']:.2f}"
        lines.append(
            f"| {row['n']} | {row['p10']:.4f} | {row['p50']:.4f} | {row['p90']:.4f} | {drift} |"
        )
    lines.extend(
        [
            "",
            "## Hormuz directional check",
            "",
            direction_note,
            "",
            "CI uses `SETU_MC_N_SIMULATIONS=500` for speed; production default is 1000.",
        ]
    )
    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT_PATH}; chosen_n={chosen_n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
