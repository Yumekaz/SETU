"""Forecast layer constants."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_FEATURES_PATH = ROOT / "data" / "forecast" / "daily_features.parquet"
DEFAULT_CHECKPOINT_PATH = ROOT / "data" / "checkpoints" / "gru" / "model.pt"
DEFAULT_REPORT_PATH = ROOT / "docs" / "gru_training_report.md"

LOOKBACK_DAYS = 14
HORIZON_DAYS = 7
MIN_TRAIN_DAYS = 30
MIN_SCORE_VARIANCE = 1e-4
FEATURE_COLUMNS = ("risk_score", "goldstein_aggregate", "event_count", "price_lag")
CORRIDOR_ORDER = ("HORMUZ", "BAB_EL_MANDEB", "MALACCA", "OTHER")
N_CORRIDORS = len(CORRIDOR_ORDER)
INPUT_DIM = len(FEATURE_COLUMNS) + N_CORRIDORS