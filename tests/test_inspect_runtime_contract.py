"""Contract tests for runtime introspection exposed by ``edutex inspect``."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from click.testing import CliRunner

from edutex.core.cli import main


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "INTROSPECTION_CONTRACT.md"


def make_project(tmp_path: Path) -> Path:
    runner = CliRunner()
    project = tmp_path / "project"
    result = runner.invoke(
        main,
        ["init", str(project), "--theme", "default", "--language", "it"],
    )
    assert result.exit_code == 0, result.output
    return project


def enable_extension(project: Path, extension_id: str = "reading_tip") -> None:
    config_path = project / "edutex.config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["extensions"]["enabled"] = [extension_id]
    config_path.write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def inspect_project(project: Path):
    return CliRunner().invoke(
        main,
        [
            "inspect",
            "--project",
            str(project),
            "--config",
            "edutex.config.yaml",
            "--format",
            "json",
        ],
    )


def test_inspect_success_reports_registry_and_resolved_graph(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    result = inspect_project(project)

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert list(payload) == ["inspection"]

    inspection = payload["inspection"]
    assert inspection["status"] == "completed"
    runtime = inspection["runtime"]

    registry = runtime["registry"]
    entities = registry["entities"]
    assert registry["entity_count"] == len(entities) == 3
    assert [entity["type"] for entity in entities] == [
        "knowledge_model",
        "theme",
        "layout",
    ]
    assert all(set(entity) == {"id", "type", "source_path"} for entity in entities)
    assert all(Path(entity["source_path"]).is_absolute() for entity in entities)

    resolver = runtime["resolver"]
    assert resolver["status"] == "completed"
    assert resolver["entity_count"] == len(resolver["entities"]) == 3
    assert resolver["entities"] == entities
    assert resolver["edge_count"] == len(resolver["edges"]) == 0
    assert runtime["extensions"] == []


def test_inspect_reports_enabled_extension_without_importing_its_module(
    tmp_path: Path,
) -> None:
    project = make_project(tmp_path)
    enable_extension(project)

    extension_dir = project / "assets" / "extensions" / "reading_tip"
    module_path = extension_dir / "extension.py"
    marker_path = tmp_path / "extension-was-imported.txt"
    module_path.write_text(
        "from pathlib import Path\n"
        f"Path({str(marker_path)!r}).write_text('executed', encoding='utf-8')\n"
        "def apply(context):\n"
        "    return context.document\n",
        encoding="utf-8",
    )

    result = inspect_project(project)

    assert result.exit_code == 0, result.output
    assert not marker_path.exists(), "inspect must not execute extension code"

    payload = json.loads(result.output)
    inspection = payload["inspection"]
    extension_records = inspection["runtime"]["extensions"]
    assert len(extension_records) == 1

    extension = extension_records[0]
    assert extension["id"] == "reading_tip"
    assert extension["name"] == "Reading Tip"
    assert extension["version"] == "1.0.0"
    assert extension["target"] == "layout.post_structure"
    assert extension["module"] == "extension.py"
    assert extension["entrypoint"] == "apply"
    assert Path(extension["manifest_path"]).resolve() == (
        extension_dir / "extension.yaml"
    ).resolve()
    assert Path(extension["module_path"]).resolve() == module_path.resolve()
    assert extension["module_exists"] is True

    registry_entities = inspection["runtime"]["registry"]["entities"]
    assert [entity["type"] for entity in registry_entities] == [
        "knowledge_model",
        "theme",
        "layout",
        "extension",
    ]
    assert inspection["runtime"]["resolver"]["entities"] == registry_entities


def test_inspect_invalid_enabled_extension_keeps_failure_shape(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    enable_extension(project)

    manifest_path = (
        project / "assets" / "extensions" / "reading_tip" / "extension.yaml"
    )
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["id"] = "unexpected_id"
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    result = inspect_project(project)

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert list(payload) == ["inspection"]
    inspection = payload["inspection"]
    assert inspection["status"] == "failed"
    assert inspection["error"]["type"] == "ExtensionError"
    assert "runtime" not in inspection
    assert "configuration" not in inspection


def test_inspection_runtime_contract_documentation() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    required_markers = (
        "edutex inspect",
        "inspection.runtime",
        "runtime.registry",
        "runtime.resolver",
        "runtime.extensions",
        "entity_count",
        "edge_count",
        "source_path",
        "manifest_path",
        "module_path",
        "module_exists",
        "non deve importare",
        "Rapporto JSON di errore",
        "determinismo",
    )
    for marker in required_markers:
        assert marker in contract, f"Marker mancante: {marker}"

    assert all(
        not line.rstrip("\n").endswith((" ", "\t"))
        for line in contract.splitlines(keepends=True)
    )
