"""Tests for the extension developer documentation contract."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "EXTENSION_DEVELOPER_CONTRACT.md"
TEMPLATE = ROOT / "src" / "edutex" / "project_template" / "assets" / "extensions" / "reading_tip"


def test_developer_contract_documents_the_public_extension_surface() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    for marker in (
        "extension.yaml",
        "version: 1.0.0",
        "framework",
        "target",
        "entrypoint",
        "def apply(context)",
        "ExtensionDiagnostic",
        "ExtensionError",
        "load_extension_with_fallback",
        "deterministici",
    ):
        assert marker in contract, f"Marker mancante: {marker}"
    assert all(
        not line.rstrip("\n").endswith((" ", "\t"))
        for line in contract.splitlines(keepends=True)
    )


def test_reference_extension_template_has_manifest_and_entrypoint() -> None:
    manifest = (TEMPLATE / "extension.yaml").read_text(encoding="utf-8")
    module = (TEMPLATE / "extension.py").read_text(encoding="utf-8")

    for marker in ("id:", "name:", "version:", "target:", "module:", "entrypoint:"):
        assert marker in manifest
    assert "def " in module


def test_contract_preserves_optional_and_required_boundaries() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    assert "`false` per impostazione predefinita" in contract
    assert "estensioni obbligatorie" in contract
    assert "optional: true" in contract
