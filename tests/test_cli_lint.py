"""Integration tests for the EduTeX lint command."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from edutex.core.cli import main


VALID_SOURCE = """::: formula.math
E = mc^2
:::
"""

WARNING_SOURCE = """::: exercise
Write a sentence.
:::
"""

ERROR_SOURCE = """::: formula.math
:::
"""


def test_lint_text_success(tmp_path: Path) -> None:
    source = tmp_path / "lesson.md"
    source.write_text(VALID_SOURCE, encoding="utf-8")

    result = CliRunner().invoke(main, ["lint", str(source)])

    assert result.exit_code == 0, result.output
    assert f"OK  {source}" in result.output
    assert "No shortcode errors found." in result.output


def test_lint_warning_is_non_blocking(tmp_path: Path) -> None:
    source = tmp_path / "lesson.md"
    source.write_text(WARNING_SOURCE, encoding="utf-8")

    result = CliRunner().invoke(main, ["lint", str(source), "--format", "text"])

    assert result.exit_code == 0, result.output
    assert "[SC201]" in result.output
    assert "0 errors, 1 warnings." in result.output


def test_lint_error_returns_non_zero(tmp_path: Path) -> None:
    source = tmp_path / "lesson.md"
    source.write_text(ERROR_SOURCE, encoding="utf-8")

    result = CliRunner().invoke(main, ["lint", str(source)])

    assert result.exit_code == 1
    assert "[SC101]" in result.output


def test_lint_json_is_machine_readable(tmp_path: Path) -> None:
    source = tmp_path / "lesson.md"
    source.write_text(ERROR_SOURCE, encoding="utf-8")

    result = CliRunner().invoke(main, ["lint", str(source), "--format", "json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["path"] == str(source)
    assert payload["valid"] is False
    assert payload["errors"][0]["code"] == "SC101"
