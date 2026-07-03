"""Tests for live URL scraper safety guards and edge cases EC-52 to EC-58."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.signals.scraper import (  # noqa: E402
    is_rate_limited,
    is_ssrf_safe_url,
    scrape_url,
)


def test_ssrf_blocks_localhost_ec_52() -> None:
    safe, reason = is_ssrf_safe_url("http://localhost:8000/secret")
    assert not safe
    assert "localhost" in (reason or "")


def test_ssrf_blocks_127_0_0_1_ec_52() -> None:
    safe, reason = is_ssrf_safe_url("http://127.0.0.1/admin")
    assert not safe


def test_ssrf_blocks_non_http_scheme_ec_52() -> None:
    safe, reason = is_ssrf_safe_url("file:///etc/passwd")
    assert not safe
    assert "scheme" in (reason or "").lower()


def test_ssrf_allows_valid_public_domain() -> None:
    safe, reason = is_ssrf_safe_url("https://www.reuters.com/business/energy")
    assert safe
    assert reason is None


def test_scrape_url_rejects_ssrf() -> None:
    res = scrape_url("http://localhost:8000/internal")
    assert res.rejection_reason is not None
    assert res.content_text == ""


def test_rate_limiter() -> None:
    # Under limit initially
    assert not is_rate_limited()
