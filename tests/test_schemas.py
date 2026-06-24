"""Validate JSON schemas and generated Pydantic models."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = ROOT / "schemas"
FIXTURES_DIR = ROOT / "data" / "fixtures"

sys.path.insert(0, str(ROOT / "backend"))

from app.models.generated import (  # noqa: E402
    CascadeResult,
    GraphEdge,
    GraphNode,
    Recommendation,
    RiskForecast,
    RiskScore,
    SignalEvent,
)

CONTRACT_FILES = [
    "signal_event.json",
    "risk_score.json",
    "cascade_result.json",
    "risk_forecast.json",
    "graph_node.json",
    "graph_edge.json",
    "recommendation.json",
]

MODEL_MAP = {
    "signal_events": SignalEvent,
    "risk_scores": RiskScore,
    "cascade_results": CascadeResult,
    "risk_forecasts": RiskForecast,
    "graph_nodes": GraphNode,
    "graph_edges": GraphEdge,
    "recommendations": Recommendation,
}


@pytest.fixture(scope="module")
def schema_store() -> dict:
    store: dict = {}
    for path in SCHEMAS_DIR.glob("*.json"):
        with path.open() as f:
            store[path.name] = json.load(f)
    return store


@pytest.mark.parametrize("filename", CONTRACT_FILES)
def test_schema_is_draft07_with_no_extra_props(filename: str, schema_store: dict) -> None:
    schema = schema_store[filename]
    assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
    assert schema.get("additionalProperties") is False


@pytest.mark.parametrize("filename", CONTRACT_FILES)
def test_schema_validates_self_example_structure(filename: str, schema_store: dict) -> None:
    schema = schema_store[filename]
    assert "properties" in schema
    assert "required" in schema
    assert len(schema["required"]) > 0


@pytest.mark.parametrize("fixture_name,model_cls", list(MODEL_MAP.items()))
def test_fixture_validates_with_pydantic(fixture_name: str, model_cls: type) -> None:
    fixture_path = FIXTURES_DIR / f"{fixture_name}.json"
    assert fixture_path.exists(), f"Missing fixture: {fixture_path}"

    with fixture_path.open() as f:
        records = json.load(f)

    assert isinstance(records, list) and len(records) > 0
    for record in records:
        instance = model_cls.model_validate(record)
        assert instance is not None


@pytest.mark.parametrize("fixture_name", list(MODEL_MAP.keys()))
def test_fixture_validates_against_json_schema(
    fixture_name: str, schema_store: dict
) -> None:
    schema_name = fixture_name.rstrip("s")
    if schema_name == "signal_event":
        schema_file = "signal_event.json"
    elif schema_name == "risk_score":
        schema_file = "risk_score.json"
    elif schema_name == "cascade_result":
        schema_file = "cascade_result.json"
    elif schema_name == "graph_node":
        schema_file = "graph_node.json"
    elif schema_name == "graph_edge":
        schema_file = "graph_edge.json"
    elif schema_name == "risk_forecast":
        schema_file = "risk_forecast.json"
    else:
        schema_file = "recommendation.json"

    schema = schema_store[schema_file]
    resolver = jsonschema.RefResolver(
        base_uri=f"file://{SCHEMAS_DIR}/",
        referrer=schema,
        store={
            f"file://{SCHEMAS_DIR}/{k}": v for k, v in schema_store.items()
        },
    )
    validator = jsonschema.Draft7Validator(schema, resolver=resolver)

    fixture_path = FIXTURES_DIR / f"{fixture_name}.json"
    with fixture_path.open() as f:
        records = json.load(f)

    for record in records:
        validator.validate(record)


def test_corridor_enum() -> None:
    with (SCHEMAS_DIR / "corridor.json").open() as f:
        corridor = json.load(f)
    assert set(corridor["enum"]) == {
        "HORMUZ",
        "BAB_EL_MANDEB",
        "MALACCA",
        "OTHER",
    }
