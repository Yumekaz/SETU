"""Windowed tensors from daily feature parquet."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

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
from app.forecast.split import ChronologicalLeakageError, ChronologicalSplit

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
    origin_dates: list[date] | None = None,
    target_dates: set[date] | None = None,
    corridors: list[str] | None = None,
) -> tuple[np.ndarray, np.ndarray, list[tuple[str, date]]]:
    """Return X [N,14,input_dim], y [N,7], meta list of (corridor, origin_date).

    Lookback always uses the full chronological timeline (matching inference).
    When ``origin_dates`` is set, only those dates are used as forecast origins.
    When ``target_dates`` is set, all horizon targets must fall in that set.
    """
    all_dates = sorted({date.fromisoformat(str(d)[:10]) for d in df["date"].unique()})
    allowed_origins = set(origin_dates) if origin_dates is not None else set(all_dates)
    corridor_list = corridors or list(CORRIDOR_ORDER)

    by_key: dict[tuple[str, date], dict] = {}
    for _, row in df.iterrows():
        d = date.fromisoformat(str(row["date"])[:10])
        by_key[(row["corridor"], d)] = row

    xs: list[np.ndarray] = []
    ys: list[np.ndarray] = []
    meta: list[tuple[str, date]] = []

    for corridor in corridor_list:
        for idx, origin in enumerate(all_dates):
            if origin not in allowed_origins:
                continue
            if idx < LOOKBACK_DAYS - 1:
                continue
            if idx + HORIZON_DAYS >= len(all_dates):
                continue
            lookback = all_dates[idx - LOOKBACK_DAYS + 1 : idx + 1]
            future = all_dates[idx + 1 : idx + 1 + HORIZON_DAYS]
            if target_dates is not None and not all(fd in target_dates for fd in future):
                continue
            window_rows = []
            ok = True
            for lb in lookback:
                key = (corridor, lb)
                if key not in by_key:
                    ok = False
                    break
                row = by_key[key]
                feats = [float(row[c]) for c in FEATURE_COLUMNS]
                window_rows.append(
                    np.array(feats + corridor_one_hot(corridor).tolist(), dtype=np.float32)
                )
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


def build_split_windows(
    df: pd.DataFrame,
    split: ChronologicalSplit,
    partition: Literal["train", "val", "test"],
    *,
    corridors: list[str] | None = None,
) -> tuple[np.ndarray, np.ndarray, list[tuple[str, date]]]:
    """Build windows for a chronological partition with leakage assertions."""
    origin_dates: list[date] = getattr(split, f"{partition}_dates")
    if not origin_dates:
        return np.zeros((0, LOOKBACK_DAYS, INPUT_DIM)), np.zeros((0, HORIZON_DAYS)), []

    allowed_origins = set(origin_dates)
    min_origin = min(origin_dates)
    xs, ys, meta = build_windows(
        df,
        origin_dates=origin_dates,
        target_dates=allowed_origins,
        corridors=corridors,
    )
    for _, origin in meta:
        if origin not in allowed_origins:
            raise ChronologicalLeakageError(
                f"window origin {origin} not in {partition} partition"
            )
        if origin < min_origin:
            raise ChronologicalLeakageError(
                f"window origin {origin} precedes {partition} min origin {min_origin}"
            )
    return xs, ys, meta
