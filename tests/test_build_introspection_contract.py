"""Test del contratto di introspection dei metadati di build."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from edutex.core.cli import main


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "BUILD_INTROSPECTION_CONTRACT.md"


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


def test_documentazione_build_introspection() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")

    required_markers = (
        "edutex build --format json",
        "build.metadata",
        "project_root",
        "config_file",
        "output_format",
        "output_path",
        "output_exists",
        "build.output",
        "build.error",
        "Determinismo",
    )

    for marker in required_markers:
        assert marker in contract, f"Marker mancante: {marker}"

    assert all(
        not line.rstrip("\n").endswith((" ", "\t"))
        for line in contract.splitlines(keepends=True)
    )


def test_build_json_success_contains_metadata(tmp_path: Path) -> None:
    runner = CliRunner()
    project = make_project(tmp_path)
    config_path = project / "edutex.config.yaml"

    result = runner.invoke(
        main,
        [
            "build",
            "--project",
            str(project),
            "--config",
            str(config_path),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0, result.output

    payload = json.loads(result.output)
    assert payload["lint"] is None

    build = payload["build"]
    assert build["status"] == "completed"
    assert Path(build["output"]).is_absolute()

    metadata = build["metadata"]
    assert Path(metadata["project_root"]).resolve() == project.resolve()
    assert Path(metadata["config_file"]).resolve() == config_path.resolve()
    assert metadata["output_format"] == "html"
    assert Path(metadata["output_path"]).resolve() == Path(build["output"]).resolve()
    assert metadata["output_exists"] is True
    assert Path(metadata["output_path"]).is_file()


def test_build_json_missing_config_preserves_error_contract(tmp_path: Path) -> None:
    runner = CliRunner()
    project = make_project(tmp_path)

    result = runner.invoke(
        main,
        [
            "build",
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
    assert payload["lint"] is None
    assert payload["build"]["status"] == "failed"
    assert payload["build"]["error"]["type"] == "ConfigurationError"
    assert "metadata" not in payload["build"]
