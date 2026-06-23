"""Deterministic corridor pre-classification and GDELT row filtering."""

from __future__ import annotations

from typing import Any

from app.signals.config import AppConfig, load_config

GDELT_TEXT_FIELDS = (
    "ActionGeo_FullName",
    "Actor1Name",
    "Actor2Name",
    "Actor1Geo_FullName",
    "Actor2Geo_FullName",
    "SOURCEURL",
)


def _safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def is_relevant_cameo(event_code: str, config: AppConfig | None = None) -> bool:
    cfg = config or load_config()
    code = (event_code or "").strip()
    if not code:
        return False
    root = code[:2]
    return root in cfg.cameo_allowlist_roots


def _text_blob(row: dict[str, str]) -> str:
    parts = [str(row.get(field, "") or "") for field in GDELT_TEXT_FIELDS]
    return " ".join(parts).lower()


def _bbox_hit(row: dict[str, str], config: AppConfig) -> str | None:
    lat = _safe_float(row.get("ActionGeo_Lat"))
    lon = _safe_float(row.get("ActionGeo_Long"))
    if lat is None or lon is None:
        return None
    for corridor, spec in config.corridors.items():
        if spec.bbox.contains(lat, lon):
            return corridor
    return None


def _keyword_hit(text: str, config: AppConfig) -> str | None:
    for corridor, spec in config.corridors.items():
        if any(kw in text for kw in spec.keywords):
            return corridor
    return None


def classify_corridor(row: dict[str, str], config: AppConfig | None = None) -> str | None:
    """Return corridor enum string or None if row is not corridor-relevant."""
    cfg = config or load_config()
    bbox_corridor = _bbox_hit(row, cfg)
    if bbox_corridor:
        return bbox_corridor
    return _keyword_hit(_text_blob(row), cfg)


def is_english_source(row: dict[str, str]) -> bool:
    """English-only MVP filter: require ASCII-heavy snippet text."""
    snippet = build_raw_snippet(row)
    if not snippet:
        return False
    ascii_chars = sum(1 for ch in snippet if ord(ch) < 128)
    return ascii_chars / max(len(snippet), 1) >= 0.85


def build_raw_snippet(row: dict[str, str], max_len: int = 500) -> str:
    geo = row.get("ActionGeo_FullName") or row.get("Actor1Geo_FullName") or ""
    actors = " | ".join(
        part
        for part in (
            row.get("Actor1Name", ""),
            row.get("Actor2Name", ""),
            row.get("EventCode", ""),
        )
        if part
    )
    url = row.get("SOURCEURL", "")
    snippet = f"{geo} — {actors} — {url}".strip(" —")
    return snippet[:max_len]


def passes_ingest_filter(row: dict[str, str], config: AppConfig | None = None) -> bool:
    cfg = config or load_config()
    if not is_relevant_cameo(str(row.get("EventCode", "")), cfg):
        return False
    if classify_corridor(row, cfg) is None:
        return False
    return is_english_source(row)