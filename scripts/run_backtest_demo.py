#!/usr/bin/env python3
"""Run Phase 5 Hormuz backtest and print headline metrics."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "ml"))

from app.backtest.run import run_backtest


def main() -> int:
    result = run_backtest()
    print(f"status={result.status}")
    print(f"reference_point_date={result.reference_point_date}")
    print(f"first_crossing_date={result.first_crossing_date}")
    print(f"lead_time_days={result.lead_time_days}")
    print(f"crossing_summary={result.crossing_summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())