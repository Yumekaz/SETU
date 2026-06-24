"""Windowed tensors from daily feature parquet."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from app.forecast.config import (
    CORRIDOR_ORDER,
    FEATURE_COLUMNS,
    HORIZON_DAYS,
    LOOKBACK_DAYS,
    MIN_SCORE_VARIANCE,
    MIN_TRAIN_DAYS,
)

CORRIDOR_TO_IDX = {c: i for i, c in enumerate(CORRIDOR_ORDER)}
N_CORRIDORS = len(CORRIDOR_ORDER)
INPUT_DIM = len(FEATURE_COLUMNS) + N_CORRIDORS


def corridor_one_hot(corridor: str) -> np.ndarray:
    vec = np.zeros(N_CORRIDORS, dtype=np.float32)
    vec[CORRIDOR_TO_IDX[corridor]] = 1.0
    return vec


def load_features_df(path: str | Path) -> pd.DataFrame:
    return pd.read_parquet(Path(path))


def corridor_train_eligible(df: pd.DataFrame, corridor: str) -> bool:
    sub = df[df["corridor"] == corridor]
    if len(sub) < MIN_TRAIN_DAYS:
        return False
    return float(sub["risk_score"].var()) >= MIN_SCORE_VARIANCE


def eligible_corridors_for_gru(df: pd.DataFrame) -> set[str]:
    return {c for c in CORRIDOR_ORDER if corridor_train_eligible(df, c)}


def build_windows(
    df: pd.DataFrame,
    *,
    dates: list[date] | None = None,
) -> tuple[np.ndarray, np.ndarray, list[tuple[str, date]]]:
    """Return X [N,14,input_dim], y [N,7], meta list of (corridor, origin_date)."""
    pivot_dates = sorted({date.fromisoformat(str(d)[:10]) for d in df["date"].unique()})
    if dates is not None:
        allowed = set(dates)
        pivot_dates = [d for d in pivot_dates if d in allowed]

    by_key: dict[tuple[str, date], dict] = {}
    for _, row in df.iterrows():
        d = date.fromisoformat(str(row["date"])[:10])
        by_key[(row["corridor"], d)] = row

    xs: list[np.ndarray] = []
    ys: list[np.ndarray] = []
    meta: list[tuple[str, date]] = []

    for corridor in CORRIDOR_ORDER:
        for i, origin in enumerate(pivot_dates):
            if i < LOOKBACK_DAYS - 1:
                continue
            if i + HORIZON_DAYS >= len(pivot_dates):
                continue
            lookback = pivot_dates[i - LOOKBACK_DAYS + 1 : i + 1]
            future = pivot_dates[i + 1 : i + 1 + HORIZON_DAYS]
            window_rows = []
            ok = True
            for lb in lookback:
                key = (corridor, lb)
                if key not in by_key:
                    ok = False
                    break
                row = by_key[key]
                feats = [float(row[c]) for c in FEATURE_COLUMNS]
                window_rows.append(np.array(feats + corridor_one_hot(corridor).tolist(), dtype=np.float32))
            if not ok:
                continue
            targets = []
            for fd in future:
                key = (corridor, fd)
                if key not in by_key:
                    ok = False
                    break
                targets.append(float(by_key[key]["risk_score"]))
            if not ok:
                continue
            xs.append(np.stack(window_rows))
            ys.append(np.array(targets, dtype=np.float32))
            meta.append((corridor, origin))

    if not xs:
        return np.zeros((0, LOOKBACK_DAYS, INPUT_DIM)), np.zeros((0, HORIZON_DAYS)), []
    return np.stack(xs), np.stack(ys), meta