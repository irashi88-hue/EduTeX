"""Integration coverage for the expanded educational shortcode set."""

from __future__ import annotations

import shutil
from html.parser import HTMLParser

import pytest
from pathlib import Path

from click.testing import CliRunner

from edutex.core.cli import main


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SHOWCASE = """---
id: shortcode-showcase
title: "Shortcode Showcase"
language: en
level: A1
version: 1.0.0
author: "EduTeX"
---
# Shortcode Showcase

::: verb
go | andare | sein | gegangen | geht
:::

::: conjugation gehen | andare
ich | gehe | io vado
du | gehst | tu vai
er/sie | geht | lui/lei va
:::

::: formula.math
E = mc^2
:::

::: formula.chem
C_6H_{12}O_6 -> 6CO_2
:::

::: example.comparative
+ Ich gehe morgen ins Kino.
- Ich morgen gehe ins Kino.
:::

::: example.contextual
Anna schreibt einen Brief.
_Anna scrive una lettera._
:::

::: exercise
Complete the sentence.
::: solution
gehen
:::
:::
"""


def make_project(path: Path, output_format: str) -> None:
    shutil.copytree(PROJECT_ROOT / "assets", path / "assets")
    (path / "assets/knowledge_models/showcase.md").write_text(SHOWCASE, encoding="utf-8")
    (path / "edutex.config.yaml").write_text(
        f'''edutex:
  version: "0.1.0"
knowledge:
  model: "assets/knowledge_models/showcase.md"
theme:
  name: "default"
layout:
  name: "default"
build:
  output_format: "{output_format}"
  output_dir: "output"
  output_file: "shortcode_showcase"
extensions:
  enabled: []
logging:
  level: "INFO"
''',
        encoding="utf-8",
    )


def test_expanded_shortcodes_html(tmp_path: Path) -> None:
    make_project(tmp_path, "html")
    result = CliRunner().invoke(main, ["build", "--project", str(tmp_path)])
    assert result.exit_code == 0, result.output

    source = (tmp_path / "output/shortcode_showcase.html").read_text(encoding="utf-8")
    HTMLParser().feed(source)
    assert '<dt>Infinitive</dt>' in source
    assert '<dt>Grammar</dt>' in source
    assert '<th scope="col">Meaning</th>' in source
    assert 'role="math"' in source
    assert 'formula-chem' in source and '<sub>6</sub>' in source
    assert 'example-correct' in source and 'example-incorrect' in source
    assert 'example-translation' in source
    assert '<div class="node solution">' in source
    assert '\\documentclass' not in source


def test_expanded_shortcodes_latex(tmp_path: Path) -> None:
    make_project(tmp_path, "latex")
    result = CliRunner().invoke(main, ["build", "--project", str(tmp_path)])
    assert result.exit_code == 0, result.output

    source = (tmp_path / "output/shortcode_showcase.tex").read_text(encoding="utf-8")
    assert r"\textbf{go}" in source
    assert r"\textbf{Meaning}" in source
    assert r"\ce{" in source
    assert r"\checkmark" in source and r"\times" in source
    assert r"\section*{Solutions}" in source
    assert "**" not in source


def test_parser_rejects_invalid_nesting_and_uppercase() -> None:
    from edutex.knowledge.parser import ParseError, parse

    with pytest.raises(ParseError):
        parse("::: Note\ntext\n:::")
    with pytest.raises(ParseError):
        parse("::: exercise\n::: note\ntext\n:::\n:::")
