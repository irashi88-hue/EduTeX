"""Tests for extension/framework compatibility."""

from __future__ import annotations

from pathlib import Path

import pytest

from edutex.core.errors import ExtensionError
from edutex.extension.compatibility import (
    FRAMEWORK_VERSION,
    is_framework_compatible,
)
from edutex.extension.loader import ExtensionLoader


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "EXTENSION_COMPATIBILITY_CONTRACT.md"


def write_manifest(tmp_path: Path, framework: str | None = None) -> Path:
    path = tmp_path / "extension.yaml"
    lines = [
        "id: sample",
        "name: Sample extension",
        "version: 1.0.0",
        "target: layout.post_structure",
        "module: extension.py",
        "entrypoint: activate",
    ]
    if framework is not None:
        lines.append(f"framework: '{framework}'")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_existing_manifest_without_framework_constraint_remains_valid(tmp_path: Path) -> None:
    manifest = ExtensionLoader().read_manifest(write_manifest(tmp_path))
    assert manifest.version == "1.0.0"
    assert manifest.framework is None


def test_compatible_framework_range_is_preserved(tmp_path: Path) -> None:
    manifest = ExtensionLoader().read_manifest(
        write_manifest(tmp_path, ">=1.0.0,<2.0.0")
    )
    assert manifest.framework == ">=1.0.0,<2.0.0"
    assert is_framework_compatible(manifest.framework, FRAMEWORK_VERSION)


@pytest.mark.parametrize(
    "constraint",
    ("1.0.0", ">=1.0.0", "<=1.0.0", ">=0.9.0,<1.1.0"),
)
def test_supported_constraints_are_compatible(constraint: str) -> None:
    assert is_framework_compatible(constraint, "1.0.0")


@pytest.mark.parametrize(
    "constraint",
    (">=2.0.0", "<1.0.0", "1.1.0", "~1.0.0", ">=1.0.0 || <0.5.0"),
)
def test_incompatible_or_unsupported_constraints_are_rejected(
    tmp_path: Path,
    constraint: str,
) -> None:
    with pytest.raises(ExtensionError, match="framework"):
        ExtensionLoader().read_manifest(write_manifest(tmp_path, constraint))


def test_invalid_constraint_is_rejected_deterministically(tmp_path: Path) -> None:
    with pytest.raises(ExtensionError, match="comparators"):
        ExtensionLoader().read_manifest(write_manifest(tmp_path, ">=1.0"))


def test_documentation_covers_the_compatibility_contract() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    for marker in (
        "framework",
        "1.0.0",
        ">=1.0.0,<2.0.0",
        "ExtensionError",
        "prima dell'importazione",
        "manifest esistenti",
    ):
        assert marker in contract, f"Marker mancante: {marker}"
    assert all(
        not line.rstrip("\n").endswith((" ", "\t"))
        for line in contract.splitlines(keepends=True)
    )
