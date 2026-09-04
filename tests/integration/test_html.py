"""Integration tests for the standalone HTML Build backend."""

from __future__ import annotations

import re
import shutil
from html.parser import HTMLParser
from pathlib import Path

from click.testing import CliRunner

from edutex.core.cli import main


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def make_project(path: Path, *, extensions: list[str]) -> None:
    shutil.copytree(PROJECT_ROOT / "assets", path / "assets")
    enabled = "[" + ", ".join(extensions) + "]"
    (path / "edutex.config.yaml").write_text(
        f'''edutex:
  version: "0.1.0"
knowledge:
  model: "assets/knowledge_models/example.md"
theme:
  name: "default"
layout:
  name: "default"
build:
  output_format: "html"
  output_dir: "output"
  output_file: "html_document"
extensions:
  enabled: {enabled}
logging:
  level: "INFO"
''',
        encoding="utf-8",
    )


def test_html_build_is_self_contained_and_parsable(tmp_path: Path) -> None:
    make_project(tmp_path, extensions=["reading_tip"])
    result = CliRunner().invoke(main, ["build", "--project", str(tmp_path)])

    assert result.exit_code == 0, result.output
    output = tmp_path / "output" / "html_document.html"
    assert output.is_file()
    source = output.read_text(encoding="utf-8")
    HTMLParser().feed(source)

    ids = re.findall(r'\bid="([^"]+)"', source)
    assert len(ids) == len(set(ids))
    for labelled_by in re.findall(r'aria-labelledby="([^"]+)"', source):
        assert f'id="{labelled_by}"' in source

    assert source.startswith("<!doctype html>")
    assert '<meta name="generator" content="EduTeX">' in source
    assert "<strong>parlo</strong>" in source
    assert 'class="blank"' in source
    assert "Reading tip" in source
    assert "\\\\documentclass" not in source
    assert "<style>" in source
    assert source.index('<header class="masthead">') < source.index('<nav class="toc"')
    assert source.index('<nav class="toc"') < source.index('<article id="content"')


def test_html_build_without_extension_has_no_contribution(tmp_path: Path) -> None:
    make_project(tmp_path, extensions=[])
    result = CliRunner().invoke(main, ["build", "--project", str(tmp_path)])

    assert result.exit_code == 0, result.output
    source = (tmp_path / "output" / "html_document.html").read_text(encoding="utf-8")
    assert "Reading tip" not in source
