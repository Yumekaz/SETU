#!/usr/bin/env python3
"""Build data/forecast/daily_features.parquet from cached GDELT + Brent timeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.forecast.config import DEFAULT_FEATURES_PATH  # noqa: E402
from app.forecast.features import build_daily_features, write_features_parquet  # noqa: E402


def main() -> int:
    df = build_daily_features()
    write_features_parquet(df, DEFAULT_FEATURES_PATH)
    meta = {
        "rows": len(df),
        "columns": list(df.columns),
        "date_min": df["date"].min(),
        "date_max": df["date"].max(),
        "per_corridor": df.groupby("corridor").size().to_dict(),
    }
    meta_path = DEFAULT_FEATURES_PATH.parent / "daily_features_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"wrote {DEFAULT_FEATURES_PATH} ({len(df)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())