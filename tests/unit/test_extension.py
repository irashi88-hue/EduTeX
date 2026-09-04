"""Unit and integration-oriented tests for the Extension System."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from edutex.core.cli import main
from edutex.core.errors import ExtensionError
from edutex.extension.loader import ExtensionLoader
from edutex.extension.registry import ExtensionPointRegistry
from edutex.extension.models import ExtensionPoint


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def make_project(path: Path, *, extension_ids: list[str]) -> None:
    shutil.copytree(PROJECT_ROOT / "assets", path / "assets")
    enabled = "[" + ", ".join(extension_ids) + "]"
    (path / "edutex.config.yaml").write_text(
        f'''edutex:
  version: "0.1.0"
knowledge:
  model: "assets/knowledge_models/example.md"
theme:
  name: "default"
layout:
  name: "default"
build:
  output_format: "latex"
  output_dir: "output"
  output_file: "extension_test"
extensions:
  enabled: {enabled}
logging:
  level: "INFO"
''',
        encoding="utf-8",
    )


def test_extension_point_registry_rejects_duplicates() -> None:
    registry = ExtensionPointRegistry()
    point = ExtensionPoint("test.point", "Test", "Test point")
    registry.declare(point)
    with pytest.raises(ExtensionError, match="Duplicate extension point"):
        registry.declare(point)


def test_loader_rejects_missing_manifest_fields(tmp_path: Path) -> None:
    manifest = tmp_path / "extension.yaml"
    manifest.write_text("id: incomplete\n", encoding="utf-8")

    with pytest.raises(ExtensionError, match="missing required fields"):
        ExtensionLoader().load(manifest)


def test_enabled_extension_contributes_before_build(tmp_path: Path) -> None:
    make_project(tmp_path, extension_ids=["reading_tip"])
    result = CliRunner().invoke(main, ["build", "--project", str(tmp_path)])

    assert result.exit_code == 0, result.output
    tex = (tmp_path / "output" / "extension_test.tex").read_text(encoding="utf-8")
    assert "\\textbf{Reading tip:}" in tex


def test_disabled_extension_does_not_contribute(tmp_path: Path) -> None:
    make_project(tmp_path, extension_ids=[])
    result = CliRunner().invoke(main, ["build", "--project", str(tmp_path)])

    assert result.exit_code == 0, result.output
    tex = (tmp_path / "output" / "extension_test.tex").read_text(encoding="utf-8")
    assert "Reading tip" not in tex
