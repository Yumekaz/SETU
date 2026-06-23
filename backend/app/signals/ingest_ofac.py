"""Pinned OFAC SDN snapshot → SANCTION SignalEvent stubs (secondary source)."""

from __future__ import annotations

import csv
import json
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

from app.models.generated import SignalEvent

ROOT = Path(__file__).resolve().parent.parent.parent.parent
OFAC_SAMPLE = ROOT / "data" / "samples" / "ofac_sdn_sample.json"
PINNED_SNAPSHOT_DATE = date(2026, 6, 23)

ENERGY_KEYWORDS = ("oil", "crude", "energy", "petroleum", "shipping", "tanker")


def _is_energy_related(name: str, program: str) -> bool:
    blob = f"{name} {program}".lower()
    return any(keyword in blob for keyword in ENERGY_KEYWORDS)


def load_ofac_rows(path: Path | None = None) -> list[dict[str, str]]:
    sample_path = path or OFAC_SAMPLE
    with sample_path.open(encoding="utf-8") as f:
        wrapper = json.load(f)
    data = wrapper["data"]
    if "rows" in data:
        return data["rows"]
    # CSV embedded as text fallback
    rows: list[dict[str, str]] = []
    reader = csv.DictReader(data["csv_text"].splitlines())
    rows.extend(reader)
    return rows


def ofac_rows_to_events(rows: list[dict[str, str]]) -> list[SignalEvent]:
    events: list[SignalEvent] = []
    ingested_at = datetime(2026, 6, 23, 12, 0, 0, tzinfo=timezone.utc)
    for row in rows:
        name = row.get("sdn_name") or row.get("SDN_Name") or ""
        program = row.get("program") or row.get("Program") or ""
        if not _is_energy_related(name, program):
            continue
        event_id = uuid.uuid5(uuid.NAMESPACE_URL, f"ofac-{row.get('ent_num', name)}")
        events.append(
            SignalEvent.model_validate(
                {
                    "event_id": str(event_id),
                    "corridor": "HORMUZ",
                    "event_type": "SANCTION",
                    "severity": 0.75,
                    "goldstein_scale": -5.0,
                    "confidence": 0.8,
                    "event_date": PINNED_SNAPSHOT_DATE,
                    "ingested_at": ingested_at,
                    "source_url": "https://www.treasury.gov/ofac/downloads/sdn.csv",
                    "raw_text_snippet": f"OFAC SDN: {name} — program {program}"[:500],
                }
            )
        )
    return events