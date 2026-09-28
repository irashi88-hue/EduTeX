"""Unit and integration-oriented tests for the Extension System."""

from __future__ import annotations

from copy import deepcopy
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest
from click.testing import CliRunner

from edutex.activator.activator import Activator
from edutex.configuration.loader import load_config
from edutex.core.cli import _register_project_assets, main
from edutex.core.errors import ExtensionError
from edutex.extension.loader import ExtensionLoader
from edutex.extension.models import (
    ExtensionManifest,
    ExtensionPoint,
    LoadedExtension,
)
from edutex.extension.registry import ExtensionPointRegistry
from edutex.extension.service import ExtensionService
from edutex.knowledge.service import KnowledgeService
from edutex.layout.service import LayoutService
from edutex.resolver.resolver import Resolver
from edutex.theme.service import ThemeService


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


def test_public_extension_api_exports_registry() -> None:
    import edutex.extension as public_extension

    assert public_extension.ExtensionPointRegistry is ExtensionPointRegistry
    assert "ExtensionPointRegistry" in public_extension.__all__


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


def test_extension_mutation_is_isolated_from_layout(tmp_path: Path) -> None:
    make_project(tmp_path, extension_ids=["mutator"])

    extension_dir = tmp_path / "assets" / "extensions" / "mutator"
    extension_dir.mkdir()
    (extension_dir / "extension.yaml").write_text(
        "id: mutator\n"
        "name: Mutator\n"
        "version: 1.0.0\n"
        "target: layout.post_structure\n"
        "module: extension.py\n"
        "entrypoint: apply\n",
        encoding="utf-8",
    )
    (extension_dir / "extension.py").write_text(
        "from edutex.extension.models import ExtensionContext\n"
        "from edutex.knowledge.models import TextBlock\n\n"
        "def apply(context: ExtensionContext):\n"
        "    context.document.prose_blocks.append(\n"
        "        (10, TextBlock(content='ISOLATION_MARKER'))\n"
        "    )\n"
        "    return context.document\n",
        encoding="utf-8",
    )

    config = load_config(tmp_path / "edutex.config.yaml")
    registry = _register_project_assets(config, tmp_path)
    state = Activator().activate(Resolver(registry).resolve())

    knowledge = KnowledgeService()
    knowledge.process(state, tmp_path)
    theme = ThemeService()
    theme.process(state, knowledge, tmp_path)
    layout = LayoutService()
    layout.process(state, theme, tmp_path)

    original_prose_blocks = deepcopy(layout.document.prose_blocks)

    extensions = ExtensionService()
    extensions.process(
        state,
        layout,
        tmp_path,
        extension_order=config.extensions.enabled,
    )

    assert layout.document.prose_blocks == original_prose_blocks
    assert any(
        "ISOLATION_MARKER" in block.content
        for _, block in extensions.document.prose_blocks
    )


def test_loader_rejects_non_callable_entrypoint(tmp_path: Path) -> None:
    module = tmp_path / "extension.py"
    module.write_text("VALUE = 42\n", encoding="utf-8")

    manifest = tmp_path / "extension.yaml"
    manifest.write_text(
        "id: invalid_entrypoint\n"
        "name: Invalid Entrypoint\n"
        "version: 1.0.0\n"
        "target: layout.post_structure\n"
        "module: extension.py\n"
        "entrypoint: VALUE\n",
        encoding="utf-8",
    )

    with pytest.raises(ExtensionError, match="not a callable"):
        ExtensionLoader().load(manifest)


def _make_extension_error_fixture(monkeypatch, handler, target="layout.post_structure"):
    manifest = ExtensionManifest(
        extension_id="test_extension",
        name="Test Extension",
        version="1.0.0",
        target=target,
        module="extension.py",
        entrypoint="apply",
    )
    loaded = LoadedExtension(manifest=manifest, handler=handler)

    def fake_load(_loader, _manifest_path, expected_id=None):
        return loaded

    monkeypatch.setattr(ExtensionLoader, "load", fake_load)

    state = SimpleNamespace(
        get_by_type=lambda _entity_type: [
            SimpleNamespace(
                entity_id="test_extension",
                source_path=Path("extension.yaml"),
            )
        ]
    )
    layout = SimpleNamespace(document=object())
    return state, layout


def test_extension_rejects_undeclared_extension_point(monkeypatch) -> None:
    state, layout = _make_extension_error_fixture(
        monkeypatch,
        lambda context: context.document,
        target="missing.point",
    )

    with pytest.raises(ExtensionError, match="undeclared"):
        ExtensionService().process(state, layout, Path("."))


def test_extension_handler_failure_is_fatal(monkeypatch) -> None:
    def fail(_context):
        raise RuntimeError("handler boom")

    state, layout = _make_extension_error_fixture(monkeypatch, fail)

    with pytest.raises(ExtensionError, match="failed at.*handler boom"):
        ExtensionService().process(state, layout, Path("."))


def test_extension_rejects_invalid_contribution_type(monkeypatch) -> None:
    state, layout = _make_extension_error_fixture(
        monkeypatch,
        lambda _context: None,
    )

    with pytest.raises(ExtensionError, match="expected DocumentStructure"):
        ExtensionService().process(state, layout, Path("."))


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

def test_extension_service_clears_stale_state_after_failed_process(monkeypatch):
    from types import SimpleNamespace

    from edutex.extension.models import ExtensionManifest, LoadedExtension
    from edutex.layout.models import DocumentStructure

    document = DocumentStructure(
        elements=[],
        prose_blocks=[],
        layout_model=object(),
    )
    calls = []

    manifest = ExtensionManifest(
        extension_id="test_extension",
        name="Test Extension",
        version="1.0.0",
        target="layout.post_structure",
        module="extension.py",
        entrypoint="apply",
    )

    def handler(context):
        calls.append(True)
        if len(calls) > 1:
            raise RuntimeError("second pass failed")
        return context.document

    loaded = LoadedExtension(manifest=manifest, handler=handler)

    def fake_load(_loader, _manifest_path, expected_id=None):
        return loaded

    monkeypatch.setattr(ExtensionLoader, "load", fake_load)

    state = SimpleNamespace(
        get_by_type=lambda _entity_type: [
            SimpleNamespace(
                entity_id="test_extension",
                source_path=Path("extension.yaml"),
            )
        ]
    )
    layout = SimpleNamespace(document=document)
    service = ExtensionService()

    service.process(state, layout, Path("."))
    assert service.document is not None
    assert len(service.loaded_extensions) == 1

    with pytest.raises(ExtensionError, match="second pass failed"):
        service.process(state, layout, Path("."))

    assert service.loaded_extensions == ()
    with pytest.raises(ExtensionError, match=r"process\(\) has not been called"):
        _ = service.document
