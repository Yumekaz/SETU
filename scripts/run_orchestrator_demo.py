#!/usr/bin/env python3
"""Run orchestrator on committed cascade fixtures (verification helper)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.models.generated import CascadeResult  # noqa: E402
from app.orchestrator.orchestrate import run_orchestrator  # noqa: E402
from app.simulation.graph_loader import load_network_graph  # noqa: E402


def main() -> int:
    fixture = ROOT / "data/fixtures/cascade_results.json"
    rows = json.loads(fixture.read_text())
    network = load_network_graph()
    for row in rows:
        cascade = CascadeResult.model_validate(row)
        rec = run_orchestrator(cascade, network)
        print(
            f"{cascade.corridor.value}: status={rec.status.value} "
            f"options={len(rec.options)} pareto="
            f"{sum(1 for o in rec.options if o.is_pareto_optimal)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())