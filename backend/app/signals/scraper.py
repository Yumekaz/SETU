"""URL content scraper with safety guards (SSRF protection, content-type checks, size limits)."""

from __future__ import annotations

import logging
import re
import socket
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Security and safety constants
MAX_RESPONSE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB max
HTTP_TIMEOUT_SECONDS = 15.0
MAX_TEXT_SNIPPET_LENGTH = 2000
RATE_LIMIT_WINDOW_SECONDS = 60
MAX_REQUESTS_PER_WINDOW = 5

# Rate limit memory tracker
_request_history: list[float] = []

# Forbidden private/loopback IP prefixes (SSRF protection)
BLOCKED_IP_PATTERNS = (
    r"^127\.",
    r"^10\.",
    r"^172\.(1[6-9]|2[0-9]|3[01])\.",
    r"^192\.168\.",
    r"^169\.254\.",
    r"^0\.",
    r"^::1$",
    r"^fc00:",
    r"^fe80:",
)


@dataclass
class ScrapedArticle:
    url: str
    title: str
    content_text: str
    domain: str
    scraped_at_iso: str
    rejection_reason: str | None = None


def is_rate_limited() -> bool:
    """Check in-memory sliding window rate limit (5 requests per 60s)."""
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS
    global _request_history
    _request_history = [t for t in _request_history if t > cutoff]
    if len(_request_history) >= MAX_REQUESTS_PER_WINDOW:
        return True
    _request_history.append(now)
    return False


def is_ssrf_safe_url(url: str) -> tuple[bool, str | None]:
    """Validate URL scheme and ensure host does not resolve to private/internal IP."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Malformed URL"

    if parsed.scheme not in {"http", "https"}:
        return False, f"Invalid scheme '{parsed.scheme}'. Only http and https allowed"

    hostname = parsed.hostname
    if not hostname:
        return False, "Missing hostname in URL"

    # Block explicit localhost/local names
    if hostname.lower() in {"localhost", "127.0.0.1", "::1"}:
        return False, "Access to localhost is prohibited"

    # Resolve hostname to IP to prevent DNS rebinding / internal access
    try:
        ip_addresses = socket.gethostbyname_ex(hostname)[2]
    except Exception as exc:
        return False, f"Could not resolve host '{hostname}': {exc}"

    for ip in ip_addresses:
        for pattern in BLOCKED_IP_PATTERNS:
            if re.match(pattern, ip):
                return False, f"Host resolves to restricted internal IP ({ip})"

    return True, None


def scrape_url(url: str) -> ScrapedArticle:
    """Scrape article content text safely from a public HTTP/HTTPS URL."""
    if is_rate_limited():
        return ScrapedArticle(
            url=url,
            title="",
            content_text="",
            domain="",
            scraped_at_iso="",
            rejection_reason="Rate limit exceeded (max 5 requests per minute)",
        )

    is_safe, error_reason = is_ssrf_safe_url(url)
    if not is_safe:
        return ScrapedArticle(
            url=url,
            title="",
            content_text="",
            domain="",
            scraped_at_iso="",
            rejection_reason=error_reason,
        )

    parsed = urlparse(url)
    domain = parsed.netloc

    try:
        with httpx.Client(follow_redirects=True, timeout=HTTP_TIMEOUT_SECONDS) as client:
            # Head request to check size and content-type before downloading
            head_resp = client.head(url)
            content_type = head_resp.headers.get("content-type", "").lower()
            if content_type and "text/html" not in content_type and "text/plain" not in content_type:
                return ScrapedArticle(
                    url=url,
                    title="",
                    content_text="",
                    domain=domain,
                    scraped_at_iso="",
                    rejection_reason=f"Unsupported content type '{content_type}'. Must be text/html or text/plain",
                )

            content_length = head_resp.headers.get("content-length")
            if content_length and int(content_length) > MAX_RESPONSE_SIZE_BYTES:
                return ScrapedArticle(
                    url=url,
                    title="",
                    content_text="",
                    domain=domain,
                    scraped_at_iso="",
                    rejection_reason="Resource size exceeds maximum 5MB limit",
                )

            # GET request
            resp = client.get(url)
            resp.raise_for_status()

            if len(resp.content) > MAX_RESPONSE_SIZE_BYTES:
                return ScrapedArticle(
                    url=url,
                    title="",
                    content_text="",
                    domain=domain,
                    scraped_at_iso="",
                    rejection_reason="Downloaded content exceeds 5MB limit",
                )

    except httpx.TimeoutException:
        return ScrapedArticle(
            url=url,
            title="",
            content_text="",
            domain=domain,
            scraped_at_iso="",
            rejection_reason=f"HTTP request timed out after {HTTP_TIMEOUT_SECONDS}s",
        )
    except httpx.HTTPStatusError as exc:
        return ScrapedArticle(
            url=url,
            title="",
            content_text="",
            domain=domain,
            scraped_at_iso="",
            rejection_reason=f"HTTP error status {exc.response.status_code}",
        )
    except Exception as exc:
        return ScrapedArticle(
            url=url,
            title="",
            content_text="",
            domain=domain,
            scraped_at_iso="",
            rejection_reason=f"Network fetch failed: {exc}",
        )

    # Parse HTML using BeautifulSoup
    try:
        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract title
        title_el = soup.find("title") or soup.find("h1")
        title = title_el.get_text().strip() if title_el else ""

        # Remove non-content tags
        for element in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
            element.decompose()

        # Extract main text
        main_content = soup.find("article") or soup.find("main") or soup.body or soup
        text_lines = [line.strip() for line in main_content.get_text().splitlines() if line.strip()]
        full_text = " ".join(text_lines)

        # Truncate to max snippet length
        content_text = full_text[:MAX_TEXT_SNIPPET_LENGTH]

        if not content_text:
            return ScrapedArticle(
                url=url,
                title=title,
                content_text="",
                domain=domain,
                scraped_at_iso="",
                rejection_reason="No extractable text content found on page",
            )

        return ScrapedArticle(
            url=url,
            title=title,
            content_text=content_text,
            domain=domain,
            scraped_at_iso=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

    except Exception as exc:
        return ScrapedArticle(
            url=url,
            title="",
            content_text="",
            domain=domain,
            scraped_at_iso="",
            rejection_reason=f"HTML parsing error: {exc}",
        )
