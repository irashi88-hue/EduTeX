"""Test del contratto del comando di authoring validation."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from edutex.core.cli import main


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "AUTHORING_VALIDATION_CONTRACT.md"


def write_source(path: Path, body: str, *, valid_frontmatter: bool = True) -> None:
    if valid_frontmatter:
        frontmatter = (
            "---\n"
            "id: german-a1\n"
            "title: German A1\n"
            "language: de\n"
            "level: A1\n"
            "version: 1.0.0\n"
            "---\n"
        )
    else:
        frontmatter = "---\n id: broken\n"
    path.write_text(frontmatter + body, encoding="utf-8")


def test_documentazione_authoring_validation() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    for marker in (
        "edutex author validate",
        "frontmatter",
        "shortcode",
        '"authoring"',
        "status",
        "metadata",
        "diagnostics",
        "exit code `1`",
        "edutex lint",
    ):
        assert marker in contract, f"Marker mancante: {marker}"
    assert all(
        not line.rstrip("\n").endswith((" ", "\t"))
        for line in contract.splitlines(keepends=True)
    )


def test_author_validate_json_success_includes_metadata(tmp_path: Path) -> None:
    source = tmp_path / "lesson.md"
    write_source(source, "::: rule\nPresent tense\n:::\n")

    result = CliRunner().invoke(
        main,
        ["author", "validate", str(source), "--format", "json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    report = payload["authoring"]
    assert report["status"] == "completed"
    assert report["valid"] is True
    assert Path(report["path"]).resolve() == source.resolve()
    assert report["metadata"] == {
        "id": "german-a1",
        "title": "German A1",
        "language": "de",
        "level": "A1",
        "version": "1.0.0",
    }
    assert report["errors"] == []
    assert report["warnings"] == []
    assert report["diagnostics"] == []


def test_author_validate_json_reports_frontmatter_and_shortcode_errors(tmp_path: Path) -> None:
    source = tmp_path / "broken.md"
    write_source(source, "::: formula.math\n:::\n", valid_frontmatter=False)

    result = CliRunner().invoke(
        main,
        ["author", "validate", str(source), "--format", "json"],
    )

    assert result.exit_code == 1
    report = json.loads(result.output)["authoring"]
    assert report["status"] == "completed"
    assert report["valid"] is False
    assert report["errors"]
    assert report["errors"][0]["code"] == "KM001"
    assert any(item["code"] == "SC101" for item in report["errors"])
    assert "metadata" not in report
    assert report["diagnostics"] == report["errors"] + report["warnings"]


def test_author_validate_text_keeps_lint_separate_and_warnings_non_blocking(tmp_path: Path) -> None:
    source = tmp_path / "warning.md"
    write_source(source, "::: exercise\nWrite a sentence.\n:::\n")

    result = CliRunner().invoke(main, ["author", "validate", str(source)])

    assert result.exit_code == 0, result.output
    assert "SC201" in result.output
    assert "0 errors, 1 warnings." in result.output
