"""Daily Brent price series for price_lag features."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent.parent
TIMELINE_PATH = ROOT / "data" / "hormuz_2026_timeline.csv"


def load_brent_daily_series(
    start: date,
    end: date,
    *,
    timeline_path: Path | None = None,
) -> pd.Series:
    """Build daily Brent USD from cited timeline anchors (forward-filled)."""
    path = timeline_path or TIMELINE_PATH
    anchors: dict[date, float] = {}
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            d = date.fromisoformat(row["date"])
            anchors[d] = float(row["brent_usd"])

    if not anchors:
        raise ValueError(f"no Brent anchors in {path}")

    idx = pd.date_range(start, end, freq="D")
    series = pd.Series(index=idx, dtype=float)
    for d, price in sorted(anchors.items()):
        if start <= d <= end:
            series[pd.Timestamp(d)] = price
    series = series.sort_index().ffill().bfill()
    return series
