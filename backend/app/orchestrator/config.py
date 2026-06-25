"""Orchestrator configuration loader."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_CONFIG_PATH = ROOT / "data" / "config" / "orchestrator.yaml"


@dataclass(frozen=True)
class OrchestratorConfig:
    spr_reserve_days_available: float
    max_penalty_days_cap: float
    max_price_impact_cap_pct: float
    max_throughput_impact_cap_pct: float
    spr_unit_cost_proxy: float
    mix_shift_cost_proxy: float
    hysteresis_risk_delta: float
    pending_ttl_hours: int


def load_orchestrator_config(path: Path | None = None) -> OrchestratorConfig:
    config_path = Path(os.getenv("SETU_ORCHESTRATOR_CONFIG", str(path or DEFAULT_CONFIG_PATH)))
    with config_path.open(encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f)
    o = raw["orchestrator"]
    return OrchestratorConfig(
        spr_reserve_days_available=float(o["spr_reserve_days_available"]),
        max_penalty_days_cap=float(o["max_penalty_days_cap"]),
        max_price_impact_cap_pct=float(o["max_price_impact_cap_pct"]),
        max_throughput_impact_cap_pct=float(o["max_throughput_impact_cap_pct"]),
        spr_unit_cost_proxy=float(o["spr_unit_cost_proxy"]),
        mix_shift_cost_proxy=float(o["mix_shift_cost_proxy"]),
        hysteresis_risk_delta=float(o["hysteresis_risk_delta"]),
        pending_ttl_hours=int(o["pending_ttl_hours"]),
    )
