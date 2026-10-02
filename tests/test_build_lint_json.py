"""Integration tests for the opt-in build lint preflight."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from edutex.core.cli import main


VALID_SOURCE = """---
id: valid-lesson
title: Valid lesson
language: en
level: A1
version: 1.0.0
author: EduTeX
---

::: formula.math
E = mc^2
:::
"""

WARNING_SOURCE = """---
id: warning-lesson
title: Warning lesson
language: en
level: A1
version: 1.0.0
author: EduTeX
---

::: exercise
Write a sentence.
:::
"""

ERROR_SOURCE = """---
id: invalid-lesson
title: Invalid lesson
language: en
level: A1
version: 1.0.0
author: EduTeX
---

::: formula.math
:::
"""


def make_project(path: Path, source: str) -> Path:
    """Create a starter project and replace its configured Knowledge Model."""
    result = CliRunner().invoke(main, ["init", str(path), "--theme", "default", "--language", "en"])
    assert result.exit_code == 0, result.output
    model = path / "assets" / "knowledge_models" / "example.md"
    model.write_text(source, encoding="utf-8")
    return path


def test_build_without_lint_does_not_print_lint_report(tmp_path: Path) -> None:
    project = make_project(tmp_path / "project", ERROR_SOURCE)

    result = CliRunner().invoke(main, ["build", "--project", str(project)])

    assert result.exit_code == 0, result.output
    assert "SC001" not in result.output
    assert (project / "output" / "document.html").is_file()


def test_build_with_lint_blocks_on_errors(tmp_path: Path) -> None:
    project = make_project(tmp_path / "project", ERROR_SOURCE)

    result = CliRunner().invoke(main, ["build", "--project", str(project), "--lint"])

    assert result.exit_code == 1
    assert "[SC101]" in result.output
    assert "Build blocked: shortcode lint found errors." in result.output
    assert "Build completed:" not in result.output
    assert not (project / "output" / "document.html").exists()


def test_build_with_lint_continues_on_warnings(tmp_path: Path) -> None:
    project = make_project(tmp_path / "project", WARNING_SOURCE)

    result = CliRunner().invoke(main, ["build", "--project", str(project), "--lint"])

    assert result.exit_code == 0, result.output
    assert "[SC201]" in result.output
    assert "Build completed:" in result.output
    assert (project / "output" / "document.html").is_file()


def test_build_with_lint_accepts_absolute_knowledge_model_path(tmp_path: Path) -> None:
    project = make_project(tmp_path / "project", VALID_SOURCE)
    model = project / "assets" / "knowledge_models" / "example.md"
    config_path = project / "edutex.config.yaml"
    config = config_path.read_text(encoding="utf-8")
    config_path.write_text(
        config.replace('model: "assets/knowledge_models/example.md"', f'model: "{model.as_posix()}"'),
        encoding="utf-8",
    )

    result = CliRunner().invoke(main, ["build", "--project", str(project), "--lint"])

    assert result.exit_code == 0, result.output
    assert "No shortcode errors found." in result.output
    assert (project / "output" / "document.html").is_file()


def test_build_with_lint_reports_missing_knowledge_model(tmp_path: Path) -> None:
    project = make_project(tmp_path / "project", VALID_SOURCE)
    config_path = project / "edutex.config.yaml"
    config = config_path.read_text(encoding="utf-8")
    config_path.write_text(
        config.replace(
            'model: "assets/knowledge_models/example.md"',
            'model: "assets/knowledge_models/missing.md"',
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(main, ["build", "--project", str(project), "--lint"])

    assert result.exit_code != 0
    assert "Knowledge Model not found" in result.output
    assert "Build completed:" not in result.output
    assert not (project / "output" / "document.html").exists()

def parse_build_json(result):
    """Decode the complete JSON contract emitted by build."""
    assert result.output.strip(), result.output
    return json.loads(result.output)


def test_build_with_lint_json_succeeds_and_reports_output(tmp_path: Path) -> None:
    project = make_project(tmp_path / "project", VALID_SOURCE)

    result = CliRunner().invoke(
        main,
        ["build", "--project", str(project), "--lint", "--format", "json"],
    )

    assert result.exit_code == 0, result.output
    payload = parse_build_json(result)
    assert list(payload) == ["lint", "build"]
    assert payload["lint"]["valid"] is True
    assert payload["lint"]["errors"] == []
    assert payload["lint"]["warnings"] == []
    assert payload["build"]["status"] == "completed"
    assert payload["build"]["output"].endswith("document.html")
    metadata = payload["build"]["metadata"]
    assert metadata["project_root"] == str(project.resolve())
    assert metadata["config_file"] == str((project / "edutex.config.yaml").resolve())
    assert metadata["output_format"] == "html"
    assert metadata["output_path"] == payload["build"]["output"]
    assert metadata["output_exists"] is True


def test_build_with_lint_json_preserves_warnings_and_continues(tmp_path: Path) -> None:
    project = make_project(tmp_path / "project", WARNING_SOURCE)

    result = CliRunner().invoke(
        main,
        ["build", "--project", str(project), "--lint", "--format", "json"],
    )

    assert result.exit_code == 0, result.output
    payload = parse_build_json(result)
    assert payload["lint"]["valid"] is True
    assert payload["lint"]["errors"] == []
    assert payload["lint"]["warnings"][0]["code"] == "SC201"
    assert payload["build"]["status"] == "completed"
    assert (project / "output" / "document.html").is_file()


def test_build_with_lint_json_blocks_on_errors(tmp_path: Path) -> None:
    project = make_project(tmp_path / "project", ERROR_SOURCE)

    result = CliRunner().invoke(
        main,
        ["build", "--project", str(project), "--lint", "--format", "json"],
    )

    assert result.exit_code == 1
    payload = parse_build_json(result)
    assert payload["lint"]["valid"] is False
    assert payload["lint"]["errors"][0]["code"] == "SC101"
    assert payload["build"]["status"] == "blocked"
    assert payload["build"]["message"] == "Build blocked: shortcode lint found errors."
    assert "output" not in payload["build"]
    assert "metadata" not in payload["build"]
    assert not (project / "output" / "document.html").exists()



def test_build_json_reports_missing_knowledge_model_as_structured_error(tmp_path: Path) -> None:
    project = make_project(tmp_path / "project", VALID_SOURCE)
    config_path = project / "edutex.config.yaml"
    config = config_path.read_text(encoding="utf-8")
    config_path.write_text(
        config.replace(
            'model: "assets/knowledge_models/example.md"',
            'model: "assets/knowledge_models/missing.md"',
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        main,
        ["build", "--project", str(project), "--format", "json"],
    )

    assert result.exit_code == 1
    payload = parse_build_json(result)
    assert list(payload) == ["lint", "build"]
    assert payload["lint"] is None
    assert payload["build"]["status"] == "failed"
    assert payload["build"]["error"]["type"] == "KnowledgeError"
    assert "Knowledge Model not found" in payload["build"]["error"]["message"]
    assert "Error:" not in result.output


def test_build_json_reports_missing_config_as_structured_error(tmp_path: Path) -> None:
    project = make_project(tmp_path / "project", VALID_SOURCE)

    result = CliRunner().invoke(
        main,
        ["build", "--project", str(project), "--config", "missing.yaml", "--format", "json"],
    )

    assert result.exit_code == 1
    payload = parse_build_json(result)
    assert payload["lint"] is None
    assert payload["build"]["status"] == "failed"
    assert payload["build"]["error"]["type"] == "ConfigurationError"
    assert "Configuration file not found" in payload["build"]["error"]["message"]
    assert "Error:" not in result.output

def test_build_error_json_serializes_extension_diagnostics():
    import json

    from edutex.core.cli import _format_build_error_json
    from edutex.extension.models import ExtensionDiagnostic

    diagnostics = (
        ExtensionDiagnostic(
            extension_id="reading_tip",
            point_id="layout.post_structure",
            phase="handler",
            message="handler boom",
        ),
    )

    payload = json.loads(
        _format_build_error_json(
            "Extension processing failed",
            error_type="ExtensionError",
            diagnostics=diagnostics,
        )
    )

    assert payload["build"]["status"] == "failed"
    assert payload["build"]["error"]["type"] == "ExtensionError"
    assert payload["build"]["error"]["diagnostics"] == [
        {
            "extension_id": "reading_tip",
            "point_id": "layout.post_structure",
            "phase": "handler",
            "message": "handler boom",
        }
    ]

def test_build_json_reports_extension_diagnostics(tmp_path: Path) -> None:
    project = make_project(tmp_path / "project", VALID_SOURCE)

    extension_dir = project / "assets" / "extensions" / "failing_extension"
    extension_dir.mkdir()
    (extension_dir / "extension.yaml").write_text(
        "id: failing_extension\n"
        "name: Failing Extension\n"
        "version: 1.0.0\n"
        "target: layout.post_structure\n"
        "module: extension.py\n"
        "entrypoint: apply\n",
        encoding="utf-8",
    )
    (extension_dir / "extension.py").write_text(
        "def apply(context):\n"
        "    raise RuntimeError('diagnostic boom')\n",
        encoding="utf-8",
    )

    config_path = project / "edutex.config.yaml"
    config = config_path.read_text(encoding="utf-8")
    if "enabled: []" not in config:
        raise AssertionError("Configurazione extensions attesa non trovata.")
    config_path.write_text(
        config.replace(
            "enabled: []",
            'enabled: ["failing_extension"]',
            1,
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        main,
        ["build", "--project", str(project), "--format", "json"],
    )

    assert result.exit_code == 1, result.output
    payload = parse_build_json(result)
    error = payload["build"]["error"]

    assert payload["build"]["status"] == "failed"
    assert error["type"] == "ExtensionError"
    assert "diagnostic boom" in error["message"]
    assert error["diagnostics"] == [
        {
            "extension_id": "failing_extension",
            "point_id": "layout.post_structure",
            "phase": "handler",
            "message": error["diagnostics"][0]["message"],
        }
    ]

def test_build_text_reports_extension_diagnostics(tmp_path: Path) -> None:
    project = make_project(tmp_path / "project", VALID_SOURCE)

    extension_dir = project / "assets" / "extensions" / "failing_extension"
    extension_dir.mkdir()
    (extension_dir / "extension.yaml").write_text(
        "id: failing_extension\n"
        "name: Failing Extension\n"
        "version: 1.0.0\n"
        "target: layout.post_structure\n"
        "module: extension.py\n"
        "entrypoint: apply\n",
        encoding="utf-8",
    )
    (extension_dir / "extension.py").write_text(
        "def apply(context):\n"
        "    raise RuntimeError('build text diagnostic boom')\n",
        encoding="utf-8",
    )

    config_path = project / "edutex.config.yaml"
    config = config_path.read_text(encoding="utf-8")
    config_path.write_text(
        config.replace("enabled: []", 'enabled: ["failing_extension"]', 1),
        encoding="utf-8",
    )

    result = CliRunner().invoke(main, ["build", "--project", str(project)])

    assert result.exit_code == 1, result.output
    assert "Extension diagnostics:" in result.output
    assert "extension_id=failing_extension" in result.output
    assert "point_id=layout.post_structure" in result.output
    assert "phase=handler" in result.output
    assert "build text diagnostic boom" in result.output
