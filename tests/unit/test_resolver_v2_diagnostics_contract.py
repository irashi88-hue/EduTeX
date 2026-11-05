"""V2 contract tests for structured Resolver diagnostics."""

import json
from pathlib import Path

from edutex.core.errors import ResolverError
from edutex.registry.models import EntityRecord, EntityReference, EntityType
from edutex.registry.registry import Registry
from edutex.resolver.resolver import Resolver


def resolve_records(records: list[EntityRecord]):
    registry = Registry()
    for record in records:
        registry.register(record)
    registry.close_registration_window()
    return Resolver(registry).resolve()


def expect_resolver_error(records: list[EntityRecord]) -> ResolverError:
    try:
        resolve_records(records)
    except ResolverError as exc:
        return exc
    raise AssertionError("Expected ResolverError")


def test_missing_required_references_are_structured_and_canonical():
    source = EntityRecord(
        "component-a",
        EntityType.COMPONENT,
        Path("component-a"),
        references=[
            EntityReference("uses", "theme-z", EntityType.THEME),
            EntityReference("requires", "layout-a", EntityType.LAYOUT),
        ],
    )

    error = expect_resolver_error([source])

    assert error.code == "RUNTIME_REFERENCE_MISSING"
    assert error.details == {
        "missing_references": [
            {
                "source": {"type": "component", "id": "component-a"},
                "expected_target": {"type": "layout", "id": "layout-a"},
                "reference_type": "requires",
            },
            {
                "source": {"type": "component", "id": "component-a"},
                "expected_target": {"type": "theme", "id": "theme-z"},
                "reference_type": "uses",
            },
        ]
    }


def test_cycle_error_has_canonical_typed_identity_path():
    z_node = EntityRecord(
        "z-node",
        EntityType.COMPONENT,
        Path("z-node"),
        references=[
            EntityReference("requires", "a-node", EntityType.COMPONENT),
        ],
    )
    a_node = EntityRecord(
        "a-node",
        EntityType.COMPONENT,
        Path("a-node"),
        references=[
            EntityReference("requires", "z-node", EntityType.COMPONENT),
        ],
    )

    error = expect_resolver_error([z_node, a_node])

    assert error.code == "RUNTIME_DEPENDENCY_CYCLE"
    assert error.details == {
        "cycle": [
            {"type": "component", "id": "a-node"},
            {"type": "component", "id": "z-node"},
            {"type": "component", "id": "a-node"},
        ]
    }


def test_cli_error_serializers_preserve_code_and_details_nesting():
    from edutex.core.cli import (
        _format_build_error_json,
        _format_inspection_error_json,
        _format_validate_json,
    )

    code = "RUNTIME_REFERENCE_MISSING"
    details = {
        "missing_references": [
            {
                "source": {"type": "component", "id": "component-a"},
                "expected_target": {"type": "theme", "id": "theme-z"},
                "reference_type": "uses",
            }
        ]
    }
    expected_error = {
        "type": "ResolverError",
        "message": "resolution failed",
        "code": code,
        "details": details,
    }

    build = json.loads(
        _format_build_error_json(
            "resolution failed",
            error_type="ResolverError",
            code=code,
            details=details,
        )
    )
    validate = json.loads(
        _format_validate_json(
            status="failed",
            error_type="ResolverError",
            message="resolution failed",
            code=code,
            details=details,
        )
    )
    inspection = json.loads(
        _format_inspection_error_json(
            "resolution failed",
            error_type="ResolverError",
            code=code,
            details=details,
        )
    )

    assert build["build"]["error"] == expected_error
    assert validate["validation"]["error"] == expected_error
    assert inspection["inspection"]["error"] == expected_error
