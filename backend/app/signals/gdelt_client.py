"""HTTP client for GDELT Events 2.0 public data (historical + recent).

Downloads, decompresses, filters, and caches GDELT export CSVs for the
backtest window and live ingestion use cases.
"""

from __future__ import annotations

import gzip
import io
import json
import logging
import time
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterator

import httpx

from app.signals.classify import passes_ingest_filter
from app.signals.config import AppConfig, load_config
from app.signals.ingest_gdelt import GDELT_HEADERS, row_to_dict

logger = logging.getLogger(__name__)

# GDELT v2 public endpoints
GDELT_MASTER_LIST_URL = "http://data.gdeltproject.org/gdeltv2/masterfilelist.txt"
GDELT_LAST_UPDATE_URL = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"
GDELT_REQUEST_DELAY_SECONDS = 1.0
GDELT_HTTP_TIMEOUT = 30.0
GDELT_MAX_RETRIES = 3


@dataclass
class PullStats:
    """Summary statistics from a GDELT pull operation."""
    files_downloaded: int = 0
    files_skipped: int = 0
    files_failed: int = 0
    rows_parsed: int = 0
    rows_accepted: int = 0
    rows_rejected: int = 0


@dataclass
class PullManifest:
    """Tracks downloaded files for resumable pulls."""
    completed_urls: set[str] = field(default_factory=set)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(sorted(self.completed_urls), indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> PullManifest:
        if not path.exists():
            return cls()
        try:
            urls = json.loads(path.read_text(encoding="utf-8"))
            return cls(completed_urls=set(urls))
        except (json.JSONDecodeError, TypeError):
            return cls()


def _parse_master_line(line: str) -> tuple[int, str, str] | None:
    """Parse a master file list line: 'size hash url'."""
    parts = line.strip().split()
    if len(parts) != 3:
        return None
    try:
        size = int(parts[0])
    except ValueError:
        return None
    return size, parts[1], parts[2]


def _url_to_date(url: str) -> date | None:
    """Extract date from GDELT export URL like '...20260201000000.export.CSV.zip'."""
    basename = url.rsplit("/", 1)[-1] if "/" in url else url
    if not basename or len(basename) < 14:
        return None
    date_str = basename[:8]
    try:
        return date(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]))
    except (ValueError, IndexError):
        return None


def filter_master_list(
    lines: list[str],
    start_date: date,
    end_date: date,
) -> list[tuple[str, date]]:
    """Filter master file list to .export.CSV.zip files within date range."""
    results: list[tuple[str, date]] = []
    for line in lines:
        parsed = _parse_master_line(line)
        if parsed is None:
            continue
        _, _, url = parsed
        if ".export.CSV" not in url:
            continue
        file_date = _url_to_date(url)
        if file_date is None:
            continue
        if start_date <= file_date <= end_date:
            results.append((url, file_date))
    return sorted(results, key=lambda x: x[0])


def _download_with_retry(
    client: httpx.Client,
    url: str,
    max_retries: int = GDELT_MAX_RETRIES,
) -> bytes | None:
    """Download a URL with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            resp = client.get(url, timeout=GDELT_HTTP_TIMEOUT)
            resp.raise_for_status()
            return resp.content
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            wait = 2 ** attempt
            logger.warning(
                "GDELT download attempt %d/%d failed for %s: %s (retrying in %ds)",
                attempt + 1, max_retries, url, exc, wait,
            )
            if attempt < max_retries - 1:
                time.sleep(wait)
    return None


def _decompress_export(content: bytes, url: str) -> str:
    """Decompress a GDELT export file (ZIP or GZ) to text."""
    if url.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            csv_name = zf.namelist()[0]
            with zf.open(csv_name) as raw:
                return io.TextIOWrapper(raw, encoding="utf-8", errors="replace").read()
    elif url.endswith(".gz"):
        return gzip.decompress(content).decode("utf-8", errors="replace")
    else:
        return content.decode("utf-8", errors="replace")


def _parse_rows(text: str) -> Iterator[dict[str, str]]:
    """Parse tab-delimited GDELT rows into dictionaries."""
    import csv as csv_mod
    reader = csv_mod.reader(io.StringIO(text), delimiter="\t")
    for row in reader:
        if not row:
            continue
        yield row_to_dict(row)


def pull_gdelt_historical(
    start_date: date,
    end_date: date,
    output_path: Path,
    *,
    config: AppConfig | None = None,
    manifest_path: Path | None = None,
    sample_interval: int = 4,
) -> PullStats:
    """Pull GDELT historical data for a date range, filter, and save.

    Args:
        start_date: Start of date range (inclusive).
        end_date: End of date range (inclusive).
        output_path: Path to write filtered JSON cache.
        config: App config for corridor/CAMEO filtering.
        manifest_path: Path for resume manifest file.
        sample_interval: Take every Nth file per day to manage volume.
            GDELT publishes 96 files/day (every 15 min).
            sample_interval=4 means 1 file/hour = 24 files/day.
    """
    cfg = config or load_config()
    stats = PullStats()
    manifest = PullManifest.load(manifest_path) if manifest_path else PullManifest()
    all_rows: list[dict[str, Any]] = []

    logger.info("Fetching GDELT master file list...")
    with httpx.Client() as client:
        master_content = _download_with_retry(client, GDELT_MASTER_LIST_URL)
        if master_content is None:
            logger.error("Failed to download GDELT master file list")
            return stats

        lines = master_content.decode("utf-8", errors="replace").splitlines()
        candidates = filter_master_list(lines, start_date, end_date)
        logger.info("Found %d export files in date range, sampling every %d", len(candidates), sample_interval)

        # Sample to reduce volume
        sampled = candidates[::sample_interval]
        logger.info("Will process %d files after sampling", len(sampled))

        for i, (url, file_date) in enumerate(sampled):
            if url in manifest.completed_urls:
                stats.files_skipped += 1
                continue

            content = _download_with_retry(client, url)
            if content is None:
                stats.files_failed += 1
                logger.warning("Failed to download %s after %d retries", url, GDELT_MAX_RETRIES)
                continue

            try:
                text = _decompress_export(content, url)
            except Exception as exc:
                stats.files_failed += 1
                logger.warning("Failed to decompress %s: %s", url, exc)
                continue

            file_accepted = 0
            for row in _parse_rows(text):
                stats.rows_parsed += 1
                if passes_ingest_filter(row, cfg):
                    stats.rows_accepted += 1
                    file_accepted += 1
                    all_rows.append(row)
                else:
                    stats.rows_rejected += 1

            stats.files_downloaded += 1
            manifest.completed_urls.add(url)

            if manifest_path and stats.files_downloaded % 50 == 0:
                manifest.save(manifest_path)

            if (i + 1) % 100 == 0:
                logger.info(
                    "Progress: %d/%d files, %d accepted rows so far",
                    i + 1, len(sampled), stats.rows_accepted,
                )

            time.sleep(GDELT_REQUEST_DELAY_SECONDS)

    # Sort by GLOBALEVENTID for deterministic output
    all_rows.sort(key=lambda r: str(r.get("GLOBALEVENTID", "")))

    # Deduplicate by GLOBALEVENTID
    seen_ids: set[str] = set()
    unique_rows: list[dict[str, Any]] = []
    for row in all_rows:
        eid = str(row.get("GLOBALEVENTID", ""))
        if eid and eid not in seen_ids:
            seen_ids.add(eid)
            unique_rows.append(row)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps({"rows": unique_rows}, indent=2, default=str),
        encoding="utf-8",
    )

    if manifest_path:
        manifest.save(manifest_path)

    logger.info(
        "GDELT pull complete: %d files downloaded, %d skipped, %d failed, "
        "%d rows parsed, %d accepted, %d unique saved",
        stats.files_downloaded, stats.files_skipped, stats.files_failed,
        stats.rows_parsed, stats.rows_accepted, len(unique_rows),
    )

    return stats


def fetch_recent_gdelt(
    *,
    config: AppConfig | None = None,
) -> list[dict[str, str]]:
    """Fetch the most recent GDELT export (last 15 min) and filter.

    This is the 'live' ingestion path for real-time signal updates.
    """
    cfg = config or load_config()
    accepted: list[dict[str, str]] = []

    with httpx.Client() as client:
        update_content = _download_with_retry(client, GDELT_LAST_UPDATE_URL)
        if update_content is None:
            logger.warning("Failed to fetch GDELT last update URL")
            return accepted

        for line in update_content.decode("utf-8", errors="replace").splitlines():
            parsed = _parse_master_line(line)
            if parsed is None:
                continue
            _, _, url = parsed
            if ".export.CSV" not in url:
                continue

            content = _download_with_retry(client, url)
            if content is None:
                continue

            try:
                text = _decompress_export(content, url)
            except Exception as exc:
                logger.warning("Failed to decompress recent export: %s", exc)
                continue

            for row in _parse_rows(text):
                if passes_ingest_filter(row, cfg):
                    accepted.append(row)
            break  # Only process the first (most recent) export file

    logger.info("Fetched %d relevant events from latest GDELT export", len(accepted))
    return accepted
