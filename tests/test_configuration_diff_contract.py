"""Contract tests for comparing a base configuration with a profile."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from click.testing import CliRunner

from edutex.core.cli import main


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "CONFIGURATION_DIFF_CONTRACT.md"


def make_project(tmp_path: Path, profiles: dict[str, object]) -> tuple[Path, Path]:
    project = tmp_path / "project"
    runner = CliRunner()
    initialized = runner.invoke(
        main,
        ["init", str(project), "--theme", "default", "--language", "it"],
    )
    assert initialized.exit_code == 0, initialized.output

    config_path = project / "edutex.config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["build"] = {
        "output_format": "pdf",
        "output_dir": "output",
        "output_file": "document",
    }
    config["profiles"] = profiles
    config_path.write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return project, config_path


def invoke_diff(project: Path, profile: str, output_format: str = "json"):
    return CliRunner().invoke(
        main,
        [
            "config",
            "diff",
            "--project",
            str(project),
            "--profile",
            profile,
            "--format",
            output_format,
        ],
    )


def test_config_diff_help_exposes_contract_options() -> None:
    result = CliRunner().invoke(main, ["config", "diff", "--help"])

    assert result.exit_code == 0, result.output
    for marker in ("--project", "--config", "--profile", "--format"):
        assert marker in result.output


def test_config_diff_json_reports_sorted_effective_changes(tmp_path: Path) -> None:
    project, config_path = make_project(
        tmp_path,
        {
            "web": {
                "build": {
                    "output_format": "html",
                    "output_dir": "web-output",
                    "output_file": "index",
                }
            }
        },
    )

    result = invoke_diff(project, "web")

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)["comparison"]
    assert payload["status"] == "completed"
    assert payload["project_root"] == str(project.resolve())
    assert payload["config_file"] == str(config_path.resolve())
    assert payload["profile"] == "web"
    assert payload["changed"] is True
    assert payload["changes"] == [
        {
            "path": "build.output_dir",
            "base_value": "output",
            "profile_value": "web-output",
        },
        {
            "path": "build.output_file",
            "base_value": "document",
            "profile_value": "index",
        },
        {
            "path": "build.output_format",
            "base_value": "pdf",
            "profile_value": "html",
        },
    ]


def test_config_diff_json_reports_no_change_as_success(tmp_path: Path) -> None:
    project, _ = make_project(tmp_path, {"same": {}})

    result = invoke_diff(project, "same")

    assert result.exit_code == 0, result.output
    comparison = json.loads(result.output)["comparison"]
    assert comparison["status"] == "completed"
    assert comparison["changed"] is False
    assert comparison["changes"] == []


def test_config_diff_text_is_readable_and_reports_differences(tmp_path: Path) -> None:
    project, _ = make_project(
        tmp_path,
        {"web": {"build": {"output_format": "html"}}},
    )

    result = invoke_diff(project, "web", "text")

    assert result.exit_code == 0, result.output
    assert "Configuration comparison: base -> profile 'web'" in result.output
    assert 'build.output_format: "pdf" -> "html"' in result.output
    assert "{\"comparison\"" not in result.output


def test_config_diff_json_preserves_error_shape_for_unknown_profile(
    tmp_path: Path,
) -> None:
    project, _ = make_project(tmp_path, {"web": {}})

    result = invoke_diff(project, "missing")

    assert result.exit_code == 1
    comparison = json.loads(result.output)["comparison"]
    assert comparison["status"] == "failed"
    assert comparison["error"]["type"] == "ConfigurationError"
    assert isinstance(comparison["error"]["message"], str)
    assert "changes" not in comparison


def test_configuration_diff_contract_documentation() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    required_markers = (
        "edutex config diff",
        "--profile NAME",
        "--format json",
        "base_value",
        "profile_value",
        "changed",
        "exit code 0",
        "ConfigurationError",
        "deterministicamente",
    )
    for marker in required_markers:
        assert marker in contract, f"Contract marker missing: {marker}"
    assert all(
        not line.rstrip("\n").endswith((" ", "\t"))
        for line in contract.splitlines(keepends=True)
    )
