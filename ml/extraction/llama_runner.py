"""Phi-3-mini GBNF extraction via llama-cpp-python (optional dependency)."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from ml.extraction.prompts import EXTRACTION_SYSTEM, build_extraction_prompt

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_GRAMMAR = ROOT / "ml" / "grammars" / "signal_event.gbnf"


class LlamaExtractionError(RuntimeError):
    pass


def _grammar_text(path: Path | None = None) -> str:
    grammar_path = path or DEFAULT_GRAMMAR
    return grammar_path.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def _load_llama(model_path: str):
    try:
        from llama_cpp import Llama
    except ImportError as exc:
        raise LlamaExtractionError("llama-cpp-python is not installed") from exc

    return Llama(
        model_path=model_path,
        n_ctx=2048,
        n_threads=max(1, os.cpu_count() or 1),
        verbose=False,
    )


def extract_fields(
    *,
    snippet: str,
    corridor: str,
    model_path: str | None = None,
    grammar_path: Path | None = None,
    max_tokens: int = 128,
) -> dict[str, object]:
    """Return the 5 GBNF-constrained fields from Phi-3-mini."""
    resolved_model = model_path or os.getenv("SETU_LLM_MODEL_PATH", "").strip()
    if not resolved_model or not Path(resolved_model).exists():
        raise LlamaExtractionError("SETU_LLM_MODEL_PATH is unset or file missing")

    llm = _load_llama(resolved_model)
    prompt = build_extraction_prompt(snippet=snippet, corridor=corridor)
    response = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens,
        temperature=0.0,
        grammar=_grammar_text(grammar_path),
    )
    content = response["choices"][0]["message"]["content"]
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise LlamaExtractionError(f"invalid JSON from model: {content!r}") from exc
    return parsed