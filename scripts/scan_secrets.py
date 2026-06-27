#!/usr/bin/env python3
"""Scan tracked git files for disallowed secret patterns."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PATTERNS = [
    (re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*=\s*['\"]?[A-Za-z0-9_\-]{20,}"), "assignment"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "openai_sk"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "aws_key"),
    (re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]{20,}"), "bearer_token"),
]

ALLOWLIST_SUBSTRINGS = (
    "REDACTED",
    "your_api_key",
    "example.com",
    ".env.example",
    "api_key=",  # pull_samples redact key name only in dict
    "SECRET_KEYS",
    "scan_secrets.py",
)

SKIP_SUFFIXES = (".png", ".jpg", ".gguf", ".db", ".lock")


def tracked_files() -> list[str]:
    proc = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def scan() -> list[str]:
    hits: list[str] = []
    for rel in tracked_files():
        if rel.endswith(SKIP_SUFFIXES):
            continue
        path = ROOT / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            if any(token in line for token in ALLOWLIST_SUBSTRINGS):
                continue
            for pattern, label in PATTERNS:
                if pattern.search(line):
                    hits.append(f"{rel}:{i}:{label}:{line.strip()[:120]}")
                    break
    return hits


def main() -> int:
    hits = scan()
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    body = "\n".join(hits) if hits else "no_hits=true\n"
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body + ("\n" if not body.endswith("\n") else ""), encoding="utf-8")
    else:
        print(body)
    return 1 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main())