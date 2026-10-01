"""Test del catalogo diagnostico pubblico di EduTeX."""

from __future__ import annotations

import json
from pathlib import Path

from edutex.core.diagnostics import (
    format_diagnostics_text,
    serialize_diagnostic,
    serialize_diagnostics,
)
from edutex.extension.models import ExtensionDiagnostic


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "docs" / "DIAGNOSTIC_CATALOG.md"


def test_catalogo_documentato_senza_whitespace_finale() -> None:
    catalog = CATALOG.read_text(encoding="utf-8")

    required_markers = (
        "ExtensionDiagnostic",
        "extension_id",
        "point_id",
        "COURSE_SOURCE_FRONTMATTER_MISSING",
        "COURSE_DURATION_UNDECLARED",
        "SC106",
        "ExtensionError",
        "build.error",
        "validation.error",
    )

    for marker in required_markers:
        assert marker in catalog, f"Marker mancante nel catalogo: {marker}"

    assert all(
        not line.rstrip("\n").endswith((" ", "\t"))
        for line in catalog.splitlines(keepends=True)
    )


def test_extension_diagnostic_schema_e_serializzazione() -> None:
    diagnostic = ExtensionDiagnostic(
        extension_id="reading_tip",
        point_id="layout.post_structure",
        phase="handler",
        message="handler boom",
    )

    serialized = serialize_diagnostic(diagnostic)

    assert serialized == {
        "extension_id": "reading_tip",
        "point_id": "layout.post_structure",
        "phase": "handler",
        "message": "handler boom",
    }
    json.dumps(serialized, ensure_ascii=False)


def test_extension_diagnostic_preserva_contesto_parziale() -> None:
    diagnostic = ExtensionDiagnostic(
        extension_id=None,
        point_id=None,
        phase="initialization",
        message="extension manifest failed",
    )

    assert serialize_diagnostic(diagnostic) == {
        "extension_id": None,
        "point_id": None,
        "phase": "initialization",
        "message": "extension manifest failed",
    }


def test_serialize_diagnostics_preserva_ordine() -> None:
    diagnostics = (
        ExtensionDiagnostic(
            extension_id="first",
            point_id="layout.post_structure",
            phase="handler",
            message="first error",
        ),
        ExtensionDiagnostic(
            extension_id="second",
            point_id="layout.post_structure",
            phase="handler",
            message="second error",
        ),
    )

    assert serialize_diagnostics(diagnostics) == [
        {
            "extension_id": "first",
            "point_id": "layout.post_structure",
            "phase": "handler",
            "message": "first error",
        },
        {
            "extension_id": "second",
            "point_id": "layout.post_structure",
            "phase": "handler",
            "message": "second error",
        },
    ]


def test_diagnostica_testuale_mantiene_i_campi_strutturati() -> None:
    diagnostic = ExtensionDiagnostic(
        extension_id="reading_tip",
        point_id="layout.post_structure",
        phase="handler",
        message="handler boom",
    )

    assert format_diagnostics_text((diagnostic,)) == (
        "Extension diagnostics:\n"
        "- extension_id=reading_tip; point_id=layout.post_structure; "
        "phase=handler; message=handler boom"
    )
