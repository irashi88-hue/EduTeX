"""Test del contratto dell'anteprima HTML del Knowledge Model."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from edutex.core.cli import main


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "KNOWLEDGE_PREVIEW_CONTRACT.md"


def make_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    result = CliRunner().invoke(main, ["init", str(project), "--theme", "dark"])
    assert result.exit_code == 0, result.output
    return project


def test_documentazione_preview() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    for marker in (
        "edutex preview",
        "SOURCE_FILE",
        "output/preview",
        "theme.name",
        "layout.name",
        "--profile",
        "non modifica",
        "exit code `0`",
    ):
        assert marker in contract, f"Marker mancante: {marker}"
    assert all(
        not line.rstrip("\n").endswith((" ", "\t"))
        for line in contract.splitlines(keepends=True)
    )


def test_preview_generates_html_with_project_style_without_changing_normal_build(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    config = project / "edutex.config.yaml"
    original_config = config.read_text(encoding="utf-8")
    source = project / "assets" / "knowledge_models" / "example.md"

    result = CliRunner().invoke(
        main,
        [
            "preview",
            str(source),
            "--project",
            str(project),
            "--config",
            str(config),
        ],
    )

    assert result.exit_code == 0, result.output
    preview = project / "output" / "preview" / "example.html"
    assert preview.is_file()
    assert str(preview.resolve()) in result.output
    html = preview.read_text(encoding="utf-8")
    assert 'edutex-course-theme" content="dark"' in html or "dark" in html
    assert original_config == config.read_text(encoding="utf-8")
    assert not (project / "output" / "document.html").exists()


def test_preview_uses_selected_profile_style(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    config = project / "edutex.config.yaml"
    source = project / "assets" / "knowledge_models" / "example.md"
    config.write_text(
        config.read_text(encoding="utf-8")
        + "\nprofiles:\n  paper:\n    theme:\n      name: default\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        main,
        [
            "preview",
            str(source),
            "--project",
            str(project),
            "--profile",
            "paper",
        ],
    )

    assert result.exit_code == 0, result.output
    preview = project / "output" / "preview" / "example.html"
    html = preview.read_text(encoding="utf-8")
    assert preview.is_file()
    assert html.startswith("<!doctype html>")


def test_preview_rejects_missing_source(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    result = CliRunner().invoke(
        main,
        ["preview", str(project / "missing.md"), "--project", str(project)],
    )

    assert result.exit_code != 0
    assert "does not exist" in result.output.lower() or "not found" in result.output.lower()
