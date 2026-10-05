"""Tests for optional extensions and controlled fallback."""

from __future__ import annotations

from pathlib import Path

import pytest

from edutex.core.errors import ExtensionError
from edutex.extension.fallback import load_extension_with_fallback
from edutex.extension.loader import ExtensionLoader


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "OPTIONAL_EXTENSION_CONTRACT.md"


def write_manifest(tmp_path: Path, *, optional: bool) -> Path:
    path = tmp_path / "extension.yaml"
    path.write_text(
        "\n".join(
            (
                "id: sample",
                "name: Sample extension",
                "version: 1.0.0",
                "target: layout.post_structure",
                "module: extension.py",
                "entrypoint: activate",
                f"optional: {str(optional).lower()}",
                "",
            )
        ),
        encoding="utf-8",
    )
    return path


def test_existing_manifest_defaults_to_required(tmp_path: Path) -> None:
    path = write_manifest(tmp_path, optional=False)
    manifest = ExtensionLoader().read_manifest(path, expected_id="sample")
    assert manifest.optional is False


def test_optional_module_failure_returns_diagnostic_without_raising(tmp_path: Path) -> None:
    path = write_manifest(tmp_path, optional=True)
    result = load_extension_with_fallback(path, expected_id="sample")

    assert result.skipped is True
    assert result.loaded is None
    assert result.diagnostic is not None
    assert result.diagnostic.extension_id == "sample"
    assert result.diagnostic.phase == "loading"
    assert "not found" in result.diagnostic.message.lower()


def test_required_module_failure_still_raises(tmp_path: Path) -> None:
    path = write_manifest(tmp_path, optional=False)

    with pytest.raises(ExtensionError):
        load_extension_with_fallback(path, expected_id="sample")


def test_optional_valid_module_loads_without_diagnostic(tmp_path: Path) -> None:
    path = write_manifest(tmp_path, optional=True)
    (tmp_path / "extension.py").write_text(
        "def activate(context):\n    return context\n",
        encoding="utf-8",
    )

    result = load_extension_with_fallback(path, expected_id="sample")

    assert result.skipped is False
    assert result.loaded is not None
    assert result.diagnostic is None


def test_documentation_covers_the_optional_contract() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    for marker in (
        "optional: true",
        "load_extension_with_fallback",
        "ExtensionDiagnostic",
        "ExtensionError",
        "loaded: None",
        "opt-in",
    ):
        assert marker in contract, f"Marker mancante: {marker}"
    assert all(
        not line.rstrip("\n").endswith((" ", "\t"))
        for line in contract.splitlines(keepends=True)
    )
