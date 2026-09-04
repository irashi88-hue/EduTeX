"""End-to-end integration tests for the EduTeX CLI and processing pipeline."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from edutex.core.cli import main


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def make_test_project(path: Path) -> Path:
    """Create an isolated project containing the repository's real assets."""
    shutil.copytree(PROJECT_ROOT / "assets", path / "assets")
    return path


def write_config(path: Path, *, output_format: str) -> Path:
    """Write a test configuration into an isolated project."""
    config_path = path / "edutex.config.yaml"
    config_path.write_text(
        f'''edutex:
  version: "0.1.0"
knowledge:
  model: "assets/knowledge_models/example.md"
theme:
  name: "default"
layout:
  name: "default"
build:
  output_format: "{output_format}"
  output_dir: "output"
  output_file: "integration_document"
extensions:
  enabled: []
logging:
  level: "INFO"
''',
        encoding="utf-8",
    )
    return config_path


def test_validate_real_project() -> None:
    """The real example project passes configuration and service validation."""
    runner = CliRunner()
    result = runner.invoke(main, ["validate", "--project", str(PROJECT_ROOT)])

    assert result.exit_code == 0, result.output
    assert "pipeline are valid" in result.output


def test_build_latex_end_to_end(tmp_path: Path) -> None:
    """The CLI produces a complete LaTeX source through all processing stages."""
    project = make_test_project(tmp_path)
    write_config(project, output_format="latex")

    runner = CliRunner()
    result = runner.invoke(main, ["build", "--project", str(project)])

    assert result.exit_code == 0, result.output
    output_path = project / "output" / "integration_document.tex"
    assert output_path.is_file()

    tex = output_path.read_text(encoding="utf-8")
    assert "\\documentclass" in tex
    assert "\\section*{Introduction}" in tex
    assert "\\begin{rulebox}" in tex
    assert "\\begin{examplebox}" in tex
    assert "\\begin{notebox}" in tex
    assert "\\begin{vocabbox}" in tex
    assert "\\textbf{parlo}" in tex
    assert "\\underline{\\hspace{1.5cm}}" in tex
    assert "**" not in tex


def test_pdf_build_requires_a_latex_compiler(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A PDF request fails explicitly when no LaTeX compiler exists."""
    from edutex.build import service as build_service_module

    project = make_test_project(tmp_path)
    write_config(project, output_format="pdf")
    monkeypatch.setattr(build_service_module.shutil, "which", lambda _: None)

    runner = CliRunner()
    result = runner.invoke(main, ["build", "--project", str(project)])

    assert result.exit_code != 0
    assert "requires 'latexmk' or 'pdflatex'" in result.output
    assert (project / "output" / "integration_document.tex").is_file()


@pytest.mark.skipif(
    shutil.which("latexmk") is None and shutil.which("pdflatex") is None,
    reason="No LaTeX compiler installed in the test environment",
)
def test_pdf_build_with_available_compiler(tmp_path: Path) -> None:
    """When LaTeX is installed, the configured PDF output is actually produced."""
    project = make_test_project(tmp_path)
    write_config(project, output_format="pdf")

    runner = CliRunner()
    result = runner.invoke(main, ["build", "--project", str(project)])

    assert result.exit_code == 0, result.output
    assert (project / "output" / "integration_document.tex").is_file()
    assert (project / "output" / "integration_document.pdf").is_file()
