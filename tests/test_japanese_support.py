"""Integration coverage for the initial Japanese language path."""

from __future__ import annotations

import json
import shutil
from html.parser import HTMLParser
from pathlib import Path

from click.testing import CliRunner

from edutex.core.cli import main


ROOT = Path(__file__).resolve().parents[1]

JAPANESE_SOURCE = """---
id: ja-a1-greetings
title: "あいさつと自己紹介"
language: ja
level: A1
version: 1.0.0
author: EduTeX
---

# あいさつと自己紹介

::: rule
title: 基本のあいさつ
おはようございます。こんにちは。こんばんは。
:::

::: example.simple
title: はじめまして
はじめまして。ルカです。どうぞよろしくお願いします。
:::

::: vocab
word: こんにちは
translation: hello
gender: —
plural: —
example: こんにちは、ルカさん。
:::

::: exercise
title: 自己紹介
「私は＿＿＿です。」を完成させましょう。
::: solution
ルカ
:::
:::
"""


def make_project(path: Path, output_format: str = "html") -> Path:
    shutil.copytree(ROOT / "assets", path / "assets")
    model = path / "assets" / "knowledge_models" / "japanese.md"
    model.write_text(JAPANESE_SOURCE, encoding="utf-8")
    config = "\n".join([
        "edutex:", '  version: "0.3.0"', "knowledge:",
        '  model: "assets/knowledge_models/japanese.md"', "theme:",
        '  name: "default"', "layout:", '  name: "default"', "build:",
        f'  output_format: "{output_format}"', '  output_dir: "output"',
        '  output_file: "japanese"', "extensions:", "  enabled: []", "logging:",
        '  level: "INFO"', "",
    ])
    (path / "edutex.config.yaml").write_text(config, encoding="utf-8")
    return path


def test_init_accepts_ja_and_writes_japanese_starter(tmp_path: Path) -> None:
    project = tmp_path / "ja-project"
    result = CliRunner().invoke(main, ["init", str(project), "--theme", "default", "--language", "ja"])
    assert result.exit_code == 0, result.output
    source = (project / "assets" / "knowledge_models" / "example.md").read_text(encoding="utf-8")
    assert "language: ja" in source
    assert "あいさつと自己紹介" in source
    assert "おはようございます" in source


def test_japanese_html_has_language_labels_and_unicode_content(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    result = CliRunner().invoke(main, ["build", "--project", str(project), "--lint"])
    assert result.exit_code == 0, result.output
    source = (project / "output" / "japanese.html").read_text(encoding="utf-8")
    HTMLParser().feed(source)
    assert '<html lang="ja">' in source
    assert "規則" in source and "例" in source and "練習" in source and "解答" in source
    assert "目次" in source and "コンテンツへ移動" in source
    assert "文書の内容" in source
    assert "あいさつと自己紹介" in source
    assert "おはようございます" in source
    assert "こんにちは" in source and "ルカ" in source


def test_japanese_latex_uses_unicode_cjk_preamble(tmp_path: Path) -> None:
    project = make_project(tmp_path, "latex")
    result = CliRunner().invoke(main, ["build", "--project", str(project), "--lint"])
    assert result.exit_code == 0, result.output
    source = (project / "output" / "japanese.tex").read_text(encoding="utf-8")
    assert "\\usepackage{fontspec}" in source
    assert "\\usepackage{xeCJK}" in source
    assert "\\usepackage[utf8]{inputenc}" not in source
    assert "あいさつと自己紹介" in source
    assert "こんにちは" in source and "解答" in source


def test_japanese_lint_json_preserves_valid_contract(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    model = project / "assets" / "knowledge_models" / "japanese.md"
    result = CliRunner().invoke(main, ["lint", str(model), "--format", "json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["valid"] is True
    assert payload["errors"] == []
