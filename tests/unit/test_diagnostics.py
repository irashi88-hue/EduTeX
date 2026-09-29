from __future__ import annotations

from dataclasses import dataclass

import pytest

from edutex.core.diagnostics import serialize_diagnostic, serialize_diagnostics
from edutex.extension.models import ExtensionDiagnostic


def test_serialize_diagnostic_supports_extension_dataclass() -> None:
    diagnostic = ExtensionDiagnostic(
        extension_id="reading_tip",
        point_id="layout.post_structure",
        phase="handler",
        message="handler boom",
    )

    assert serialize_diagnostic(diagnostic) == {
        "extension_id": "reading_tip",
        "point_id": "layout.post_structure",
        "phase": "handler",
        "message": "handler boom",
    }


@dataclass(frozen=True)
class GenericDiagnostic:
    code: str
    message: str


def test_serialize_diagnostics_preserves_order() -> None:
    diagnostics = (
        GenericDiagnostic(code="D001", message="first"),
        GenericDiagnostic(code="D002", message="second"),
    )

    assert serialize_diagnostics(diagnostics) == [
        {"code": "D001", "message": "first"},
        {"code": "D002", "message": "second"},
    ]


class MappingDiagnostic:
    def to_dict(self) -> dict[str, str]:
        return {"code": "D003", "message": "mapped"}


def test_serialize_diagnostic_supports_to_dict() -> None:
    assert serialize_diagnostic(MappingDiagnostic()) == {
        "code": "D003",
        "message": "mapped",
    }


def test_serialize_diagnostic_rejects_unsupported_values() -> None:
    with pytest.raises(TypeError, match="dataclass, mapping"):
        serialize_diagnostic(object())


def test_serialize_diagnostic_requires_mapping_from_to_dict() -> None:
    class InvalidDiagnostic:
        def to_dict(self) -> str:
            return "invalid"

    with pytest.raises(TypeError, match="must return a mapping"):
        serialize_diagnostic(InvalidDiagnostic())
