"""Smoke tests for the beginner-friendly project workflow."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from edutex.core.cli import main


def test_init_validate_and_build_html(tmp_path: Path) -> None:
    project = tmp_path / "starter"
    runner = CliRunner()

    initialized = runner.invoke(main, ["init", str(project)])
    assert initialized.exit_code == 0, initialized.output
    assert (project / "edutex.config.yaml").is_file()
    assert (project / "assets/knowledge_models/example.md").is_file()
    assert (project / "assets/themes/dark/theme.yaml").is_file()
    assert (project / "assets/themes/default/theme.yaml").is_file()
    assert (project / "assets/layouts/default/layout.yaml").is_file()

    validated = runner.invoke(main, ["validate", "--project", str(project)])
    assert validated.exit_code == 0, validated.output

    built = runner.invoke(main, ["build", "--project", str(project)])
    assert built.exit_code == 0, built.output
    output = project / "output" / "document.html"
    assert output.is_file()
    assert "<!doctype html>" in output.read_text(encoding="utf-8")
