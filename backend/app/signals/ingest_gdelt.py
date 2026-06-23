"""Parse and normalize GDELT Events rows."""

from __future__ import annotations

import csv
import io
import json
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from app.signals.classify import passes_ingest_filter
from app.signals.config import AppConfig, load_config

ROOT = Path(__file__).resolve().parent.parent.parent.parent
SAMPLES_DIR = ROOT / "data" / "samples"

GDELT_HEADERS = [
    "GLOBALEVENTID", "SQLDATE", "MonthYear", "Year", "FractionDate",
    "Actor1Code", "Actor1Name", "Actor1CountryCode", "Actor1KnownGroupCode",
    "Actor1EthnicCode", "Actor1Religion1Code", "Actor1Religion2Code",
    "Actor1Type1Code", "Actor1Type2Code", "Actor1Type3Code",
    "Actor2Code", "Actor2Name", "Actor2CountryCode", "Actor2KnownGroupCode",
    "Actor2EthnicCode", "Actor2Religion1Code", "Actor2Religion2Code",
    "Actor2Type1Code", "Actor2Type2Code", "Actor2Type3Code",
    "IsRootEvent", "EventCode", "EventBaseCode", "EventRootCode", "QuadClass",
    "GoldsteinScale", "NumMentions", "NumSources", "NumArticles", "AvgTone",
    "Actor1Geo_Type", "Actor1Geo_FullName", "Actor1Geo_CountryCode", "Actor1Geo_ADM1Code",
    "Actor1Geo_Lat", "Actor1Geo_Long", "Actor1Geo_FeatureID",
    "Actor2Geo_Type", "Actor2Geo_FullName", "Actor2Geo_CountryCode", "Actor2Geo_ADM1Code",
    "Actor2Geo_Lat", "Actor2Geo_Long", "Actor2Geo_FeatureID",
    "ActionGeo_Type", "ActionGeo_FullName", "ActionGeo_CountryCode", "ActionGeo_ADM1Code",
    "ActionGeo_Lat", "ActionGeo_Long", "ActionGeo_FeatureID",
    "DATEADDED", "SOURCEURL",
]


def parse_sql_date(value: str) -> date:
    """Normalize GDELT SQLDATE (YYYYMMDD) to UTC date."""
    cleaned = (value or "").strip()
    if len(cleaned) != 8 or not cleaned.isdigit():
        raise ValueError(f"invalid SQLDATE: {value!r}")
    return date(int(cleaned[:4]), int(cleaned[4:6]), int(cleaned[6:8]))


def parse_goldstein(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def row_to_dict(row: list[str]) -> dict[str, str]:
    padded = row + [""] * max(0, len(GDELT_HEADERS) - len(row))
    return dict(zip(GDELT_HEADERS, padded[: len(GDELT_HEADERS)], strict=False))


def iter_csv_rows(text: str) -> Iterator[dict[str, str]]:
    reader = csv.reader(io.StringIO(text), delimiter="\t")
    for row in reader:
        if not row:
            continue
        yield row_to_dict(row)


def iter_zip_bytes(content: bytes) -> Iterator[dict[str, str]]:
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        csv_name = zf.namelist()[0]
        with zf.open(csv_name) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace").read()
    yield from iter_csv_rows(text)


def filter_rows(
    rows: list[dict[str, str]],
    config: AppConfig | None = None,
) -> list[dict[str, str]]:
    cfg = config or load_config()
    return [row for row in rows if passes_ingest_filter(row, cfg)]


def load_sample_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        wrapper = json.load(f)
    data = wrapper.get("data", {})
    if "rows" in data:
        rows = data["rows"]
        if rows and isinstance(rows[0], dict):
            return rows
    return []


def load_backtest_cache(path: Path | None = None) -> list[dict[str, str]]:
    cache_path = path or (SAMPLES_DIR / "gdelt_hormuz_backtest.json")
    with cache_path.open(encoding="utf-8") as f:
        payload = json.load(f)
    return payload.get("rows", [])


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")