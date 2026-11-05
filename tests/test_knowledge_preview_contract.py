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

def test_build_validate_and_preview_register_operation_scope(tmp_path: Path, monkeypatch) -> None:
    import edutex.core.cli as cli_module

    project = make_project(tmp_path)
    original = project / "assets" / "knowledge_models" / "example.md"
    selected_preview = original.with_name("preview-only.md")
    selected_preview.write_text(original.read_text(encoding="utf-8"), encoding="utf-8")

    registered = []
    actual_register = cli_module._register_project_assets

    def record_registration(config, project_root):
        registry = actual_register(config, project_root)
        registered.append(
            {Path(entity.source_path).resolve() for entity in registry.get_all()}
        )
        return registry

    monkeypatch.setattr(cli_module, "_register_project_assets", record_registration)

    build = CliRunner().invoke(main, ["build", "--project", str(project)])
    assert build.exit_code == 0, build.output

    validate = CliRunner().invoke(main, ["validate", "--project", str(project)])
    assert validate.exit_code == 0, validate.output

    preview = CliRunner().invoke(
        main,
        ["preview", str(selected_preview), "--project", str(project)],
    )
    assert preview.exit_code == 0, preview.output

    assert len(registered) == 3
    build_scope, validate_scope, preview_scope = registered
    assert build_scope == validate_scope
    assert original.resolve() in build_scope
    assert selected_preview.resolve() not in build_scope

    support = build_scope - {original.resolve()}
    assert {path.name for path in support} == {"theme.yaml", "layout.yaml"}
    assert preview_scope == support | {selected_preview.resolve()}
    assert original.resolve() not in preview_scope
