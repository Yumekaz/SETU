#!/usr/bin/env python3
"""Build gdelt_hormuz_backtest.json from GDELT daily exports (Feb–Jun 2026)."""

from __future__ import annotations

import json
import sys
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

from app.signals.ingest_gdelt import filter_rows, iter_zip_bytes, load_sample_rows  # noqa: E402

OUT_PATH = ROOT / "data" / "samples" / "gdelt_hormuz_backtest.json"
SAMPLE_PATH = ROOT / "data" / "samples" / "gdelt_events_sample.json"
TIMEOUT = 45.0
TARGET_ROWS = 55

# Strategic dates across the Hormuz backtest window (weekly-ish sampling).
PULL_DATES = [
    date(2026, 2, 7),
    date(2026, 2, 14),
    date(2026, 2, 21),
    date(2026, 2, 28),
    date(2026, 3, 4),
    date(2026, 3, 11),
    date(2026, 3, 18),
    date(2026, 3, 25),
    date(2026, 4, 8),
    date(2026, 4, 22),
    date(2026, 5, 1),
    date(2026, 5, 15),
    date(2026, 6, 1),
    date(2026, 6, 15),
    date(2026, 6, 23),
]


def _pull_day(client: httpx.Client, day: date) -> list[dict[str, str]]:
    urls = [
        f"http://data.gdeltproject.org/events/{day.strftime('%Y%m%d')}.export.CSV.zip",
        f"http://data.gdeltproject.org/gdeltv2/{day.strftime('%Y%m%d')}000000.export.CSV.zip",
    ]
    for url in urls:
        try:
            resp = client.get(url, timeout=TIMEOUT)
            if resp.status_code != 200:
                continue
            return list(iter_zip_bytes(resp.content))
        except (httpx.HTTPError, zipfile.BadZipFile, IndexError, KeyError):
            continue
    return []


def build_backtest(*, use_network: bool = True) -> dict[str, object]:
    collected: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    if use_network:
        with httpx.Client() as client:
            for day in PULL_DATES:
                if len(collected) >= TARGET_ROWS:
                    break
                for row in filter_rows(_pull_day(client, day)):
                    event_id = str(row.get("GLOBALEVENTID", ""))
                    if event_id in seen_ids:
                        continue
                    collected.append(row)
                    seen_ids.add(event_id)
                    if len(collected) >= TARGET_ROWS:
                        break

    for row in filter_rows(load_sample_rows(SAMPLE_PATH)):
        event_id = str(row.get("GLOBALEVENTID", ""))
        if event_id not in seen_ids:
            collected.append(row)
            seen_ids.add(event_id)

    if len(collected) < TARGET_ROWS:
        raise RuntimeError(
            f"Only collected {len(collected)} filtered rows; need >= {TARGET_ROWS}. "
            "Re-run with network access."
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window_start": "2026-02-01",
        "window_end": "2026-06-30",
        "row_count": len(collected),
        "rows": collected,
    }


def main() -> int:
    use_network = "--offline" not in sys.argv
    payload = build_backtest(use_network=use_network)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {OUT_PATH} ({payload['row_count']} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
