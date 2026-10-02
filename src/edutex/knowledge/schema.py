"""Stable JSON schema for the EduTeX Content Model."""

from __future__ import annotations

from copy import deepcopy


CONTENT_MODEL_SCHEMA_VERSION = "1.0.0"


def content_model_schema() -> dict[str, object]:
    """Return a fresh deterministic JSON Schema for ``ContentModel``."""
    schema: dict[str, object] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": (
            "https://edutex.dev/schema/content-model-"
            f"{CONTENT_MODEL_SCHEMA_VERSION}.json"
        ),
        "title": "EduTeX Content Model",
        "description": "Schema for the parsed, typed educational content model.",
        "type": "object",
        "additionalProperties": False,
        "required": ["items"],
        "properties": {
            "items": {
                "type": "array",
                "items": {"$ref": "#/$defs/contentItem"},
            }
        },
        "$defs": {
            "contentItem": {
                "oneOf": [
                    {"$ref": "#/$defs/contentNode"},
                    {"$ref": "#/$defs/textBlock"},
                ]
            },
            "contentNode": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "node_type",
                    "subtype",
                    "fields",
                    "body",
                    "children",
                    "source_line",
                ],
                "properties": {
                    "node_type": {"type": "string"},
                    "subtype": {"type": ["string", "null"]},
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "body": {"type": "string"},
                    "children": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/contentNode"},
                    },
                    "source_line": {
                        "type": "integer",
                        "minimum": 0,
                    },
                },
            },
            "textBlock": {
                "type": "object",
                "additionalProperties": False,
                "required": ["content"],
                "properties": {
                    "content": {"type": "string"},
                },
            },
        },
    }
    return deepcopy(schema)
