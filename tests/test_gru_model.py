"""GRU model and training smoke tests."""

from __future__ import annotations

from pathlib import Path

import torch
from app.forecast.config import INPUT_DIM

from ml.forecast.gru_model import RiskGRUForecaster
from ml.forecast.loss import quantile_band_loss
from ml.forecast.train import train_gru


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


def test_train_gru_produces_checkpoint_and_log(tmp_path: Path) -> None:
    ckpt = tmp_path / "model.pt"
    result = train_gru(seed=42, epochs=5, checkpoint_path=ckpt)
    assert ckpt.exists()
    assert (ckpt.parent / "model_meta.json").exists()
    assert result.train_loss == result.train_loss
    assert "HORMUZ" in result.eligible_corridors or result.fallback_corridors
    state = torch.load(ckpt, map_location="cpu", weights_only=True)
    assert len(state) > 0
