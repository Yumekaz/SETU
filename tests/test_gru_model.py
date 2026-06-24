"""GRU model and training smoke tests."""

from __future__ import annotations

import json
from pathlib import Path

import torch

from app.forecast.config import DEFAULT_CHECKPOINT_PATH, INPUT_DIM
from app.forecast.dataset import build_windows, load_features_df
from ml.forecast.gru_model import RiskGRUForecaster
from ml.forecast.loss import quantile_band_loss
from ml.forecast.train import train_gru

SCRATCH = Path("/tmp/grok-goal-87d4d5399344/implementer")


def test_gru_forward_pass_no_nan_and_ordered_quantiles() -> None:
    model = RiskGRUForecaster()
    x = torch.rand(4, 14, INPUT_DIM)
    pred = model(x)
    assert pred.shape == (4, 7, 3)
    assert not torch.isnan(pred).any()
    assert (pred[:, :, 0] <= pred[:, :, 1]).all()
    assert (pred[:, :, 1] <= pred[:, :, 2]).all()


def test_quantile_loss_finite_on_random_batch() -> None:
    pred = torch.rand(8, 7, 3)
    target = torch.rand(8, 7)
    loss = quantile_band_loss(pred, target)
    assert float(loss.item()) == float(loss.item())
    assert not torch.isnan(loss)


def test_train_gru_produces_checkpoint_and_log() -> None:
    result = train_gru(seed=42, epochs=5)
    assert DEFAULT_CHECKPOINT_PATH.exists()
    assert result.train_loss == result.train_loss
    assert "HORMUZ" in result.eligible_corridors or result.fallback_corridors

    SCRATCH.mkdir(parents=True, exist_ok=True)
    (SCRATCH / "gru_train.log").write_text(
        json.dumps(
            {
                "train_loss": result.train_loss,
                "val_loss": result.val_loss,
                "eligible": result.eligible_corridors,
                "fallback": result.fallback_corridors,
            },
            indent=2,
        ),
        encoding="utf-8",
    )