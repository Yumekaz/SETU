"""Train shared GRU on daily_features.parquet."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, TensorDataset

from app.forecast.config import (
    CORRIDOR_ORDER,
    DEFAULT_CHECKPOINT_PATH,
    DEFAULT_FEATURES_PATH,
    DEFAULT_REPORT_PATH,
    MIN_TRAIN_DAYS,
)
from app.forecast.dataset import build_windows, eligible_corridors_for_gru, load_features_df
from app.forecast.split import assert_no_chronological_leakage, chronological_split, unique_sorted_dates
from ml.forecast.gru_model import RiskGRUForecaster
from ml.forecast.loss import quantile_band_loss

ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class TrainResult:
    train_loss: float
    val_loss: float
    eligible_corridors: list[str]
    fallback_corridors: list[str]
    training_data_through: str
    history: list[dict[str, float]]


def train_gru(
    features_path: Path | None = None,
    checkpoint_path: Path | None = None,
    *,
    seed: int = 42,
    epochs: int = 80,
    batch_size: int = 16,
    lr: float = 1e-3,
) -> TrainResult:
    torch.manual_seed(seed)
    np.random.seed(seed)

    df = load_features_df(features_path or DEFAULT_FEATURES_PATH)
    dates = unique_sorted_dates(df)
    split = chronological_split(dates)
    assert_no_chronological_leakage(split)

    eligible = eligible_corridors_for_gru(df)
    fallback = [c for c in CORRIDOR_ORDER if c not in eligible]

    x_train, y_train, _ = build_windows(df, dates=split.train_dates)
    x_val, y_val, _ = build_windows(df, dates=split.val_dates)

    if len(x_train) == 0:
        raise ValueError("no training windows — check feature parquet")

    model = RiskGRUForecaster()
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    train_ds = TensorDataset(torch.from_numpy(x_train), torch.from_numpy(y_train))
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=False)

    x_val_t = torch.from_numpy(x_val) if len(x_val) else None
    y_val_t = torch.from_numpy(y_val) if len(y_val) else None

    history: list[dict[str, float]] = []
    best_val = float("inf")
    best_state = None

    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0
        batches = 0
        for xb, yb in train_loader:
            opt.zero_grad()
            pred = model(xb)
            loss = quantile_band_loss(pred, yb)
            if torch.isnan(loss):
                raise ValueError(f"NaN loss at epoch {epoch}")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            epoch_loss += float(loss.item())
            batches += 1
        train_loss = epoch_loss / max(batches, 1)

        val_loss = train_loss
        if x_val_t is not None and len(x_val_t) > 0:
            model.eval()
            with torch.no_grad():
                pred = model(x_val_t)
                val_loss = float(quantile_band_loss(pred, y_val_t).item())

        history.append({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss})
        if val_loss < best_val:
            best_val = val_loss
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)

    ckpt_path = checkpoint_path or DEFAULT_CHECKPOINT_PATH
    ckpt_path.parent.mkdir(parents=True, exist_ok=True)
    training_through = max(split.train_dates).isoformat()
    torch.save(
        {
            "state_dict": model.state_dict(),
            "eligible_corridors": sorted(eligible),
            "fallback_corridors": fallback,
            "training_data_through": training_through,
            "seed": seed,
            "final_train_loss": history[-1]["train_loss"],
            "final_val_loss": history[-1]["val_loss"],
        },
        ckpt_path,
    )

    return TrainResult(
        train_loss=history[-1]["train_loss"],
        val_loss=history[-1]["val_loss"],
        eligible_corridors=sorted(eligible),
        fallback_corridors=fallback,
        training_data_through=training_through,
        history=history,
    )


def write_training_report(result: TrainResult, df: pd.DataFrame, path: Path | None = None) -> Path:
    out = path or DEFAULT_REPORT_PATH
    hormuz_rows = len(df[df["corridor"] == "HORMUZ"])
    lines = [
        "# GRU Training Report — Phase 3",
        "",
        "## Data honesty (Hormuz-heavy cache)",
        "",
        "The GDELT backtest cache contains ~55 Hormuz-window events. "
        "BAB_EL_MANDEB and MALACCA have thin daily series; those corridors use "
        "`TREND_FALLBACK` when below MIN_TRAIN_DAYS or variance threshold. "
        "This is directional evidence, not statistically proven accuracy.",
        "",
        f"- Total feature rows: {len(df)}",
        f"- HORMUZ rows: {hormuz_rows}",
        "",
        "## Corridor routing",
        "",
        f"- GRU corridors: {', '.join(result.eligible_corridors) or '(none)'}",
        f"- TREND_FALLBACK corridors: {', '.join(result.fallback_corridors)}",
        "",
        "## Final metrics",
        "",
        f"- Training data through: {result.training_data_through}",
        f"- Final train loss: {result.train_loss:.6f}",
        f"- Final val loss: {result.val_loss:.6f}",
        "",
        "## Loss curve (epoch, train_loss, val_loss)",
        "",
        "| epoch | train_loss | val_loss |",
        "|---:|---:|---:|",
    ]
    for row in result.history[:: max(1, len(result.history) // 20)]:
        lines.append(
            f"| {int(row['epoch'])} | {row['train_loss']:.6f} | {row['val_loss']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Band approach",
            "",
            "Quantile pinball loss (p10/p50/p90) with sigmoid-bounded scores.",
        ]
    )
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out