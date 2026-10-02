"""Contract tests for selectable EduTeX configuration profiles."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from edutex.configuration.loader import load_config
from edutex.core.cli import main
from edutex.core.errors import ConfigurationError


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "CONFIGURATION_PROFILES_CONTRACT.md"


def minimal_config() -> dict[str, object]:
    return {
        "edutex": {"version": "1.0.0"},
        "knowledge": {"model": "assets/knowledge_models/example.md"},
        "theme": {"name": "default"},
        "layout": {"name": "default"},
    }


def write_config(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def make_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    result = CliRunner().invoke(
        main,
        ["init", str(project), "--theme", "default", "--language", "it"],
    )
    assert result.exit_code == 0, result.output

    config_path = project / "edutex.config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["extensions"] = {"enabled": []}
    config["profiles"] = {
        "web": {
            "build": {
                "output_format": "html",
                "output_dir": "profile-output",
                "output_file": "web-document",
            }
        },
        "course-missing-theme": {"theme": {"name": "not-installed"}},
    }
    write_config(config_path, config)
    return project


def test_profile_merge_is_recursive_and_replaces_lists_and_scalars(
    tmp_path: Path,
) -> None:
    path = tmp_path / "edutex.config.yaml"
    payload = minimal_config()
    payload["build"] = {
        "output_format": "pdf",
        "output_dir": "artifacts",
        "output_file": "base-document",
    }
    payload["extensions"] = {"enabled": ["base_extension", "shared_extension"]}
    payload["profiles"] = {
        "web": {
            "build": {
                "output_format": "html",
                "output_file": "web-document",
            },
            "extensions": {"enabled": ["reading_tip"]},
        },
        "dark": {"theme": {"name": "dark"}},
    }
    write_config(path, payload)

    base = load_config(path)
    web = load_config(path, profile="web")
    dark = load_config(path, profile="dark")

    assert base.build.output_format.value == "pdf"
    assert base.extensions.enabled == ["base_extension", "shared_extension"]
    assert web.build.output_format.value == "html"
    assert web.build.output_dir == Path("artifacts")
    assert web.build.output_file == "web-document"
    assert web.extensions.enabled == ["reading_tip"]
    assert dark.theme.name == "dark"
    assert dark.build.output_format.value == "pdf"
    assert "profiles" not in web.model_dump()

    with pytest.raises(TypeError, match="immutable"):
        web.extensions.enabled.append("another_extension")


def test_unknown_profile_and_invalid_selected_override_raise_configuration_error(
    tmp_path: Path,
) -> None:
    path = tmp_path / "edutex.config.yaml"
    payload = minimal_config()
    payload["profiles"] = {
        "web": {"build": {"output_format": "not-a-format"}},
    }
    write_config(path, payload)

    with pytest.raises(ConfigurationError, match="Unknown configuration profile"):
        load_config(path, profile="missing")
    with pytest.raises(ConfigurationError, match="Configuration validation failed"):
        load_config(path, profile="web")


def test_profile_definitions_are_checked_even_when_not_selected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "edutex.config.yaml"
    payload = minimal_config()
    payload["profiles"] = {"web": []}
    write_config(path, payload)

    with pytest.raises(ConfigurationError, match="must be a YAML mapping"):
        load_config(path)

    payload["profiles"] = {"web": {"build": {"output_fomrat": "html"}}}
    write_config(path, payload)
    with pytest.raises(ConfigurationError, match="unknown field"):
        load_config(path)

    payload["profiles"] = {" web ": {"build": {"output_format": "html"}}}
    write_config(path, payload)
    with pytest.raises(ConfigurationError, match="non-empty strings without surrounding whitespace"):
        load_config(path)


def test_cli_build_validate_and_inspect_apply_selected_profile(
    tmp_path: Path,
) -> None:
    project = make_project(tmp_path)
    runner = CliRunner()

    build_result = runner.invoke(
        main,
        ["build", "--project", str(project), "--profile", "web", "--format", "json"],
    )
    assert build_result.exit_code == 0, build_result.output
    build_payload = json.loads(build_result.output)
    build = build_payload["build"]
    assert build["status"] == "completed"
    metadata = build["metadata"]
    assert metadata["output_format"] == "html"
    expected_output = (project / "profile-output" / "web-document.html").resolve()
    assert Path(metadata["output_path"]).resolve() == expected_output
    assert Path(metadata["project_root"]).resolve() == project.resolve()
    assert Path(metadata["config_file"]).resolve() == (project / "edutex.config.yaml").resolve()
    assert metadata["output_path"] == build["output"]
    assert Path(metadata["output_path"]).is_absolute()
    assert metadata["output_exists"] is True

    validate_result = runner.invoke(
        main,
        ["validate", "--project", str(project), "--profile", "web", "--format", "json"],
    )
    assert validate_result.exit_code == 0, validate_result.output
    assert json.loads(validate_result.output) == {"validation": {"status": "completed"}}

    inspect_result = runner.invoke(
        main,
        ["inspect", "--project", str(project), "--profile", "web", "--format", "json"],
    )
    assert inspect_result.exit_code == 0, inspect_result.output
    inspection = json.loads(inspect_result.output)["inspection"]
    assert inspection["configuration"]["profile"] == "web"
    assert inspection["configuration"]["build"]["output_format"] == "html"


def test_profile_failures_keep_json_error_shapes(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    runner = CliRunner()

    build_result = runner.invoke(
        main,
        ["build", "--project", str(project), "--profile", "missing", "--format", "json"],
    )
    assert build_result.exit_code == 1
    build = json.loads(build_result.output)["build"]
    assert build["status"] == "failed"
    assert build["error"]["type"] == "ConfigurationError"
    assert "metadata" not in build

    validate_result = runner.invoke(
        main,
        ["validate", "--project", str(project), "--profile", "missing", "--format", "json"],
    )
    assert validate_result.exit_code == 1
    validation = json.loads(validate_result.output)["validation"]
    assert validation["status"] == "failed"
    assert validation["error"]["type"] == "ConfigurationError"

    inspect_result = runner.invoke(
        main,
        ["inspect", "--project", str(project), "--profile", "missing", "--format", "json"],
    )
    assert inspect_result.exit_code == 1
    inspection = json.loads(inspect_result.output)["inspection"]
    assert inspection["status"] == "failed"
    assert inspection["error"]["type"] == "ConfigurationError"


def test_course_build_rejects_profiles_for_pdf_and_latex(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    runner = CliRunner()

    for output_format in ("pdf", "latex"):
        result = runner.invoke(
            main,
            [
                "course",
                "build",
                "--project",
                str(project),
                "--profile",
                "web",
                "--format",
                output_format,
            ],
        )
        assert result.exit_code == 1
        assert "only with --format html" in result.output

    selected_profile = runner.invoke(
        main,
        [
            "course",
            "build",
            "--project",
            str(project),
            "--profile",
            "course-missing-theme",
            "--format",
            "html",
        ],
    )
    assert selected_profile.exit_code == 1
    assert "Theme asset not found" in selected_profile.output

    missing = runner.invoke(
        main,
        ["course", "build", "--project", str(project), "--profile", "missing"],
    )
    assert missing.exit_code == 1
    assert "Unknown configuration profile" in missing.output


def test_configuration_profiles_contract_documentation() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    required_markers = (
        "edutex.config.yaml",
        "profiles:",
        "EduTexConfig",
        "override ricorsivo",
        "Liste e valori scalari",
        "senza ereditarietà",
        "edutex build",
        "edutex validate",
        "edutex inspect",
        "edutex course build",
        "--profile NAME",
        "inspection.configuration.profile",
        "ConfigurationError",
        "immutabilità",
        "pdf",
        "latex",
        "html",
    )
    for marker in required_markers:
        assert marker in contract, f"Marker mancante: {marker}"
    assert all(
        not line.rstrip("\n").endswith((" ", "\t"))
        for line in contract.splitlines(keepends=True)
    )
