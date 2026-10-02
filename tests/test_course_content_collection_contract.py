"""Test del contratto della raccolta dei contenuti del corso."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from edutex.course import CourseBuildError, load_course_content
from edutex.core.cli import main


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "COURSE_CONTENT_COLLECTION_CONTRACT.md"


def make_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    result = CliRunner().invoke(main, ["init", str(project), "--theme", "dark"])
    assert result.exit_code == 0, result.output
    (project / "lessons").mkdir()
    (project / "lessons" / "grammar.md").write_text(
        "---\n"
        "id: grammar\n"
        "title: Grammar\n"
        "language: de\n"
        "level: A1\n"
        "version: 1.0.0\n"
        "---\n"
        "::: rule\n"
        "Present tense\n"
        ":::\n",
        encoding="utf-8",
    )
    (project / "lessons" / "vocabulary.md").write_text(
        "---\n"
        "id: vocabulary\n"
        "title: Vocabulary\n"
        "language: de\n"
        "level: A1\n"
        "version: 1.0.0\n"
        "---\n"
        "::: vocab Haus | house\n"
        "Haus\n"
        ":::\n",
        encoding="utf-8",
    )
    (project / "course.yaml").write_text(
        "course:\n"
        "  id: german-a1\n"
        "  title: German A1\n"
        "  modules:\n"
        "    - id: grammar\n"
        "      title: Grammar\n"
        "      lessons:\n"
        "        - id: grammar\n"
        "          title: Grammar\n"
        "          source: lessons/grammar.md\n"
        "    - id: vocabulary\n"
        "      title: Vocabulary\n"
        "      lessons:\n"
        "        - id: vocabulary\n"
        "          title: Vocabulary\n"
        "          source: lessons/vocabulary.md\n",
        encoding="utf-8",
    )
    return project


def test_documentazione_course_content_collection() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    for marker in (
        "course.yaml",
        "edutex.config.yaml",
        "CourseContentCollection",
        "CourseContentEntry",
        "load_course_content",
        "source_path",
        "KeyError",
        "CourseBuildError",
        "copie distaccate",
    ):
        assert marker in contract, f"Marker mancante: {marker}"
    assert all(
        not line.rstrip("\n").endswith((" ", "\t"))
        for line in contract.splitlines(keepends=True)
    )


def test_collection_processes_all_lessons_in_manifest_order(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    collection = load_course_content(project / "course.yaml", project)

    assert collection.ids == ("grammar", "vocabulary")
    assert len(collection) == 2
    assert [entry.lesson_id for entry in collection.all()] == [
        "grammar",
        "vocabulary",
    ]
    assert collection["grammar"].meta.id == "grammar"
    assert collection["vocabulary"].content.nodes()[0].node_type == "vocab"
    assert collection["grammar"].source_path.is_absolute()
    assert collection["grammar"].source_path.is_file()


def test_collection_returns_detached_entries(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    collection = load_course_content(project / "course.yaml", project)

    entry = collection["grammar"]
    entry.content.items[0].body = "changed"
    entry.meta.title = "changed"

    fresh = collection["grammar"]
    assert fresh.content.items[0].body == "Present tense"
    assert fresh.meta.title == "Grammar"
    assert collection.get("missing") is None
    with pytest.raises(KeyError):
        collection["missing"]


def test_collection_reports_invalid_course_or_lesson(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    (project / "course.yaml").write_text(
        (project / "course.yaml").read_text(encoding="utf-8").replace(
            "lessons/vocabulary.md", "lessons/missing.md"
        ),
        encoding="utf-8",
    )

    with pytest.raises(CourseBuildError, match="Course manifest is invalid"):
        load_course_content(project / "course.yaml", project)
