"""Tests for actionable configuration, front matter, and parser diagnostics."""

from pathlib import Path

import pytest

from edutex.configuration.loader import load_config
from edutex.core.errors import ConfigurationError, KnowledgeError
from edutex.knowledge.loader import load_knowledge_model
from edutex.knowledge.parser import ParseError, parse


def test_config_validation_lists_field_locations(tmp_path: Path) -> None:
    path = tmp_path / "edutex.config.yaml"
    path.write_text(
        """edutex:\n  version: \"0.1.0\"\nknowledge:\n  model: \"\"\ntheme:\n  name: default\nlayout:\n  name: default\n""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError) as error:
        load_config(path)

    message = str(error.value)
    assert "Configuration validation failed" in message
    assert "knowledge.model" in message
    assert "must not be empty" in message


def test_front_matter_missing_field_explains_fix(tmp_path: Path) -> None:
    path = tmp_path / "lesson.md"
    path.write_text("---\nid: lesson\ntitle: Lesson\n---\n# Lesson\n", encoding="utf-8")

    with pytest.raises(KnowledgeError) as error:
        load_knowledge_model(path)

    message = str(error.value)
    assert "missing required front matter fields" in message
    assert "'language'" in message
    assert "'level'" in message
    assert "'version'" in message


def test_parser_reports_unexpected_closing_delimiter() -> None:
    with pytest.raises(ParseError, match=r"Line 2: Unexpected closing delimiter"):
        parse("Text\n:::\n")


def test_parser_reports_unclosed_shortcode_line() -> None:
    with pytest.raises(ParseError, match=r"Line 1: Unclosed shortcode 'note'"):
        parse("::: note\nA note without a closing delimiter.\n")
