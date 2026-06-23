"""Load corridor and scoring configuration from data/config/corridors.yaml."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_CONFIG_PATH = ROOT / "data" / "config" / "corridors.yaml"


@dataclass(frozen=True)
class BBox:
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float

    def contains(self, lat: float, lon: float) -> bool:
        return (
            self.lat_min <= lat <= self.lat_max
            and self.lon_min <= lon <= self.lon_max
        )


@dataclass(frozen=True)
class CorridorConfig:
    keywords: tuple[str, ...]
    bbox: BBox


@dataclass(frozen=True)
class ScoringConfig:
    w_sev: float
    w_gold: float
    w_type: float
    recency_tau_days: float
    cap_single_event: float
    confidence_threshold: float
    trend_stable_epsilon: float
    top_k_events: int


@dataclass(frozen=True)
class AppConfig:
    corridors: dict[str, CorridorConfig]
    cameo_allowlist_roots: tuple[str, ...]
    event_type_weights: dict[str, float]
    scoring: ScoringConfig


def _parse_bbox(raw: dict[str, float]) -> BBox:
    return BBox(
        lat_min=float(raw["lat_min"]),
        lat_max=float(raw["lat_max"]),
        lon_min=float(raw["lon_min"]),
        lon_max=float(raw["lon_max"]),
    )


def load_config(path: Path | None = None) -> AppConfig:
    config_path = Path(os.getenv("SETU_CONFIG_PATH", str(path or DEFAULT_CONFIG_PATH)))
    with config_path.open(encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f)

    corridors: dict[str, CorridorConfig] = {}
    for name, spec in raw["corridors"].items():
        corridors[name] = CorridorConfig(
            keywords=tuple(k.lower() for k in spec["keywords"]),
            bbox=_parse_bbox(spec["bbox"]),
        )

    scoring_raw = raw["scoring"]
    scoring = ScoringConfig(
        w_sev=float(scoring_raw["w_sev"]),
        w_gold=float(scoring_raw["w_gold"]),
        w_type=float(scoring_raw["w_type"]),
        recency_tau_days=float(scoring_raw["recency_tau_days"]),
        cap_single_event=float(scoring_raw["cap_single_event"]),
        confidence_threshold=float(scoring_raw["confidence_threshold"]),
        trend_stable_epsilon=float(scoring_raw["trend_stable_epsilon"]),
        top_k_events=int(scoring_raw["top_k_events"]),
    )

    return AppConfig(
        corridors=corridors,
        cameo_allowlist_roots=tuple(raw["cameo_allowlist_roots"]),
        event_type_weights={k: float(v) for k, v in raw["event_type_weights"].items()},
        scoring=scoring,
    )