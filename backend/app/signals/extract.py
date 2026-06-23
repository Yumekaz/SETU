"""Merge LLM/rules partial extraction with GDELT metadata into SignalEvent."""

from __future__ import annotations

import os
import sys
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pydantic import ValidationError

from app.models.generated import EventType, SignalEvent
from app.signals.classify import build_raw_snippet, classify_corridor, passes_ingest_filter
from app.signals.config import AppConfig, load_config
from app.signals.ingest_gdelt import parse_goldstein, parse_sql_date
from app.signals.rules_extractor import extract_from_gdelt

ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@dataclass(frozen=True)
class ExtractionResult:
    status: str
    event: SignalEvent | None = None
    reason: str | None = None
    source_id: str | None = None
    payload: dict[str, Any] | None = None


def _extractor_mode() -> str:
    return os.getenv("SETU_EXTRACTOR_MODE", "rules").strip().lower()


def _llm_partial(snippet: str, corridor: str) -> dict[str, Any]:
    from ml.extraction.llama_runner import extract_fields

    return extract_fields(snippet=snippet, corridor=corridor)


def _normalize_url(url: str) -> str:
    parsed = urlparse(url if "://" in url else f"https://{url}")
    if not parsed.netloc:
        return "https://example.com/unknown-source"
    return url if "://" in url else f"https://{url}"


def _merge_partial(
    partial: dict[str, Any],
    row: dict[str, str],
    *,
    ingested_at: datetime | None = None,
) -> SignalEvent:
    event_id = uuid.uuid5(uuid.NAMESPACE_URL, str(row.get("GLOBALEVENTID", uuid.uuid4())))
    goldstein = partial.get("_goldstein")
    if goldstein is None:
        goldstein = parse_goldstein(row.get("GoldsteinScale"))

    ingested = ingested_at or datetime.now(timezone.utc)
    sql_date = str(row.get("SQLDATE", ""))
    event_date_raw = partial.get("event_date") or parse_sql_date(sql_date).isoformat()
    if isinstance(event_date_raw, date):
        event_date_value = event_date_raw
    else:
        event_date_value = date.fromisoformat(str(event_date_raw))

    return SignalEvent.model_validate(
        {
            "event_id": str(event_id),
            "corridor": partial["corridor"],
            "event_type": partial["event_type"],
            "severity": float(partial["severity"]),
            "goldstein_scale": float(goldstein),
            "confidence": float(partial["confidence"]),
            "event_date": event_date_value,
            "ingested_at": ingested,
            "source_url": _normalize_url(str(row.get("SOURCEURL", "https://example.com/unknown"))),
            "raw_text_snippet": build_raw_snippet(row),
        }
    )


def extract_signal(
    row: dict[str, str],
    *,
    config: AppConfig | None = None,
    ingested_at: datetime | None = None,
) -> ExtractionResult:
    cfg = config or load_config()
    source_id = str(row.get("GLOBALEVENTID", ""))
    if not passes_ingest_filter(row, cfg):
        return ExtractionResult(
            status="rejected",
            reason="ingest_filter",
            source_id=source_id,
            payload={"row_id": source_id},
        )
    pre_corridor = classify_corridor(row, cfg)
    if pre_corridor is None:
        return ExtractionResult(
            status="rejected",
            reason="no_corridor",
            source_id=source_id,
            payload={"row_id": source_id},
        )

    snippet = build_raw_snippet(row)
    mode = _extractor_mode()
    partial: dict[str, Any]
    try:
        if mode == "llm":
            partial = _llm_partial(snippet, pre_corridor)
        else:
            partial = extract_from_gdelt(row, pre_corridor)
    except Exception as exc:  # noqa: BLE001 — extraction failures are logged, not fatal
        partial = extract_from_gdelt(row, pre_corridor)
        partial["_fallback_reason"] = str(exc)

    try:
        event = _merge_partial(partial, row, ingested_at=ingested_at)
    except (ValidationError, ValueError, KeyError) as exc:
        return ExtractionResult(
            status="rejected",
            reason="validation_error",
            source_id=source_id,
            payload={"error": str(exc), "partial": partial},
        )

    if event.confidence < cfg.scoring.confidence_threshold:
        return ExtractionResult(
            status="rejected",
            reason="low_confidence",
            event=event,
            source_id=source_id,
            payload=event.model_dump(mode="json"),
        )
    if event.event_type == EventType.unknown:
        return ExtractionResult(
            status="rejected",
            reason="unknown_type",
            event=event,
            source_id=source_id,
            payload=event.model_dump(mode="json"),
        )

    return ExtractionResult(
        status="accepted",
        event=event,
        source_id=source_id,
        payload=event.model_dump(mode="json"),
    )
