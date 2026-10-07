
"Contract tests for the bundled theme used by zero-configuration builds."

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from edutex.configuration.loader import load_config
from edutex.core.cli import main


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _make_project(tmp_path: Path, output_format: str, *, theme_name: str | None = None) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    shutil.copytree(PROJECT_ROOT / "assets", project / "assets")
    shutil.rmtree(project / "assets" / "themes")
    config = f'''edutex:
  version: "1.0.0"
knowledge:
  model: "assets/knowledge_models/example.md"
'''
    if theme_name is not None:
        config += f'''theme:
  name: "{theme_name}"
'''
    config += f'''layout:
  name: "default"
build:
  output_format: "{output_format}"
  output_dir: "output"
  output_file: "zero_config"
'''
    (project / "edutex.config.yaml").write_text(config, encoding="utf-8")
    return project


@pytest.mark.parametrize(("output_format", "extension"), [("html", "html"), ("latex", "tex")])
def test_default_theme_builds_without_project_theme(
    tmp_path: Path, output_format: str, extension: str
) -> None:
    project = _make_project(tmp_path, output_format)
    config = load_config(project / "edutex.config.yaml")
    assert config.theme.name == "default"
    assert "name" not in config.theme.model_fields_set
    assert not (project / "assets" / "themes").exists()

    result = CliRunner().invoke(main, ["build", "--project", str(project)])
    assert result.exit_code == 0, result.output

    output = project / "output" / f"zero_config.{extension}"
    assert output.is_file()
    rendered = output.read_text(encoding="utf-8")
    assert "Introduction" in rendered
    if output_format == "latex":
        assert r"\documentclass" in rendered
    else:
        assert "<html" in rendered


def test_missing_explicit_theme_does_not_fall_back(tmp_path: Path) -> None:
    project = _make_project(tmp_path, "html", theme_name="custom-missing")
    result = CliRunner().invoke(main, ["build", "--project", str(project)])

    assert result.exit_code != 0
    assert "Theme asset not found" in result.output
    assert not (project / "output" / "zero_config.html").exists()


def test_invalid_explicit_theme_does_not_fall_back(tmp_path: Path) -> None:
    project = _make_project(tmp_path, "html", theme_name="custom-invalid")
    theme_path = project / "assets" / "themes" / "custom-invalid" / "theme.yaml"
    theme_path.parent.mkdir(parents=True)
    theme_path.write_text("id: custom-invalid\nstyles: [\n", encoding="utf-8")
    result = CliRunner().invoke(main, ["build", "--project", str(project)])

    assert result.exit_code != 0
    assert not (project / "output" / "zero_config.html").exists()


def test_inspection_reports_bundled_theme_without_project_theme(tmp_path: Path) -> None:
    from edutex.core.cli import _inspect_project

    project = _make_project(tmp_path, "html")
    report = _inspect_project(project / "edutex.config.yaml", project)["inspection"]

    assert report["assets"]["theme"] == {
        "path": "package:edutex.theme/default_theme.yaml",
        "exists": True,
    }
    assert all(entity["type"] != "theme" for entity in report["runtime"]["registry"]["entities"])


def test_bundled_default_theme_is_packaged_and_valid() -> None:
    import tomllib

    package_theme = PROJECT_ROOT / "src" / "edutex" / "theme" / "default_theme.yaml"
    assert package_theme.is_file()
    theme = yaml.safe_load(package_theme.read_text(encoding="utf-8"))
    assert theme["id"] == "default"
    assert "_default" in theme["styles"]

    metadata = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert "theme/*.yaml" in metadata["tool"]["setuptools"]["package-data"]["edutex"]
