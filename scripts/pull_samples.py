#!/usr/bin/env python3
"""Pull and cache real sample data from GDELT, OFAC, EIA, and FRED."""

from __future__ import annotations

import csv
import io
import json
import os
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = ROOT / "data" / "samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

TIMEOUT = 60.0
USER_AGENT = "SETU-Phase0/0.1.0 (research; contact: setu@example.com)"


def _write_json(name: str, payload: object, meta: dict | None = None) -> Path:
    out = SAMPLES_DIR / name
    wrapper = {
        "pulled_at": datetime.now(timezone.utc).isoformat(),
        "source": meta or {},
        "data": payload,
    }
    out.write_text(json.dumps(wrapper, indent=2), encoding="utf-8")
    print(f"  wrote {out}")
    return out


def pull_gdelt(client: httpx.Client) -> None:
    """Pull a small slice of GDELT Events CSV (no API key required)."""
    print("Pulling GDELT...")
    meta = {
        "provider": "GDELT Project",
        "format": "GDELT 2.0 Events export CSV (tab-delimited)",
        "note": "Public direct download; no API key",
    }

    rows: list[dict[str, str]] = []
    headers: list[str] = []
    source_file: str | None = None

    # Prefer latest 15-minute export from GDELT 2.0 lastupdate.txt
    try:
        lastupdate = client.get(
            "http://data.gdeltproject.org/gdeltv2/lastupdate.txt", timeout=TIMEOUT
        )
        lastupdate.raise_for_status()
        for line in lastupdate.text.splitlines():
            if "export.CSV.zip" in line:
                source_file = line.split()[-1]
                break
    except httpx.HTTPError as exc:
        print(f"  lastupdate.txt failed: {exc}")

    candidate_urls: list[str] = []
    if source_file:
        candidate_urls.append(source_file)

    # Legacy daily exports as fallback
    today = datetime.now(timezone.utc)
    from datetime import timedelta

    for day_offset in range(1, 8):
        dt = today - timedelta(days=day_offset)
        ymd = dt.strftime("%Y%m%d")
        candidate_urls.append(
            f"http://data.gdeltproject.org/events/{ymd}.export.CSV.zip"
        )

    for zip_url in candidate_urls:
        try:
            resp = client.get(zip_url, timeout=TIMEOUT)
            if resp.status_code != 200:
                continue
            with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                csv_name = zf.namelist()[0]
                with zf.open(csv_name) as raw:
                    text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace")
                    reader = csv.reader(text, delimiter="\t")
                    for i, row in enumerate(reader):
                        if i == 0:
                            # GDELT exports have no header row — use canonical column names
                            headers = [
                                "GLOBALEVENTID",
                                "SQLDATE",
                                "MonthYear",
                                "Year",
                                "FractionDate",
                                "Actor1Code",
                                "Actor1Name",
                                "Actor1CountryCode",
                                "Actor1KnownGroupCode",
                                "Actor1EthnicCode",
                                "Actor1Religion1Code",
                                "Actor1Religion2Code",
                                "Actor1Type1Code",
                                "Actor1Type2Code",
                                "Actor1Type3Code",
                                "Actor2Code",
                                "Actor2Name",
                                "Actor2CountryCode",
                                "Actor2KnownGroupCode",
                                "Actor2EthnicCode",
                                "Actor2Religion1Code",
                                "Actor2Religion2Code",
                                "Actor2Type1Code",
                                "Actor2Type2Code",
                                "Actor2Type3Code",
                                "IsRootEvent",
                                "EventCode",
                                "EventBaseCode",
                                "EventRootCode",
                                "QuadClass",
                                "GoldsteinScale",
                                "NumMentions",
                                "NumSources",
                                "NumArticles",
                                "AvgTone",
                                "Actor1Geo_Type",
                                "Actor1Geo_FullName",
                                "Actor1Geo_CountryCode",
                                "Actor1Geo_ADM1Code",
                                "Actor1Geo_Lat",
                                "Actor1Geo_Long",
                                "Actor1Geo_FeatureID",
                                "Actor2Geo_Type",
                                "Actor2Geo_FullName",
                                "Actor2Geo_CountryCode",
                                "Actor2Geo_ADM1Code",
                                "Actor2Geo_Lat",
                                "Actor2Geo_Long",
                                "Actor2Geo_FeatureID",
                                "ActionGeo_Type",
                                "ActionGeo_FullName",
                                "ActionGeo_CountryCode",
                                "ActionGeo_ADM1Code",
                                "ActionGeo_Lat",
                                "ActionGeo_Long",
                                "ActionGeo_FeatureID",
                                "DATEADDED",
                                "SOURCEURL",
                            ]
                            record = dict(zip(headers, row, strict=False))
                            rows.append(record)
                        elif i <= 50:
                            record = dict(zip(headers, row, strict=False))
                            rows.append(record)
                        else:
                            break
            source_file = zip_url
            meta["url"] = zip_url
            break
        except (httpx.HTTPError, zipfile.BadZipFile, KeyError) as exc:
            print(f"  skip {zip_url}: {exc}")
            continue

    if not rows:
        raise RuntimeError("Could not download any GDELT export file")

    _write_json(
        "gdelt_events_sample.json",
        {"row_count": len(rows), "columns": headers, "rows": rows},
        {**meta, "source_file": source_file},
    )


def pull_ofac(client: httpx.Client) -> None:
    """Pull OFAC SDN list (public CSV)."""
    print("Pulling OFAC SDN...")
    csv_url = "https://www.treasury.gov/ofac/downloads/sdn.csv"
    meta = {
        "provider": "US Treasury OFAC",
        "url": csv_url,
        "format": "SDN CSV",
        "note": "Public download; no API key",
    }

    resp = client.get(csv_url, timeout=TIMEOUT)
    resp.raise_for_status()

    reader = csv.reader(io.StringIO(resp.text))
    rows = []
    for i, row in enumerate(reader):
        rows.append(row)
        if i >= 25:
            break

    _write_json(
        "ofac_sdn_sample.json",
        {
            "row_count": len(rows),
            "columns": [
                "ent_num",
                "sdn_name",
                "sdn_type",
                "program",
                "title",
                "call_sign",
                "vess_type",
                "tonnage",
                "grt",
                "vess_flag",
                "vess_owner",
                "remarks",
            ],
            "rows": rows,
        },
        meta,
    )


def pull_eia(client: httpx.Client) -> None:
    """Pull EIA data if API key present; else documented fallback sample."""
    print("Pulling EIA...")
    api_key = os.getenv("EIA_API_KEY", "").strip()
    meta = {
        "provider": "US EIA Open Data",
        "series": "PET.RBRTE.R2 (Brent spot, daily)",
        "docs": "https://www.eia.gov/opendata/",
    }

    if api_key:
        url = "https://api.eia.gov/v2/petroleum/pri/spt/data/"
        params = {
            "api_key": api_key,
            "frequency": "daily",
            "data[0]": "value",
            "facets[series][]": "RBRTE",
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": 10,
        }
        resp = client.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        payload = resp.json()
        meta["url"] = str(resp.url).split("api_key")[0] + "api_key=REDACTED"
        meta["live"] = True
        _write_json("eia_brent_sample.json", payload, meta)
        return

    # Fallback: minimal valid sample documenting expected v2 API response shape
    print("  EIA_API_KEY not set — writing documented fallback sample")
    fallback = {
        "response": {
            "total": 2,
            "dateFormat": "YYYY-MM-DD",
            "frequency": "daily",
            "data": [
                {"period": "2026-06-20", "value": 82.45, "series": "RBRTE"},
                {"period": "2026-06-19", "value": 81.90, "series": "RBRTE"},
            ],
        },
        "request": {
            "command": "/v2/petroleum/pri/spt/data/",
            "params": {
                "frequency": "daily",
                "data[0]": "value",
                "facets[series][]": "RBRTE",
            },
        },
    }
    meta["live"] = False
    meta["note"] = (
        "Fallback sample — set EIA_API_KEY in .env for live pull. "
        "Shape matches EIA Open Data API v2 response."
    )
    _write_json("eia_brent_sample.json", fallback, meta)


def pull_fred(client: httpx.Client) -> None:
    """Pull FRED Brent series if API key present; else documented fallback."""
    print("Pulling FRED...")
    api_key = os.getenv("FRED_API_KEY", "").strip()
    series_id = "DCOILBRENTEU"
    meta = {
        "provider": "FRED (Federal Reserve Bank of St. Louis)",
        "series_id": series_id,
        "docs": "https://fred.stlouisfed.org/series/DCOILBRENTEU",
    }

    if api_key:
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "api_key": api_key,
            "file_type": "json",
            "series_id": series_id,
            "sort_order": "desc",
            "limit": 10,
        }
        resp = client.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        payload = resp.json()
        meta["url"] = "https://api.stlouisfed.org/fred/series/observations"
        meta["live"] = True
        _write_json("fred_brent_sample.json", payload, meta)
        return

    # Public CSV fallback (no key) — FRED allows CSV download without API key
    csv_url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        resp = client.get(csv_url, timeout=TIMEOUT)
        resp.raise_for_status()
        lines = resp.text.strip().splitlines()
        header = lines[0] if lines else ""
        observations = []
        for line in lines[1:11]:
            parts = line.split(",")
            if len(parts) >= 2:
                observations.append({"date": parts[0], "value": parts[1]})
        payload = {
            "series_id": series_id,
            "source": "public_csv",
            "csv_header": header,
            "observations": observations,
        }
        meta["url"] = csv_url
        meta["live"] = True
        meta["note"] = "Pulled from public FRED CSV export (no API key required)"
        _write_json("fred_brent_sample.json", payload, meta)
        return
    except httpx.HTTPError as exc:
        print(f"  FRED CSV fallback failed: {exc}")

    fallback = {
        "count": 2,
        "observations": [
            {"realtime_start": "2026-06-20", "realtime_end": "2026-06-20",
             "date": "2026-06-20", "value": "82.45"},
            {"realtime_start": "2026-06-19", "realtime_end": "2026-06-19",
             "date": "2026-06-19", "value": "81.90"},
        ],
        "series_id": series_id,
    }
    meta["live"] = False
    meta["note"] = (
        "Fallback sample — set FRED_API_KEY in .env for live API pull. "
        "Shape matches FRED series/observations JSON endpoint."
    )
    _write_json("fred_brent_sample.json", fallback, meta)


def main() -> int:
    print(f"Writing samples to {SAMPLES_DIR}")
    headers = {"User-Agent": USER_AGENT}

    with httpx.Client(headers=headers, follow_redirects=True) as client:
        pull_gdelt(client)
        pull_ofac(client)
        pull_eia(client)
        pull_fred(client)

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())