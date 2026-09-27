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
from edutex.extension.service import ExtensionService
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


def test_loader_rejects_non_string_target(tmp_path: Path) -> None:
    module = tmp_path / "extension.py"
    module.write_text(
        "def apply(context):\n"
        "    return context\n",
        encoding="utf-8",
    )

    manifest = tmp_path / "extension.yaml"
    manifest.write_text(
        "id: typed_extension\n"
        "name: Typed Extension\n"
        "version: 1.0.0\n"
        "target:\n"
        "  - layout.post_structure\n"
        "module: extension.py\n"
        "entrypoint: apply\n",
        encoding="utf-8",
    )

    with pytest.raises(ExtensionError, match="non-empty string"):
        ExtensionLoader().load(manifest)


def test_loader_rejects_module_path_escape(tmp_path: Path) -> None:
    extension_dir = tmp_path / "extension"
    extension_dir.mkdir()

    outside_module = tmp_path / "outside.py"
    outside_module.write_text(
        "def apply(context):\n"
        "    return context\n",
        encoding="utf-8",
    )

    manifest = extension_dir / "extension.yaml"
    manifest.write_text(
        "id: escaped_extension\n"
        "name: Escaped Extension\n"
        "version: 1.0.0\n"
        "target: layout.post_structure\n"
        "module: ../outside.py\n"
        "entrypoint: apply\n",
        encoding="utf-8",
    )

    with pytest.raises(ExtensionError, match="inside the extension directory"):
        ExtensionLoader().load(manifest)


def test_extension_service_termination_is_idempotent() -> None:
    service = ExtensionService()
    service._loaded = [object()]  # type: ignore[list-item]
    service._document = object()  # type: ignore[assignment]

    service.terminate()
    service.terminate()

    assert service.loaded_extensions == ()
    with pytest.raises(ExtensionError, match=r"process\(\) has not been called"):
        _ = service.document


def test_extensions_follow_configured_order(tmp_path: Path) -> None:
    make_project(tmp_path, extension_ids=["second_tip", "first_tip"])
    extensions_root = tmp_path / "assets" / "extensions"

    for extension_id, label in (
        ("first_tip", "ORDERFIRST"),
        ("second_tip", "ORDERSECOND"),
    ):
        directory = extensions_root / extension_id
        directory.mkdir()
        (directory / "extension.yaml").write_text(
            "\n".join(
                [
                    f"id: {extension_id}",
                    f"name: {extension_id}",
                    "version: 1.0.0",
                    "target: layout.post_structure",
                    "module: extension.py",
                    "entrypoint: apply",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (directory / "extension.py").write_text(
            "from copy import deepcopy\n"
            "from edutex.extension.models import ExtensionContext\n"
            "from edutex.knowledge.models import TextBlock\n\n"
            "def apply(context: ExtensionContext):\n"
            "    document = deepcopy(context.document)\n"
            "    document.prose_blocks.append(\n"
            "        (10, TextBlock(content={!r}))\n"
            "    )\n"
            "    return document\n".format(label),
            encoding="utf-8",
        )

    result = CliRunner().invoke(main, ["build", "--project", str(tmp_path)])

    assert result.exit_code == 0, result.output
    tex = (tmp_path / "output" / "extension_test.tex").read_text(
        encoding="utf-8"
    )
    assert tex.index("ORDERSECOND") < tex.index("ORDERFIRST")


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
