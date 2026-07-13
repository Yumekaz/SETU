#!/usr/bin/env python3
"""Evaluate whether a baseline-derived Hormuz alert threshold is possible."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.backtest.calibration import calibrate_threshold  # noqa: E402
from app.backtest.config import load_backtest_config  # noqa: E402
from app.backtest.replay import load_backtest_events  # noqa: E402


def main() -> None:
    config = load_backtest_config()
    events = load_backtest_events(config)
    result = calibrate_threshold(
        events,
        config=config,
        baseline_start=date(2026, 1, 15),
        baseline_end=date(2026, 1, 31),
        target_false_positive_rate=0.05,
    )
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
