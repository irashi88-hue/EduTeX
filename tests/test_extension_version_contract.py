"""Tests for the public extension SemVer contract."""

from __future__ import annotations

from pathlib import Path

import pytest

from edutex.core.errors import ExtensionError
from edutex.extension.loader import ExtensionLoader
from edutex.extension.versioning import is_valid_semver, validate_semver


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "EXTENSION_VERSION_CONTRACT.md"


@pytest.mark.parametrize(
    "value",
    (
        "0.0.0",
        "1.0.0",
        "1.0.0-alpha.1",
        "1.0.0+build.1",
        "1.0.0-rc.1+build.7",
    ),
)
def test_valid_semver_values_are_accepted(value: str) -> None:
    assert is_valid_semver(value)
    assert validate_semver(value) == value


@pytest.mark.parametrize(
    "value",
    (
        "",
        "1.0",
        "v1.0.0",
        "01.0.0",
        "1.0.0-",
        "1.0.0+",
        "1.0.0-alpha..1",
        1,
        None,
    ),
)
def test_invalid_semver_values_are_rejected(value: object) -> None:
    assert not is_valid_semver(value)
    with pytest.raises(ValueError, match="SemVer 2.0.0"):
        validate_semver(value)


def write_manifest(tmp_path: Path, version: object) -> Path:
    path = tmp_path / "extension.yaml"
    if isinstance(version, str):
        rendered = version
    elif version is None:
        rendered = "null"
    else:
        rendered = str(version)
    path.write_text(
        "\n".join(
            (
                "id: sample",
                "name: Sample extension",
                f"version: {rendered}",
                "target: layout.post_structure",
                "module: extension.py",
                "entrypoint: activate",
                "",
            )
        ),
        encoding="utf-8",
    )
    return path


def test_loader_accepts_valid_version_and_preserves_manifest_fields(tmp_path: Path) -> None:
    manifest_path = write_manifest(tmp_path, "1.0.0-rc.1+build.7")
    manifest = ExtensionLoader().read_manifest(manifest_path, expected_id="sample")

    assert manifest.extension_id == "sample"
    assert manifest.version == "1.0.0-rc.1+build.7"
    assert manifest.target == "layout.post_structure"
    assert manifest.module == "extension.py"
    assert manifest.entrypoint == "activate"


@pytest.mark.parametrize("version", ("1.0", "v1.0.0", "", "01.0.0"))
def test_loader_rejects_invalid_version_before_module_loading(
    tmp_path: Path,
    version: str,
) -> None:
    manifest_path = write_manifest(tmp_path, version)

    with pytest.raises(ExtensionError, match="SemVer 2.0.0"):
        ExtensionLoader().read_manifest(manifest_path, expected_id="sample")


def test_documentation_covers_the_stable_version_contract() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    for marker in (
        "SemVer 2.0.0",
        "1.0.0-alpha.1",
        "1.0.0+build.1",
        "ExtensionError",
        "prima dell'importazione",
        "non modifica",
        "01.0.0",
    ):
        assert marker in contract, f"Marker mancante: {marker}"
    assert all(
        not line.rstrip("\n").endswith((" ", "\t"))
        for line in contract.splitlines(keepends=True)
    )
