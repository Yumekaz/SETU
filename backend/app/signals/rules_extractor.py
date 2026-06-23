"""Deterministic GDELT → partial SignalEvent fields (CI / no-model fallback)."""

from __future__ import annotations

from typing import Any

from app.signals.ingest_gdelt import parse_goldstein, parse_sql_date

CAMEO_TO_EVENT_TYPE: dict[str, str] = {
    "14": "MILITARY",
    "15": "MILITARY",
    "16": "MILITARY",
    "17": "MILITARY",
    "18": "MILITARY",
    "19": "MILITARY",
    "04": "DIPLOMATIC",
    "05": "DIPLOMATIC",
    "07": "ACCIDENT",
    "08": "INFRASTRUCTURE",
    "09": "PIRACY",
}


def _event_type_from_cameo(event_code: str) -> str:
    code = (event_code or "").strip()
    if not code:
        return "UNKNOWN"
    root = code[:2]
    return CAMEO_TO_EVENT_TYPE.get(root, "UNKNOWN")


def _severity_from_goldstein(goldstein: float) -> float:
    return min(max(abs(goldstein) / 10.0, 0.05), 1.0)


def extract_from_gdelt(row: dict[str, str], pre_corridor: str) -> dict[str, Any]:
    event_date = parse_sql_date(str(row.get("SQLDATE", "")))
    goldstein = parse_goldstein(row.get("GoldsteinScale"))
    event_type = _event_type_from_cameo(str(row.get("EventCode", "")))
    severity = _severity_from_goldstein(goldstein)
    confidence = 0.7 if event_type != "UNKNOWN" else 0.35
    return {
        "corridor": pre_corridor,
        "event_type": event_type,
        "severity": round(severity, 3),
        "confidence": confidence,
        "event_date": event_date.isoformat(),
        "_goldstein": goldstein,
    }