"""Contract tests for printable course content and its solutions appendix."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from edutex.core.cli import main


def _write_lesson(
    project: Path,
    *,
    lesson_id: str,
    title: str,
    body_marker: str,
    exercise_marker: str,
    solution_marker: str,
) -> None:
    source = f"""---
id: {lesson_id}
title: {title}
language: it
level: A1
version: 1.0.0
author: EduTeX
---
# {title}

{body_marker}

::: exercise
title: Esercizio di {title}
{exercise_marker}
::: solution
{solution_marker}
:::
:::
"""
    (project / "lessons" / f"{lesson_id}.md").write_text(
        source,
        encoding="utf-8",
    )


def test_course_latex_includes_lessons_exercises_and_final_solutions(
    tmp_path: Path,
) -> None:
    project = tmp_path / "printable-course"
    runner = CliRunner()
    initialized = runner.invoke(
        main,
        ["init", str(project), "--theme", "dark", "--language", "it"],
    )
    assert initialized.exit_code == 0, initialized.output

    (project / "lessons").mkdir(exist_ok=True)
    _write_lesson(
        project,
        lesson_id="lesson-one",
        title="Prima lezione",
        body_marker="FirstLessonBodyMarker",
        exercise_marker="FirstExercisePromptMarker",
        solution_marker="FirstSolutionMarker",
    )
    _write_lesson(
        project,
        lesson_id="lesson-two",
        title="Seconda lezione",
        body_marker="SecondLessonBodyMarker",
        exercise_marker="SecondExercisePromptMarker",
        solution_marker="SecondSolutionMarker",
    )

    (project / "course.yaml").write_text(
        """id: printable-course
title: Corso stampabile
language: it
level: A1
version: 1.0.0
modules:
  - id: module-one
    title: Primo modulo
    lessons:
      - id: lesson-one
        title: Prima lezione
        source: lessons/lesson-one.md
  - id: module-two
    title: Secondo modulo
    lessons:
      - id: lesson-two
        title: Seconda lezione
        source: lessons/lesson-two.md
""",
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "course",
            "build",
            "--project",
            str(project),
            "--format",
            "latex",
        ],
    )
    assert result.exit_code == 0, result.output

    source = (project / "output" / "course.tex").read_text(encoding="utf-8")
    ordered_content = (
        "FirstLessonBodyMarker",
        "FirstExercisePromptMarker",
        "SecondLessonBodyMarker",
        "SecondExercisePromptMarker",
    )
    positions = []
    for marker in ordered_content:
        assert marker in source, f"Missing printable course content: {marker}"
        positions.append(source.index(marker))
    assert positions == sorted(positions), "Lessons or exercises are out of manifest order."

    solutions_heading = r"\section*{Soluzioni}"
    assert solutions_heading in source, "Expected a final solutions section."
    lesson_content, solutions = source.split(solutions_heading, maxsplit=1)

    for marker in ("FirstSolutionMarker", "SecondSolutionMarker"):
        assert marker not in lesson_content, f"Solution appears inline: {marker}"
        assert marker in solutions, f"Solution missing from the appendix: {marker}"

    assert solutions.index("FirstSolutionMarker") < solutions.index("SecondSolutionMarker")