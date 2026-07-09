"""Regression coverage for non-destructive live GDELT refresh behavior."""

from __future__ import annotations

import inspect

from app.signals.pipeline import run_pipeline


def test_live_pipeline_defaults_to_source_aware_reset_policy() -> None:
    signature = inspect.signature(run_pipeline)
    assert signature.parameters["reset"].default is None
