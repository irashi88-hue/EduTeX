"""Test del contratto dello schema pubblico del Content Model."""

from __future__ import annotations

import json
from pathlib import Path

from edutex.knowledge import CONTENT_MODEL_SCHEMA_VERSION, content_model_schema


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "CONTENT_MODEL_SCHEMA_CONTRACT.md"


def test_documentazione_content_model_schema() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    for marker in (
        "content_model_schema",
        "CONTENT_MODEL_SCHEMA_VERSION",
        "Draft 2020-12",
        "ContentNode",
        "TextBlock",
        "additionalProperties: false",
        "JSON-safe",
        "$defs.contentNode",
    ):
        assert marker in contract, f"Marker mancante: {marker}"
    assert all(
        not line.rstrip("\n").endswith((" ", "\t"))
        for line in contract.splitlines(keepends=True)
    )


def test_schema_is_json_safe_and_matches_public_version() -> None:
    schema = content_model_schema()

    assert CONTENT_MODEL_SCHEMA_VERSION == "1.0.0"
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"].endswith("content-model-1.0.0.json")
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert schema["required"] == ["items"]
    assert json.loads(json.dumps(schema, ensure_ascii=False)) == schema


def test_schema_describes_recursive_content_items_without_unknown_fields() -> None:
    schema = content_model_schema()
    definitions = schema["$defs"]

    assert set(definitions) == {"contentItem", "contentNode", "textBlock"}
    assert definitions["contentItem"]["oneOf"] == [
        {"$ref": "#/$defs/contentNode"},
        {"$ref": "#/$defs/textBlock"},
    ]

    node = definitions["contentNode"]
    assert node["additionalProperties"] is False
    assert node["required"] == [
        "node_type",
        "subtype",
        "fields",
        "body",
        "children",
        "source_line",
    ]
    assert node["properties"]["children"] == {
        "type": "array",
        "items": {"$ref": "#/$defs/contentNode"},
    }

    text_block = definitions["textBlock"]
    assert text_block["additionalProperties"] is False
    assert text_block["required"] == ["content"]


def test_schema_result_is_detached_between_calls() -> None:
    first = content_model_schema()
    first["title"] = "changed"
    first["$defs"]["contentNode"]["properties"]["body"] = {"type": "integer"}

    second = content_model_schema()
    assert second["title"] == "EduTeX Content Model"
    assert second["$defs"]["contentNode"]["properties"]["body"] == {
        "type": "string"
    }
