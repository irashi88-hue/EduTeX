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


def make_project(path: Path) -> Path:
    result = CliRunner().invoke(
        main,
        ["init", str(path), "--theme", "default", "--language", "en"],
    )
    assert result.exit_code == 0, result.output

    model = path / "assets" / "knowledge_models" / "example.md"
    model.write_text(VALID_SOURCE, encoding="utf-8")
    return path


def test_validate_json_succeeds(tmp_path: Path) -> None:
    project = make_project(tmp_path / "project")

    result = CliRunner().invoke(
        main,
        ["validate", "--project", str(project), "--format", "json"],
    )

    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {
        "validation": {
            "status": "completed",
        },
    }


def test_validate_text_output_remains_unchanged(tmp_path: Path) -> None:
    project = make_project(tmp_path / "project")

    result = CliRunner().invoke(
        main,
        ["validate", "--project", str(project)],
    )

    assert result.exit_code == 0, result.output
    assert result.output.strip() == (
        "Configuration, assets, and processing pipeline are valid."
    )


def test_validate_json_reports_extension_diagnostics(tmp_path: Path) -> None:
    project = make_project(tmp_path / "project")

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
        "    raise RuntimeError('validate diagnostic boom')\n",
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
        ["validate", "--project", str(project), "--format", "json"],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    error = payload["validation"]["error"]

    assert payload["validation"]["status"] == "failed"
    assert error["type"] == "ExtensionError"
    assert "validate diagnostic boom" in error["message"]
    assert error["diagnostics"] == [
        {
            "extension_id": "failing_extension",
            "point_id": "layout.post_structure",
            "phase": "handler",
            "message": error["diagnostics"][0]["message"],
        }
    ]


def test_validate_help_exposes_format_option() -> None:
    result = CliRunner().invoke(main, ["validate", "--help"])

    assert result.exit_code == 0, result.output
    assert "--format" in result.output
