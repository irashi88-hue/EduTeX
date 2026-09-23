"""Course manifest validation and index generation tests."""

from __future__ import annotations

import json
import re
import shutil
from html.parser import HTMLParser
from pathlib import Path

from click.testing import CliRunner

from edutex.core.cli import main


PROJECT_ROOT = Path(__file__).resolve().parents[1]

MANIFEST = """id: german-a1
title: German A1
language: de
level: A1
version: 1.0.0
author: EduTeX
description: Beginner course
modules:
  - id: module-01
    title: Greetings
    lessons:
      - id: lesson-01
        title: Hello
        source: lessons/hello.md
        duration_minutes: 20
        objectives: [Introduce yourself]
"""


GOODBYE_LESSON = """---
id: goodbye
title: Goodbye
language: en
level: A1
version: 1.0.0
author: Tester
---
# Goodbye

Second lesson.
"""


def make_project(path: Path) -> None:
    shutil.copytree(PROJECT_ROOT / "assets", path / "assets")
    (path / "lessons").mkdir(parents=True)
    (path / "lessons/hello.md").write_text(
        "---\nid: hello\ntitle: Hello\nlanguage: en\nlevel: A1\nversion: 1.0.0\nauthor: Tester\n---\n# Hello\n",
        encoding="utf-8",
    )
    (path / "edutex.config.yaml").write_text(
        """edutex:
  version: "0.3.0"
knowledge:
  model: "assets/knowledge_models/example.md"
theme:
  name: "default"
layout:
  name: "default"
build:
  output_format: "html"
  output_dir: "output"
  output_file: "document"
extensions:
  enabled: []
logging:
  level: "INFO"
""",
        encoding="utf-8",
    )
    (path / "course.yaml").write_text(MANIFEST, encoding="utf-8")


def test_course_validate_json(tmp_path: Path) -> None:
    make_project(tmp_path)
    result = CliRunner().invoke(main, ["course", "validate", "--project", str(tmp_path), "--format", "json"])
    assert result.exit_code == 0, result.output
    assert '"valid": true' in result.output
    assert '"lessons": 1' in result.output


def test_course_html_has_keyboard_skip_link_and_main_landmark(tmp_path: Path) -> None:
    make_project(tmp_path)
    result = CliRunner().invoke(
        main, ["course", "build", "--project", str(tmp_path), "--format", "html"]
    )
    assert result.exit_code == 0, result.output
    index = (tmp_path / "output/course.html").read_text(encoding="utf-8")
    lesson = (tmp_path / "output/lessons/lesson-01.html").read_text(encoding="utf-8")
    assert '<a class="skip-link" href="#course-content">Skip to course content</a>' in index
    assert '<main id="course-content" tabindex="-1" aria-labelledby="course-title">' in index
    assert '<h1 id="course-title">German A1</h1>' in index
    assert '<a class="skip-link" href="#lesson-content">Skip to lesson content</a>' in lesson
    assert '<main id="lesson-content" tabindex="-1" aria-label="Lesson content">' in lesson


def test_course_lesson_navigation_has_explicit_link_labels(tmp_path: Path) -> None:
    make_project(tmp_path)
    (tmp_path / "lessons/goodbye.md").write_text(GOODBYE_LESSON, encoding="utf-8")
    manifest = MANIFEST.replace(
        "        objectives: [Introduce yourself]\n",
        "        objectives: [Introduce yourself]\n"
        "      - id: lesson-02\n"
        "        title: Goodbye\n"
        "        source: lessons/goodbye.md\n",
    )
    (tmp_path / "course.yaml").write_text(manifest, encoding="utf-8")
    result = CliRunner().invoke(
        main, ["course", "build", "--project", str(tmp_path), "--format", "html"]
    )
    assert result.exit_code == 0, result.output
    first = (tmp_path / "output/lessons/lesson-01.html").read_text(encoding="utf-8")
    second = (tmp_path / "output/lessons/lesson-02.html").read_text(encoding="utf-8")
    assert 'aria-label="Next lesson: Goodbye"' in first
    assert 'aria-label="Previous lesson: Hello"' in second
    assert 'aria-label="Course index"' in first
    assert 'aria-disabled="true"' in first


def test_course_build_html_contains_navigation(tmp_path: Path) -> None:
    make_project(tmp_path)
    result = CliRunner().invoke(main, ["course", "build", "--project", str(tmp_path), "--format", "html"])
    assert result.exit_code == 0, result.output
    source = (tmp_path / "output/course.html").read_text(encoding="utf-8")
    assert '<meta name="generator" content="EduTeX Course Management">' in source
    assert "German A1" in source
    assert "Greetings" in source
    assert "Hello" in source
    assert 'href="lessons/lesson-01.html"' in source


def test_course_build_latex_contains_roadmap(tmp_path: Path) -> None:
    make_project(tmp_path)
    result = CliRunner().invoke(main, ["course", "build", "--project", str(tmp_path), "--format", "latex"])
    assert result.exit_code == 0, result.output
    source = (tmp_path / "output/course.tex").read_text(encoding="utf-8")
    assert "\\section{Greetings}" in source
    assert "Hello" in source
    assert "lessons/hello.md" in source


def test_course_build_latex_enables_pdf_text_accessibility(tmp_path: Path) -> None:
    make_project(tmp_path)
    result = CliRunner().invoke(
        main, ["course", "build", "--project", str(tmp_path), "--format", "latex"]
    )
    assert result.exit_code == 0, result.output
    source = (tmp_path / "output/course.tex").read_text(encoding="utf-8")
    assert r"\usepackage{cmap}" in source
    assert r"\ifdefined\pdfgentounicode" in source
    assert r"\input glyphtounicode" in source
    assert r"\pdfgentounicode=1" in source
    assert "unicode=true" in source
    assert "bookmarks=true" in source
    assert "bookmarksopen=true" in source
    assert "bookmarksnumbered=true" in source


def test_course_build_latex_sets_pdf_metadata_and_language(tmp_path: Path) -> None:
    make_project(tmp_path)
    result = CliRunner().invoke(
        main, ["course", "build", "--project", str(tmp_path), "--format", "latex"]
    )
    assert result.exit_code == 0, result.output
    source = (tmp_path / "output/course.tex").read_text(encoding="utf-8")
    assert "pdftitle={German A1}" in source
    assert "pdfauthor={EduTeX}" in source
    assert "pdfsubject={Beginner course}" in source
    assert "pdflang={de-DE}" in source


def test_course_build_latex_uses_metadata_fallbacks(tmp_path: Path) -> None:
    make_project(tmp_path)
    manifest = (tmp_path / "course.yaml").read_text(encoding="utf-8")
    manifest = manifest.replace("author: EduTeX\n", "author: \n").replace(
        "description: Beginner course\n", "description: \n"
    )
    (tmp_path / "course.yaml").write_text(manifest, encoding="utf-8")
    result = CliRunner().invoke(
        main, ["course", "build", "--project", str(tmp_path), "--format", "latex"]
    )
    assert result.exit_code == 0, result.output
    source = (tmp_path / "output/course.tex").read_text(encoding="utf-8")
    assert "pdfauthor={EduTeX}" in source
    assert "pdfsubject={EduTeX course roadmap}" in source


def test_course_validate_json_reports_structured_source_diagnostic(tmp_path: Path) -> None:
    make_project(tmp_path)
    (tmp_path / "lessons/hello.md").write_text("# Hello\n", encoding="utf-8")
    result = CliRunner().invoke(
        main,
        ["course", "validate", "--project", str(tmp_path), "--format", "json"],
    )
    assert result.exit_code != 0
    payload = json.loads(result.output)
    diagnostic = payload["diagnostics"][0]
    assert diagnostic["code"] == "COURSE_SOURCE_FRONTMATTER_MISSING"
    assert diagnostic["severity"] == "error"
    assert diagnostic["field"] == "course.modules[1].lessons[1].source"
    assert diagnostic["path"] == "lessons/hello.md"


def test_course_validate_json_reports_warnings_without_fake_fields(tmp_path: Path) -> None:
    make_project(tmp_path)
    manifest = (tmp_path / "course.yaml").read_text(encoding="utf-8")
    (tmp_path / "course.yaml").write_text(
        manifest.replace("        duration_minutes: 20\n", ""),
        encoding="utf-8",
    )
    result = CliRunner().invoke(
        main,
        ["course", "validate", "--project", str(tmp_path), "--format", "json"],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    warning = next(item for item in payload["diagnostics"] if item["severity"] == "warning")
    assert warning["code"] == "COURSE_DURATION_UNDECLARED"
    assert "field" not in warning


def test_course_validate_json_reports_unknown_prerequisite_code(tmp_path: Path) -> None:
    make_project(tmp_path)
    manifest = MANIFEST.replace(
        "        objectives: [Introduce yourself]\n",
        "        objectives: [Introduce yourself]\n        prerequisites: [missing-lesson]\n",
    )
    (tmp_path / "course.yaml").write_text(manifest, encoding="utf-8")
    result = CliRunner().invoke(
        main,
        ["course", "validate", "--project", str(tmp_path), "--format", "json"],
    )
    assert result.exit_code != 0
    payload = json.loads(result.output)
    diagnostic = next(item for item in payload["diagnostics"] if "prerequisite" in item["message"].lower())
    assert diagnostic["code"] == "COURSE_PREREQUISITE_UNKNOWN"
    assert diagnostic["field"] == "course.modules[1].lessons[1].prerequisites"


def test_course_validate_json_keeps_legacy_errors_and_diagnostics(tmp_path: Path) -> None:
    make_project(tmp_path)
    (tmp_path / "lessons/hello.md").write_text("# Hello\n", encoding="utf-8")
    result = CliRunner().invoke(
        main,
        ["course", "validate", "--project", str(tmp_path), "--format", "json"],
    )
    payload = json.loads(result.output)
    assert payload["valid"] is False
    assert payload["errors"]
    assert payload["diagnostics"]
    assert payload["errors"][0] == payload["diagnostics"][0]["message"]


def test_course_validate_rejects_lesson_without_frontmatter(tmp_path: Path) -> None:
    make_project(tmp_path)
    (tmp_path / "lessons/hello.md").write_text("# Hello\n", encoding="utf-8")
    result = CliRunner().invoke(main, ["course", "validate", "--project", str(tmp_path)])
    assert result.exit_code != 0
    assert "not a valid Knowledge Model" in result.output
    assert "front matter" in result.output


def test_course_validate_rejects_lesson_with_incomplete_frontmatter(tmp_path: Path) -> None:
    make_project(tmp_path)
    (tmp_path / "lessons/hello.md").write_text(
        "---\nid: hello\ntitle: Hello\n---\n# Hello\n",
        encoding="utf-8",
    )
    result = CliRunner().invoke(main, ["course", "validate", "--project", str(tmp_path)])
    assert result.exit_code != 0
    assert "not a valid Knowledge Model" in result.output
    assert "missing required front matter fields" in result.output


def test_course_validate_rejects_missing_source(tmp_path: Path) -> None:
    (tmp_path / "course.yaml").write_text(MANIFEST.replace("lessons/hello.md", "lessons/missing.md"), encoding="utf-8")
    result = CliRunner().invoke(main, ["course", "validate", "--project", str(tmp_path)])
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_init_materializes_course_manifest(tmp_path: Path) -> None:
    project = tmp_path / "new-project"
    result = CliRunner().invoke(main, ["init", str(project)])
    assert result.exit_code == 0, result.output
    assert (project / "course.yaml").is_file()


def test_course_build_html_generates_lesson_pages_and_navigation(tmp_path: Path) -> None:
    make_project(tmp_path)
    (tmp_path / "lessons/goodbye.md").write_text(GOODBYE_LESSON, encoding="utf-8")
    (tmp_path / "course.yaml").write_text(
        MANIFEST.replace(
            "source: lessons/hello.md",
            "source: lessons/hello.md",
        ).replace(
            "        duration_minutes: 20\n        objectives: [Introduce yourself]\n",
            "        duration_minutes: 20\n        objectives: [Introduce yourself]\n      - id: lesson-02\n        title: Goodbye\n        source: lessons/goodbye.md\n",
        ),
        encoding="utf-8",
    )
    result = CliRunner().invoke(
        main,
        ["course", "build", "--project", str(tmp_path), "--format", "html"],
    )
    assert result.exit_code == 0, result.output
    index = (tmp_path / "output/course.html").read_text(encoding="utf-8")
    first = (tmp_path / "output/lessons/lesson-01.html").read_text(encoding="utf-8")
    second = (tmp_path / "output/lessons/lesson-02.html").read_text(encoding="utf-8")
    assert (tmp_path / "output/lessons/lesson-01.html").is_file()
    assert (tmp_path / "output/lessons/lesson-02.html").is_file()
    assert 'href="lessons/lesson-01.html"' in index
    assert 'href="lessons/lesson-02.html"' in index
    assert 'href="../course.html"' in first
    assert 'href="lesson-02.html"' in first
    assert 'href="lesson-01.html"' in second
    assert 'Course navigation' in first
    assert "# Hello" not in first


def test_course_build_html_reports_lesson_build_failure(tmp_path: Path) -> None:
    make_project(tmp_path)
    (tmp_path / "course.yaml").write_text(
        MANIFEST.replace("lessons/hello.md", "lessons/missing.md"),
        encoding="utf-8",
    )
    result = CliRunner().invoke(
        main,
        ["course", "build", "--project", str(tmp_path), "--format", "html"],
    )
    assert result.exit_code != 0
    assert "Course manifest is invalid" in result.output
    assert "does not exist" in result.output



def test_course_validate_accepts_prerequisites_and_reports_dependency_count(tmp_path: Path) -> None:
    make_project(tmp_path)
    (tmp_path / "lessons/goodbye.md").write_text(
        "---\nid: goodbye\ntitle: Goodbye\nlanguage: en\nlevel: A1\nversion: 1.0.0\nauthor: Tester\n---\n# Goodbye\n",
        encoding="utf-8",
    )
    manifest = MANIFEST.replace(
        "        objectives: [Introduce yourself]\n",
        "        objectives: [Introduce yourself]\n      - id: lesson-02\n        title: Goodbye\n        source: lessons/goodbye.md\n        prerequisites: [lesson-01]\n",
    )
    (tmp_path / "course.yaml").write_text(manifest, encoding="utf-8")
    result = CliRunner().invoke(
        main,
        ["course", "validate", "--project", str(tmp_path), "--format", "json"],
    )
    assert result.exit_code == 0, result.output
    assert '"dependencies": 1' in result.output


def test_course_validate_rejects_unknown_prerequisite(tmp_path: Path) -> None:
    make_project(tmp_path)
    manifest = MANIFEST.replace(
        "        objectives: [Introduce yourself]\n",
        "        objectives: [Introduce yourself]\n        prerequisites: [missing-lesson]\n",
    )
    (tmp_path / "course.yaml").write_text(manifest, encoding="utf-8")
    result = CliRunner().invoke(main, ["course", "validate", "--project", str(tmp_path)])
    assert result.exit_code != 0
    assert "Unknown prerequisite 'missing-lesson'" in result.output


def test_course_validate_rejects_prerequisite_cycle(tmp_path: Path) -> None:
    make_project(tmp_path)
    (tmp_path / "lessons/goodbye.md").write_text(
        "---\nid: goodbye\ntitle: Goodbye\nlanguage: en\nlevel: A1\nversion: 1.0.0\nauthor: Tester\n---\n# Goodbye\n",
        encoding="utf-8",
    )
    manifest = MANIFEST.replace(
        "        objectives: [Introduce yourself]\n",
        "        objectives: [Introduce yourself]\n        prerequisites: [lesson-02]\n      - id: lesson-02\n        title: Goodbye\n        source: lessons/goodbye.md\n        prerequisites: [lesson-01]\n",
    )
    (tmp_path / "course.yaml").write_text(manifest, encoding="utf-8")
    result = CliRunner().invoke(main, ["course", "validate", "--project", str(tmp_path)])
    assert result.exit_code != 0
    assert "Prerequisite cycle detected" in result.output


def test_course_index_contains_dependency_gate_and_progress_script(tmp_path: Path) -> None:
    make_project(tmp_path)
    (tmp_path / "lessons/goodbye.md").write_text(GOODBYE_LESSON, encoding="utf-8")
    manifest = MANIFEST.replace(
        "        objectives: [Introduce yourself]\n",
        "        objectives: [Introduce yourself]\n      - id: lesson-02\n        title: Goodbye\n        source: lessons/goodbye.md\n        prerequisites: [lesson-01]\n",
    )
    (tmp_path / "course.yaml").write_text(manifest, encoding="utf-8")
    result = CliRunner().invoke(
        main,
        ["course", "build", "--project", str(tmp_path), "--format", "html"],
    )
    assert result.exit_code == 0, result.output
    index = (tmp_path / "output/course.html").read_text(encoding="utf-8")
    lesson = (tmp_path / "output/lessons/lesson-01.html").read_text(encoding="utf-8")
    assert 'data-prerequisites="[&quot;lesson-01&quot;]"' in index
    assert "localStorage" in index
    assert "edutex:course:german-a1:completed" in index
    assert "data-course-complete" in lesson
    assert "Mark lesson complete" in lesson
    assert 'const storageKey = "edutex:course:german-a1:completed";' in index
    assert 'JSON.parse(localStorage.getItem(storageKey) || "[]")' in index
    assert 'localStorage.setItem(storageKey, JSON.stringify([...completed]))' in index
    assert 'const missing = prerequisites.filter((item) => !completed.has(item));' in index
    assert 'if (prerequisites.some((item) => !completed.has(item))) event.preventDefault();' in index
    assert "completed.add(lessonId);" in index
    assert "completed.delete(lessonId);" in index
    assert 'data-course-progress-bar' in index


def test_course_build_removes_stale_lesson_pages(tmp_path: Path) -> None:
    make_project(tmp_path)
    (tmp_path / "lessons/goodbye.md").write_text(GOODBYE_LESSON, encoding="utf-8")
    two_lessons = MANIFEST.replace("language: de\n", "language: it\n").replace(
        "        objectives: [Introduce yourself]\n",
        "        objectives: [Introduce yourself]\n"
        "      - id: lesson-02\n"
        "        title: Goodbye\n"
        "        source: lessons/goodbye.md\n",
    )
    (tmp_path / "course.yaml").write_text(two_lessons, encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(
        main, ["course", "build", "--project", str(tmp_path), "--format", "html"]
    )
    assert result.exit_code == 0, result.output
    stale = tmp_path / "output/lessons/lesson-02.html"
    assert stale.is_file()
    stale_source = stale.read_text(encoding="utf-8")
    assert 'class="course-lesson-nav"' in stale_source
    assert 'aria-label="Navigazione del corso"' in stale_source

    manual = tmp_path / "output/lessons/manual.html"
    manual.write_text(
        '<meta name="generator" content="EduTeX"><html>Manual</html>',
        encoding="utf-8",
    )
    foreign = tmp_path / "output/lessons/foreign.html"
    foreign.write_text(
        '<nav class="course-lesson-nav">Foreign</nav>',
        encoding="utf-8",
    )
    plain = tmp_path / "output/lessons/notes.html"
    plain.write_text("<html>Unrelated</html>", encoding="utf-8")

    (tmp_path / "course.yaml").write_text(MANIFEST, encoding="utf-8")
    result = runner.invoke(
        main, ["course", "build", "--project", str(tmp_path), "--format", "html"]
    )
    assert result.exit_code == 0, result.output
    assert not stale.exists()
    assert (tmp_path / "output/lessons/lesson-01.html").is_file()
    assert manual.is_file()
    assert foreign.is_file()
    assert plain.is_file()


def test_course_metadata_is_optional_for_legacy_manifest(tmp_path: Path) -> None:
    make_project(tmp_path)
    result = CliRunner().invoke(
        main,
        ["course", "validate", "--project", str(tmp_path), "--format", "json"],
    )
    assert result.exit_code == 0, result.output
    assert '"objectives": 0' in result.output
    assert '"competencies": 0' in result.output
    assert '"duration_minutes": 20' in result.output


def test_course_metadata_and_declared_duration_are_rendered(tmp_path: Path) -> None:
    make_project(tmp_path)
    manifest = MANIFEST.replace(
        "description: Beginner course\n",
        "description: Beginner course\n"
        "objectives:\n"
        "  - Introduce yourself confidently\n"
        "  - Ask simple questions\n"
        "competencies:\n"
        "  - Speaking\n"
        "  - Listening\n"
        "estimated_duration_minutes: 90\n",
    )
    (tmp_path / "course.yaml").write_text(manifest, encoding="utf-8")
    result = CliRunner().invoke(
        main,
        ["course", "build", "--project", str(tmp_path), "--format", "html"],
    )
    assert result.exit_code == 0, result.output
    source = (tmp_path / "output/course.html").read_text(encoding="utf-8")
    assert "Course goals" in source
    assert "Introduce yourself confidently" in source
    assert "Skills you will build" in source
    assert "Speaking" in source
    assert "90 min remaining" in source
    assert "data-course-progress-bar" in source
    assert "totalMinutes = 90" in source


def test_course_metadata_is_reported_in_json(tmp_path: Path) -> None:
    make_project(tmp_path)
    manifest = MANIFEST.replace(
        "description: Beginner course\n",
        "description: Beginner course\n"
        "objectives: [Goal one]\n"
        "competencies: [Skill one, Skill two]\n"
        "estimated_duration_minutes: 45\n",
    )
    (tmp_path / "course.yaml").write_text(manifest, encoding="utf-8")
    result = CliRunner().invoke(
        main,
        ["course", "validate", "--project", str(tmp_path), "--format", "json"],
    )
    assert result.exit_code == 0, result.output
    assert '"objectives": 1' in result.output
    assert '"competencies": 2' in result.output
    assert '"duration_minutes": 45' in result.output


def test_course_presentation_defaults_preserve_legacy_manifest(tmp_path: Path) -> None:
    make_project(tmp_path)
    result = CliRunner().invoke(
        main,
        ["course", "validate", "--project", str(tmp_path), "--format", "json"],
    )
    assert result.exit_code == 0, result.output
    assert '"theme": "midnight"' in result.output


def test_course_presentation_customizes_theme_and_visibility(tmp_path: Path) -> None:
    make_project(tmp_path)
    manifest = MANIFEST.replace(
        "description: Beginner course\n",
        """description: Beginner course
presentation:
  theme: forest
  accent: "#123456"
  show_contents: false
  show_progress: false
  show_objectives: false
  show_competencies: false
  show_prerequisites: false
  show_lesson_navigation: false
objectives: [Course goal]
competencies: [Speaking]
""",
    )
    (tmp_path / "course.yaml").write_text(manifest, encoding="utf-8")
    result = CliRunner().invoke(
        main,
        ["course", "build", "--project", str(tmp_path), "--format", "html"],
    )
    assert result.exit_code == 0, result.output
    index = (tmp_path / "output/course.html").read_text(encoding="utf-8")
    assert 'edutex-course-theme" content="forest"' in index
    assert "--accent:#123456" in index
    assert '<nav class="contents"' not in index
    assert '<section class="progress-card"' not in index
    assert "Course goals" not in index
    assert "Skills you will build" not in index


def test_course_presentation_rejects_invalid_theme_and_color(tmp_path: Path) -> None:
    make_project(tmp_path)
    manifest = MANIFEST.replace(
        "description: Beginner course\n",
        """description: Beginner course
presentation:
  theme: neon
  accent: blue
""",
    )
    (tmp_path / "course.yaml").write_text(manifest, encoding="utf-8")
    result = CliRunner().invoke(main, ["course", "validate", "--project", str(tmp_path)])
    assert result.exit_code != 0
    assert "course.presentation.theme must be one of" in result.output
    assert "six-digit hexadecimal color" in result.output

def test_course_html_has_structural_accessibility_and_local_link_contract(tmp_path: Path) -> None:
    make_project(tmp_path)
    (tmp_path / "lessons/goodbye.md").write_text(GOODBYE_LESSON, encoding="utf-8")
    manifest = MANIFEST.replace(
        "        objectives: [Introduce yourself]\n",
        "        objectives: [Introduce yourself]\n"
        "      - id: lesson-02\n"
        "        title: Goodbye\n"
        "        source: lessons/goodbye.md\n",
    )
    (tmp_path / "course.yaml").write_text(manifest, encoding="utf-8")

    result = CliRunner().invoke(
        main, ["course", "build", "--project", str(tmp_path), "--format", "html"]
    )
    assert result.exit_code == 0, result.output

    output = tmp_path / "output"
    index = (output / "course.html").read_text(encoding="utf-8")
    lesson_pages = [
        output / "lessons" / "lesson-01.html",
        output / "lessons" / "lesson-02.html",
    ]

    for page in [output / "course.html", *lesson_pages]:
        source_page = page.read_text(encoding="utf-8")
        HTMLParser().feed(source_page)

        ids = re.findall(r'\bid="([^"]+)', source_page)
        assert len(ids) == len(set(ids)), page.name
        for labelled_by in re.findall(r'aria-labelledby="([^"]+)"', source_page):
            assert f'id="{labelled_by}"' in source_page, (page.name, labelled_by)

    assert '<main id="course-content" tabindex="-1" aria-labelledby="course-title">' in index
    assert '<h1 id="course-title">German A1</h1>' in index
    assert '<main id="lesson-content" tabindex="-1" aria-label="Lesson content">' in (
        lesson_pages[0].read_text(encoding="utf-8")
    )
    assert 'aria-label="Course navigation"' in lesson_pages[0].read_text(encoding="utf-8")
    assert 'aria-label="Course index"' in lesson_pages[0].read_text(encoding="utf-8")

    for href in re.findall(r'href="([^"]+)"', index):
        if href.startswith(("#", "http://", "https://", "mailto:")):
            continue
        assert (output / href).is_file(), href

    for page in lesson_pages:
        source_page = page.read_text(encoding="utf-8")
        for href in re.findall(r'href="([^"]+)"', source_page):
            if href.startswith(("#", "http://", "https://", "mailto:")):
                continue
            assert (page.parent / href).resolve().is_file(), (page.name, href)


def test_course_build_pdf_accessibility_contract(tmp_path: Path) -> None:
    import shutil
    import subprocess

    import pytest

    required = ("pdfinfo", "pdftotext", "pdftoppm")
    if not (shutil.which("latexmk") or shutil.which("pdflatex")):
        pytest.skip("No LaTeX compiler available")
    if not all(shutil.which(tool) for tool in required):
        pytest.skip("PDF inspection tools are not available")

    make_project(tmp_path)
    result = CliRunner().invoke(
        main,
        ["course", "build", "--project", str(tmp_path), "--format", "pdf"],
    )
    assert result.exit_code == 0, result.output

    tex = (tmp_path / "output" / "course.tex").read_text(encoding="utf-8")
    for expected in (
        r"\usepackage{cmap}",
        r"\pdfgentounicode=1",
        r"pdflang={de-DE}",
        "unicode=true",
        "bookmarks=true",
        "bookmarksopen=true",
        "bookmarksnumbered=true",
        r"\tableofcontents",
        r"\section{Greetings}",
    ):
        assert expected in tex

    pdf_path = tmp_path / "output" / "course.pdf"
    assert pdf_path.is_file()

    info = subprocess.run(
        [shutil.which("pdfinfo"), str(pdf_path)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    fields = {
        line.split(":", 1)[0].strip(): line.split(":", 1)[1].strip()
        for line in info.splitlines()
        if ":" in line
    }
    assert int(fields["Pages"]) >= 1
    assert fields.get("Title") == "German A1"
    assert fields.get("Author") == "EduTeX"
    assert fields.get("Subject") == "Beginner course"

    text_path = tmp_path / "course-accessibility.txt"
    subprocess.run(
        [shutil.which("pdftotext"), str(pdf_path), str(text_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    text = text_path.read_text(encoding="utf-8", errors="replace")
    assert "German A1" in text
    assert "Greetings" in text
    assert "Hello" in text
    assert text.index("Greetings") < text.index("Hello")

    preview_dir = tmp_path / "pdf-accessibility-preview"
    preview_dir.mkdir()
    subprocess.run(
        [
            shutil.which("pdftoppm"),
            "-f",
            "1",
            "-l",
            "1",
            "-png",
            str(pdf_path),
            str(preview_dir / "page"),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert any(preview_dir.glob("page-*.png"))

    inspector = shutil.which("mutool")
    if inspector:
        outline = subprocess.run(
            [inspector, "show", str(pdf_path), "outline"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        assert "Greetings" in outline
        assert "Hello" in outline

def test_course_html_multilingual_labels_and_unicode(tmp_path: Path) -> None:
    from html.parser import HTMLParser

    make_project(tmp_path)
    manifest_path = tmp_path / "course.yaml"
    manifest = manifest_path.read_text(encoding="utf-8")
    expected = {
        "it": (
            "Moduli",
            "Lezioni",
            "Indice del corso",
            "Progressi",
            "Segna come completata",
            "Segna come non completata",
        ),
        "en": (
            "Modules",
            "Lessons",
            "Course contents",
            "Progress",
            "Mark lesson complete",
            "Mark as incomplete",
        ),
        "ja": (
            "モジュール",
            "レッスン",
            "コース目次",
            "進捗",
            "レッスンを完了にする",
            "完了を取り消す",
        ),
    }

    for language, labels in expected.items():
        manifest_path.write_text(
            manifest.replace("language: de\n", f"language: {language}\n"),
            encoding="utf-8",
        )
        result = CliRunner().invoke(
            main,
            ["course", "build", "--project", str(tmp_path), "--format", "html"],
        )
        assert result.exit_code == 0, f"language={language}: {result.output}"

        source = (tmp_path / "output" / "course.html").read_text(
            encoding="utf-8"
        )
        HTMLParser().feed(source)

        assert f'<html lang="{language}">' in source
        assert 'aria-pressed="false"' in source
        assert 'button.setAttribute("aria-pressed", String(isCompleted));' in source
        assert "completed.delete(lessonId)" in source
        for label in labels:
            assert label in source, (
                f"missing label {label!r} for language={language}"
            )

        assert "edutex:course:german-a1:completed" in source
        assert "Ã" not in source
        assert "ã" not in source

def test_course_html_language_variants_and_fallback(tmp_path: Path) -> None:
    make_project(tmp_path)
    manifest_path = tmp_path / "course.yaml"
    manifest = manifest_path.read_text(encoding="utf-8")

    expected = {
        "it-IT": ("Moduli", "Indice del corso"),
        "ja-JP": ("モジュール", "コース目次"),
        "fr": ("Modules", "Course contents"),
    }

    for language, labels in expected.items():
        manifest_path.write_text(
            manifest.replace("language: de\n", f"language: {language}\n"),
            encoding="utf-8",
        )
        result = CliRunner().invoke(
            main,
            ["course", "build", "--project", str(tmp_path), "--format", "html"],
        )
        assert result.exit_code == 0, f"language={language}: {result.output}"

        source = (tmp_path / "output" / "course.html").read_text(
            encoding="utf-8"
        )
        assert f'<html lang="{language}">' in source
        for label in labels:
            assert label in source, (
                f"missing label {label!r} for language={language}"
            )
        assert "Ã" not in source
        assert "ã" not in source

def test_course_html_multilingual_semantic_accessibility(tmp_path: Path) -> None:
    from html.parser import HTMLParser

    class AccessibilityParser(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.html_lang = ""
            self.buttons: list[dict[str, str]] = []
            self.live_regions: list[dict[str, str]] = []

        def handle_starttag(
            self, tag: str, attrs: list[tuple[str, str | None]]
        ) -> None:
            attributes = {
                name: value or "" for name, value in attrs
            }
            if tag == "html":
                self.html_lang = attributes.get("lang", "")
            if tag == "button":
                self.buttons.append(attributes)
            if "aria-live" in attributes:
                self.live_regions.append(attributes)

    make_project(tmp_path)
    manifest_path = tmp_path / "course.yaml"
    manifest = manifest_path.read_text(encoding="utf-8")

    expected = {
        "it": {
            "skip": "Vai al contenuto del corso",
            "kicker": "Corso EduTeX",
            "complete": "Segna come completata",
        },
        "ja": {
            "skip": "コース内容へ移動",
            "kicker": "EduTeX コース",
            "complete": "レッスンを完了にする",
        },
    }

    for language, labels in expected.items():
        manifest_path.write_text(
            manifest.replace("language: de\n", f"language: {language}\n"),
            encoding="utf-8",
        )
        result = CliRunner().invoke(
            main,
            ["course", "build", "--project", str(tmp_path), "--format", "html"],
        )
        assert result.exit_code == 0, f"language={language}: {result.output}"

        source = (tmp_path / "output" / "course.html").read_text(
            encoding="utf-8"
        )
        parser = AccessibilityParser()
        parser.feed(source)

        assert parser.html_lang == language
        assert labels["skip"] in source
        assert labels["kicker"] in source
        assert labels["complete"] in source

        assert parser.buttons
        for button in parser.buttons:
            assert button.get("type") == "button"
            assert button.get("aria-label")
            assert button.get("aria-pressed") == "false"
            assert button.get("data-mark-complete")

        assert parser.live_regions
        assert 'aria-live="polite"' in source

        assert "Skip to course content" not in source
        assert "EduTeX course" not in source
        assert "Self-paced" not in source
        assert "Ã" not in source
        assert "ã" not in source

def test_course_html_localized_lesson_link_labels(tmp_path: Path) -> None:
    from edutex.course.service import load_course_manifest, render_course_html

    make_project(tmp_path)
    (tmp_path / "lessons/goodbye.md").write_text(
        GOODBYE_LESSON,
        encoding="utf-8",
    )

    manifest = MANIFEST.replace(
        "language: de\n",
        "language: it\n",
    ).replace(
        "        objectives: [Introduce yourself]\n",
        "        objectives: [Introduce yourself]\n"
        "      - id: lesson-02\n"
        "        title: Goodbye\n"
        "        source: lessons/goodbye.md\n",
    )
    (tmp_path / "course.yaml").write_text(manifest, encoding="utf-8")

    report = load_course_manifest(tmp_path / "course.yaml", tmp_path)
    assert report.manifest is not None

    index = render_course_html(
        report.manifest,
        {"lesson-01": "lessons/lesson-01.html"},
    )

    assert 'href="lessons/lesson-01.html"' in index
    assert '>Apri lezione</a>' in index
    assert 'href="../lessons/goodbye.md"' in index
    assert '>Apri sorgente della lezione</a>' in index
    assert ">Open lesson</a>" not in index
    assert ">Open lesson source</a>" not in index

def test_course_lesson_navigation_is_multilingual(tmp_path: Path) -> None:
    make_project(tmp_path)
    manifest_path = tmp_path / "course.yaml"
    manifest = manifest_path.read_text(encoding="utf-8")

    expected = {
        "it": {
            "navigation": "Navigazione del corso",
            "index": "Indice del corso",
            "module": "Modulo 1 · Lezione 1",
            "previous": "Precedente",
            "next": "Successiva",
            "complete": "Segna come completata",
            "skip": "Vai al contenuto della lezione",
            "content": "Contenuto della lezione",
        },
        "ja": {
            "navigation": "コースナビゲーション",
            "index": "コース目次",
            "module": "モジュール 1 · レッスン 1",
            "previous": "前へ",
            "next": "次へ",
            "complete": "レッスンを完了にする",
            "skip": "レッスン内容へ移動",
            "content": "レッスン内容",
        },
    }

    for language, labels in expected.items():
        manifest_path.write_text(
            manifest.replace("language: de\n", f"language: {language}\n"),
            encoding="utf-8",
        )
        result = CliRunner().invoke(
            main,
            ["course", "build", "--project", str(tmp_path), "--format", "html"],
        )
        assert result.exit_code == 0, f"language={language}: {result.output}"

        lesson = (
            tmp_path / "output" / "lessons" / "lesson-01.html"
        ).read_text(encoding="utf-8")

        assert f'aria-label="{labels["navigation"]}"' in lesson
        assert f'aria-label="{labels["index"]}"' in lesson
        assert labels["module"] in lesson
        assert labels["previous"] in lesson
        assert labels["next"] in lesson
        assert labels["complete"] in lesson
        assert labels["skip"] in lesson
        assert f'aria-label="{labels["content"]}"' in lesson
        assert 'aria-pressed="false"' in lesson
        assert 'aria-live="polite"' in lesson
        assert "Course navigation" not in lesson
        assert "Course index" not in lesson
        assert "Mark lesson complete" not in lesson
        assert "Ã" not in lesson
        assert "ã" not in lesson

def test_course_lesson_navigation_language_variants(tmp_path: Path) -> None:
    make_project(tmp_path)
    manifest_path = tmp_path / "course.yaml"
    manifest = manifest_path.read_text(encoding="utf-8")

    expected = {
        "it-IT": {
            "navigation": "Navigazione del corso",
            "index": "Indice del corso",
            "complete": "Segna come completata",
        },
        "ja-JP": {
            "navigation": "コースナビゲーション",
            "index": "コース目次",
            "complete": "レッスンを完了にする",
        },
        "fr": {
            "navigation": "Course navigation",
            "index": "Course index",
            "complete": "Mark lesson complete",
        },
    }

    for language, labels in expected.items():
        manifest_path.write_text(
            manifest.replace("language: de\n", f"language: {language}\n"),
            encoding="utf-8",
        )
        result = CliRunner().invoke(
            main,
            ["course", "build", "--project", str(tmp_path), "--format", "html"],
        )
        assert result.exit_code == 0, f"language={language}: {result.output}"

        lesson = (
            tmp_path / "output" / "lessons" / "lesson-01.html"
        ).read_text(encoding="utf-8")

        assert '<html lang="en">' in lesson
        assert f'aria-label="{labels["navigation"]}"' in lesson
        assert f'aria-label="{labels["index"]}"' in lesson
        assert labels["complete"] in lesson
        assert 'aria-pressed="false"' in lesson
        assert 'aria-live="polite"' in lesson
        assert "Ã" not in lesson
        assert "ã" not in lesson

def test_course_lesson_completion_runtime_contract(tmp_path: Path) -> None:
    make_project(tmp_path)
    manifest_path = tmp_path / "course.yaml"
    manifest = manifest_path.read_text(encoding="utf-8")

    expected = {
        "it": {
            "complete": "Segna come completata",
            "incomplete": "Segna come non completata",
            "completed": "Completata",
        },
        "ja": {
            "complete": "レッスンを完了にする",
            "incomplete": "完了を取り消す",
            "completed": "完了",
        },
    }

    for language, labels in expected.items():
        manifest_path.write_text(
            manifest.replace("language: de\n", f"language: {language}\n"),
            encoding="utf-8",
        )
        result = CliRunner().invoke(
            main,
            ["course", "build", "--project", str(tmp_path), "--format", "html"],
        )
        assert result.exit_code == 0, f"language={language}: {result.output}"

        lesson = (
            tmp_path / "output" / "lessons" / "lesson-01.html"
        ).read_text(encoding="utf-8")

        assert "edutex:course:german-a1:completed" in lesson
        assert "localStorage.getItem(key)" in lesson
        assert "localStorage.setItem(key, JSON.stringify([...items]))" in lesson
        assert "completed.has(lessonId)" in lesson
        assert "completed.delete(lessonId)" in lesson
        assert "completed.add(lessonId)" in lesson
        assert "labels.mark_incomplete" in lesson
        assert "labels.mark_complete" in lesson
        assert 'button.setAttribute("aria-label", button.textContent);' in lesson
        assert 'button.setAttribute("aria-pressed", String(isComplete));' in lesson
        assert f">{labels['complete']}</button>" in lesson
        assert labels["incomplete"] in lesson
        assert labels["completed"] in lesson
        assert 'aria-pressed="false"' in lesson
        assert "Ã" not in lesson
        assert "ã" not in lesson

def test_course_lesson_navigation_aria_labels_are_localized(tmp_path: Path) -> None:
    make_project(tmp_path)
    (tmp_path / "lessons/goodbye.md").write_text(
        GOODBYE_LESSON,
        encoding="utf-8",
    )

    manifest_path = tmp_path / "course.yaml"
    manifest = manifest_path.read_text(encoding="utf-8")
    manifest = manifest.replace(
        "        objectives: [Introduce yourself]\n",
        "        objectives: [Introduce yourself]\n"
        "      - id: lesson-02\n"
        "        title: Goodbye\n"
        "        source: lessons/goodbye.md\n",
    )

    expected = {
        "it": 'aria-label="Successiva lezione: Goodbye"',
        "ja": 'aria-label="次へ レッスン: Goodbye"',
        "fr": 'aria-label="Next lesson: Goodbye"',
    }

    for language, expected_label in expected.items():
        manifest_path.write_text(
            manifest.replace("language: de\n", f"language: {language}\n"),
            encoding="utf-8",
        )
        result = CliRunner().invoke(
            main,
            ["course", "build", "--project", str(tmp_path), "--format", "html"],
        )
        assert result.exit_code == 0, f"language={language}: {result.output}"

        first = (
            tmp_path / "output" / "lessons" / "lesson-01.html"
        ).read_text(encoding="utf-8")

        assert expected_label in first
        assert 'aria-label="Successiva lesson: Goodbye"' not in first
        assert 'aria-label="次へ lesson: Goodbye"' not in first
        assert "Ã" not in first
        assert "ã" not in first
