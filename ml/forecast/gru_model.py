"""2-layer GRU forecaster per Appendix D."""

from __future__ import annotations

import torch
from torch import nn

from app.forecast.config import HORIZON_DAYS, INPUT_DIM


class RiskGRUForecaster(nn.Module):
    def __init__(
        self,
        input_dim: int = INPUT_DIM,
        hidden_size: int = 64,
        horizon: int = HORIZON_DAYS,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        self.gru = nn.GRU(
            input_dim,
            hidden_size,
            num_layers=2,
            batch_first=True,
            dropout=dropout,
        )
        self.head = nn.Linear(hidden_size, horizon * 3)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.gru(x)
        last = out[:, -1, :]
        raw = self.head(last).view(-1, HORIZON_DAYS, 3)
        p10 = torch.sigmoid(raw[:, :, 0])
        p50 = torch.sigmoid(raw[:, :, 1])
        p90 = torch.sigmoid(raw[:, :, 2])
        p50 = torch.clamp(p50, 0.0, 1.0)
        p10 = torch.minimum(p10, p50)
        p90 = torch.maximum(p90, p50)
        return torch.stack([p10, p50, p90], dim=-1)