"""Backtest configuration loader."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from app.models.generated import Corridor

ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_CONFIG_PATH = ROOT / "data" / "config" / "backtest.yaml"


@dataclass(frozen=True)
class BacktestConfig:
    window_start: date
    window_end: date
    corridor: Corridor
    risk_threshold: float
    reference_point_date: date
    reference_point_label: str
    seed: int
    n_simulations: int
    cache_path: Path
    timeline_path: Path
    ground_truth_compare_date: date


def load_backtest_config(path: Path | None = None) -> BacktestConfig:
    config_path = Path(os.getenv("SETU_BACKTEST_CONFIG", str(path or DEFAULT_CONFIG_PATH)))
    with config_path.open(encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f)
    b = raw["backtest"]
    root = config_path.resolve().parent.parent.parent
    cache = Path(b["cache_path"])
    timeline = Path(b["timeline_path"])
    if not cache.is_absolute():
        cache = root / cache
    if not timeline.is_absolute():
        timeline = root / timeline
    return BacktestConfig(
        window_start=date.fromisoformat(str(b["window_start"])),
        window_end=date.fromisoformat(str(b["window_end"])),
        corridor=next(c for c in Corridor if c.value == str(b["corridor"])),
        risk_threshold=float(b["risk_threshold"]),
        reference_point_date=date.fromisoformat(str(b["reference_point_date"])),
        reference_point_label=str(b["reference_point_label"]),
        seed=int(b["seed"]),
        n_simulations=int(b["n_simulations"]),
        cache_path=cache,
        timeline_path=timeline,
        ground_truth_compare_date=date.fromisoformat(str(b["ground_truth_compare_date"])),
    )
