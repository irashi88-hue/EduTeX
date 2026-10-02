"""Test del contratto di introspection tooling di EduTeX."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from edutex.core.cli import main


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "INTROSPECTION_CONTRACT.md"


def make_project(tmp_path: Path) -> Path:
    runner = CliRunner()
    project = tmp_path / "project"

    result = runner.invoke(
        main,
        [
            "init",
            str(project),
            "--theme",
            "default",
            "--language",
            "it",
        ],
    )

    assert result.exit_code == 0, result.output
    return project


def test_documentazione_introspection() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")

    required_markers = (
        "edutex inspect",
        "inspection",
        "project_root",
        "config_file",
        "framework_version",
        "knowledge_model",
        "output_format",
        "output_dir",
        "output_file",
        "assets",
        "ConfigurationError",
        "determinismo",
    )

    for marker in required_markers:
        assert marker in contract, f"Marker mancante: {marker}"

    assert all(
        not line.rstrip("\n").endswith((" ", "\t"))
        for line in contract.splitlines(keepends=True)
    )


def test_inspect_json_success(tmp_path: Path) -> None:
    runner = CliRunner()
    project = make_project(tmp_path)

    result = runner.invoke(
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

    assert result.exit_code == 0, result.output

    payload = json.loads(result.output)
    assert list(payload) == ["inspection"]

    inspection = payload["inspection"]
    assert inspection["status"] == "completed"
    assert Path(inspection["project_root"]).resolve() == project.resolve()
    assert (
        Path(inspection["config_file"]).resolve()
        == (project / "edutex.config.yaml").resolve()
    )

    configuration = inspection["configuration"]
    assert configuration["framework_version"] == "1.0.0"
    assert configuration["knowledge_model"] == (
        "assets/knowledge_models/example.md"
    )
    assert configuration["theme"] == "default"
    assert configuration["layout"] == "default"
    assert configuration["build"]["output_format"] == "html"
    assert Path(configuration["build"]["output_dir"]).resolve() == (
        project / "output"
    ).resolve()
    assert configuration["build"]["output_file"] == "document"
    assert configuration["extensions"] == []
    assert configuration["logging_level"] == "INFO"

    assets = inspection["assets"]
    assert assets["knowledge_model"]["exists"] is True
    assert assets["theme"]["exists"] is True
    assert assets["layout"]["exists"] is True
    assert assets["extensions"] == []


def test_inspect_missing_config_is_structured_json_error(tmp_path: Path) -> None:
    runner = CliRunner()
    project = make_project(tmp_path)

    result = runner.invoke(
        main,
        [
            "inspect",
            "--project",
            str(project),
            "--config",
            "missing.yaml",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 1

    payload = json.loads(result.output)
    assert list(payload) == ["inspection"]
    assert payload["inspection"]["status"] == "failed"

    error = payload["inspection"]["error"]
    assert error["type"] == "ConfigurationError"
    assert "Configuration file not found" in error["message"]
