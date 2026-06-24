#!/usr/bin/env python3
"""Train GRU checkpoint and write docs/gru_training_report.md."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

from app.forecast.config import DEFAULT_FEATURES_PATH  # noqa: E402
from app.forecast.dataset import load_features_df  # noqa: E402

from ml.forecast.train import train_gru, write_training_report  # noqa: E402


def main() -> int:
    if not DEFAULT_FEATURES_PATH.exists():
        print("missing parquet — run scripts/build_forecast_dataset.py first", file=sys.stderr)
        return 1
    df = load_features_df(DEFAULT_FEATURES_PATH)
    result = train_gru(seed=42)
    write_training_report(result, df)
    print(
        f"train_loss={result.train_loss:.6f} val_loss={result.val_loss:.6f} "
        f"gru={result.eligible_corridors} fallback={result.fallback_corridors}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
