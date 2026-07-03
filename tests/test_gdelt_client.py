"""Tests for GDELT Events 2.0 HTTP client and edge cases EC-43 to EC-46."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.signals.gdelt_client import (  # noqa: E402
    PullManifest,
    _parse_master_line,
    _url_to_date,
    filter_master_list,
)


def test_parse_master_line() -> None:
    line = "12345 abcdef http://data.gdeltproject.org/gdeltv2/20260302000000.export.CSV.zip"
    parsed = _parse_master_line(line)
    assert parsed is not None
    size, md5_hash, url = parsed
    assert size == 12345
    assert md5_hash == "abcdef"
    assert "20260302000000.export.CSV.zip" in url


def test_url_to_date() -> None:
    url = "http://data.gdeltproject.org/gdeltv2/20260302121500.export.CSV.zip"
    d = _url_to_date(url)
    assert d == date(2026, 3, 2)


def test_filter_master_list() -> None:
    lines = [
        "100 hash1 http://data.gdeltproject.org/gdeltv2/20260201000000.export.CSV.zip",
        "200 hash2 http://data.gdeltproject.org/gdeltv2/20260302000000.export.CSV.zip",
        "300 hash3 http://data.gdeltproject.org/gdeltv2/20260701000000.export.CSV.zip",
        "400 hash4 http://data.gdeltproject.org/gdeltv2/20260302000000.gkg.csv.zip",  # GKG ignored
    ]
    res = filter_master_list(lines, start_date=date(2026, 2, 1), end_date=date(2026, 3, 31))
    assert len(res) == 2
    assert res[0][0].endswith("20260201000000.export.CSV.zip")
    assert res[1][0].endswith("20260302000000.export.CSV.zip")


def test_pull_manifest_save_and_load(tmp_path: Path) -> None:
    manifest_file = tmp_path / "test_manifest.json"
    m1 = PullManifest()
    m1.completed_urls.add("http://example.com/file1.zip")
    m1.completed_urls.add("http://example.com/file2.zip")
    m1.save(manifest_file)

    m2 = PullManifest.load(manifest_file)
    assert len(m2.completed_urls) == 2
    assert "http://example.com/file1.zip" in m2.completed_urls
