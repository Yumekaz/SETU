"""Quantile (pinball) loss for risk score bands."""

from __future__ import annotations

import torch


def pinball_loss(pred: torch.Tensor, target: torch.Tensor, quantile: float) -> torch.Tensor:
    err = target - pred
    return torch.mean(torch.maximum(quantile * err, (quantile - 1.0) * err))


def quantile_band_loss(
    preds: torch.Tensor,
    target: torch.Tensor,
    *,
    quantiles: tuple[float, float, float] = (0.1, 0.5, 0.9),
) -> torch.Tensor:
    """preds: [batch, horizon, 3]; target: [batch, horizon]."""
    losses = []
    for i, q in enumerate(quantiles):
        losses.append(pinball_loss(preds[:, :, i], target, q))
    return sum(losses) / len(losses)