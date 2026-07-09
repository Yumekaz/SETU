"""Portable scratch directories for evidence-writing tests."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def scratch_dir(name: str) -> Path:
    """Return a writable scratch directory for test evidence artifacts."""
    root = os.getenv("SETU_SCRATCH_DIR")
    base = Path(root) if root else Path(tempfile.gettempdir())
    return base / name
