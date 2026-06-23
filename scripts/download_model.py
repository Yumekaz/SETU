#!/usr/bin/env python3
"""Download Phi-3-mini GGUF model to gitignored data/models/."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "data" / "models"
# Public HuggingFace mirror (Q4_K_M quant, ~2.3GB).
DEFAULT_URL = (
    "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/"
    "resolve/main/Phi-3-mini-4k-instruct-q4.gguf"
)
DEFAULT_FILENAME = "Phi-3-mini-4k-instruct-q4.gguf"


def main() -> int:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    dest = MODELS_DIR / DEFAULT_FILENAME
    if dest.exists() and dest.stat().st_size > 1_000_000:
        print(f"Model already present: {dest}")
        return 0

    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    print(f"Downloading {url} -> {dest}")
    with httpx.stream("GET", url, follow_redirects=True, timeout=120.0) as resp:
        resp.raise_for_status()
        with dest.open("wb") as f:
            for chunk in resp.iter_bytes():
                f.write(chunk)
    print(f"Saved {dest} ({dest.stat().st_size} bytes)")
    print(f"Set SETU_LLM_MODEL_PATH={dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())