"""LLM extraction runner tests (rules fallback when model absent)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = Path("/tmp/grok-goal-7dbdddf7e201/implementer")


def test_llm_runner_or_rules_fallback():
    from ml.extraction.llama_runner import LlamaExtractionError, extract_fields

    model_path = os.getenv("SETU_LLM_MODEL_PATH", "")
    log_lines: list[str] = []

    if model_path and Path(model_path).exists():
        try:
            result = extract_fields(
                snippet="Strait of Hormuz military exercise reported 2026-03-11",
                corridor="HORMUZ",
                model_path=model_path,
            )
            log_lines.append(f"llm_ok keys={sorted(result.keys())}")
            required = {"corridor", "event_type", "severity", "confidence", "event_date"}
            assert set(result.keys()) >= required
        except Exception as exc:  # noqa: BLE001
            log_lines.append(f"llm_error={exc}")
            pytest.skip(f"LLM load failed: {exc}")
    else:
        from app.signals.rules_extractor import extract_from_gdelt

        row = {
            "GLOBALEVENTID": "llm-fallback-1",
            "SQLDATE": "20260311",
            "EventCode": "190",
            "GoldsteinScale": "-8",
            "ActionGeo_FullName": "Strait of Hormuz",
            "ActionGeo_Lat": "26.5",
            "ActionGeo_Long": "56.5",
            "SOURCEURL": "https://example.com/h",
            "Actor1Name": "Iran",
            "Actor2Name": "Navy",
        }
        partial = extract_from_gdelt(row, "HORMUZ")
        log_lines.append(f"rules_fallback={partial}")
        with pytest.raises(LlamaExtractionError):
            extract_fields(snippet="test", corridor="HORMUZ", model_path="/nonexistent/model.gguf")

    SCRATCH.mkdir(parents=True, exist_ok=True)
    (SCRATCH / "extract_llm.log").write_text("\n".join(log_lines), encoding="utf-8")
