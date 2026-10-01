"""Test del contratto runtime della configurazione EduTeX."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from pydantic import ValidationError

from edutex.configuration.schema import EduTexConfig, LogLevel, OutputFormat
from edutex.core.cli import main


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "CONFIGURATION_RUNTIME_CONTRACT.md"


def minimal_config() -> dict[str, object]:
    return {
        "edutex": {"version": "1.0.0"},
        "knowledge": {"model": "assets/knowledge_models/example.md"},
        "theme": {"name": "default"},
        "layout": {"name": "default"},
    }


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


def test_documentazione_configurazione_runtime() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")

    required_markers = (
        "EduTexConfig",
        "knowledge.model",
        "build.output_dir",
        "build.output_file",
        "OutputFormat",
        "LogLevel",
        "ConfigurationError",
        "project_root",
        "edutex.config.yaml",
        "immutabile",
    )

    for marker in required_markers:
        assert marker in contract, f"Marker mancante: {marker}"

    assert all(
        not line.rstrip("\n").endswith((" ", "\t"))
        for line in contract.splitlines(keepends=True)
    )


def test_schema_defaults_and_enum_values() -> None:
    config = EduTexConfig.model_validate(minimal_config())

    assert config.build.output_format is OutputFormat.pdf
    assert config.build.output_dir == Path("output")
    assert config.build.output_file == "document"
    assert config.extensions.enabled == []
    assert config.logging.level is LogLevel.info

    assert set(item.value for item in OutputFormat) == {
        "pdf",
        "latex",
        "html",
    }
    assert set(item.value for item in LogLevel) == {
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
    }


def test_schema_normalizes_names_and_rejects_empty_values() -> None:
    raw = minimal_config()
    raw["theme"] = {"name": "  default  "}
    raw["layout"] = {"name": "  default  "}
    raw["extensions"] = {"enabled": [" reading_tip "]}
    raw["logging"] = {"level": "WARNING"}

    config = EduTexConfig.model_validate(raw)

    assert config.theme.name == "default"
    assert config.layout.name == "default"
    assert config.extensions.enabled == ["reading_tip"]
    assert config.logging.level is LogLevel.warning

    invalid = minimal_config()
    invalid["knowledge"] = {"model": "   "}
    with pytest.raises(ValidationError):
        EduTexConfig.model_validate(invalid)


def test_schema_is_immutable() -> None:
    config = EduTexConfig.model_validate(minimal_config())

    with pytest.raises((TypeError, ValidationError)):
        config.build.output_file = "changed"

    with pytest.raises(TypeError, match="immutable"):
        config.extensions.enabled.append("reading_tip")


def test_relative_and_absolute_config_paths_are_accepted(tmp_path: Path) -> None:
    runner = CliRunner()
    project = make_project(tmp_path)
    config = project / "edutex.config.yaml"

    relative_result = runner.invoke(
        main,
        [
            "validate",
            "--project",
            str(project),
            "--config",
            "edutex.config.yaml",
            "--format",
            "json",
        ],
    )
    assert relative_result.exit_code == 0, relative_result.output
    assert json.loads(relative_result.output) == {
        "validation": {"status": "completed"}
    }

    absolute_result = runner.invoke(
        main,
        [
            "validate",
            "--project",
            str(project),
            "--config",
            str(config.resolve()),
            "--format",
            "json",
        ],
    )
    assert absolute_result.exit_code == 0, absolute_result.output
    assert json.loads(absolute_result.output) == {
        "validation": {"status": "completed"}
    }


def test_missing_config_is_structured_json_error(tmp_path: Path) -> None:
    runner = CliRunner()
    project = make_project(tmp_path)

    result = runner.invoke(
        main,
        [
            "validate",
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
    error = payload["validation"]["error"]
    assert payload["validation"]["status"] == "failed"
    assert error["type"] == "ConfigurationError"
    assert "Configuration file not found" in error["message"]
