"""Course manifest validation and course index rendering.

The course layer deliberately sits beside the lesson pipeline. It owns the
course hierarchy and its navigation outputs, while existing Knowledge, Theme,
Layout, and Build services continue to own individual lesson generation.
"""

from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml

from edutex.core.errors import KnowledgeError
from edutex.knowledge.loader import load_knowledge_model


_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


class CourseBuildError(ValueError):
    """Raised when a course manifest cannot be validated or built."""


@dataclass(frozen=True)
class CourseLesson:
    """One lesson entry in a course module."""

    lesson_id: str
    title: str
    source: str
    description: str = ""
    duration_minutes: int | None = None
    objectives: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    prerequisites: tuple[str, ...] = ()


@dataclass(frozen=True)
class CourseModule:
    """An ordered group of lessons."""

    module_id: str
    title: str
    description: str = ""
    lessons: tuple[CourseLesson, ...] = ()


@dataclass(frozen=True)
class CoursePresentation:
    """Optional visual and navigation preferences for a course index."""

    theme: str = "midnight"
    accent: str = "#72b7ff"
    accent_secondary: str = "#26734d"
    surface: str = "#ffffff"
    background: str = "#f6f8fb"
    ink: str = "#172033"
    muted: str = "#536176"
    show_contents: bool = True
    show_progress: bool = True
    show_objectives: bool = True
    show_competencies: bool = True
    show_prerequisites: bool = True
    show_lesson_navigation: bool = True


@dataclass(frozen=True)
class CourseManifest:
    """Validated course metadata and ordered curriculum."""

    course_id: str
    title: str
    language: str = "en"
    level: str = ""
    version: str = "1.0.0"
    author: str = ""
    description: str = ""
    objectives: tuple[str, ...] = ()
    competencies: tuple[str, ...] = ()
    estimated_duration_minutes: int | None = None
    presentation: CoursePresentation = CoursePresentation()
    modules: tuple[CourseModule, ...] = ()

    @property
    def lesson_count(self) -> int:
        return sum(len(module.lessons) for module in self.modules)

    @property
    def module_count(self) -> int:
        return len(self.modules)

    @property
    def duration_minutes(self) -> int:
        """Return the declared estimate or the sum of lesson durations."""
        if self.estimated_duration_minutes is not None:
            return self.estimated_duration_minutes
        return sum(
            lesson.duration_minutes or 0
            for module in self.modules
            for lesson in module.lessons
        )


@dataclass(frozen=True)
class CourseDiagnostic:
    """Machine-readable validation diagnostic."""

    code: str
    message: str
    severity: str = "error"
    field: str | None = None
    path: str | None = None

    def to_dict(self) -> dict[str, str]:
        result = {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
        }
        if self.field is not None:
            result["field"] = self.field
        if self.path is not None:
            result["path"] = self.path
        return result


@dataclass
class CourseValidation:
    """Stable validation result suitable for text or JSON CLI output."""

    manifest_path: str
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    manifest: CourseManifest | None = None
    diagnostics: list[CourseDiagnostic] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest": self.manifest_path,
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "course": (
                {
                    "id": self.manifest.course_id,
                    "title": self.manifest.title,
                    "modules": self.manifest.module_count,
                    "lessons": self.manifest.lesson_count,
                    "dependencies": sum(
                        len(lesson.prerequisites)
                        for module in self.manifest.modules
                        for lesson in module.lessons
                    ),
                    "objectives": len(self.manifest.objectives),
                    "competencies": len(self.manifest.competencies),
                    "duration_minutes": self.manifest.duration_minutes,
                    "theme": self.manifest.presentation.theme,
                }
                if self.manifest is not None
                else None
            ),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def _text(value: Any, field_name: str, errors: list[str], *, required: bool = False) -> str:
    if value is None:
        if required:
            errors.append(f"{field_name} is required.")
        return ""
    if not isinstance(value, str):
        errors.append(f"{field_name} must be a string.")
        return ""
    result = value.strip()
    if required and not result:
        errors.append(f"{field_name} must not be empty.")
    return result


def _string_list(value: Any, field_name: str, errors: list[str]) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        errors.append(f"{field_name} must be a list of strings.")
        return ()
    return tuple(item.strip() for item in value if item.strip())


def _duration(value: Any, field_name: str, errors: list[str]) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        errors.append(f"{field_name} must be a positive integer.")
        return None
    return value


def _safe_source(project_root: Path, source: str, field_name: str, errors: list[str]) -> None:
    path = Path(source)
    if path.is_absolute() or ".." in path.parts:
        errors.append(f"{field_name} must be a relative path inside the project.")
        return
    resolved = (project_root / path).resolve()
    try:
        resolved.relative_to(project_root.resolve())
    except ValueError:
        errors.append(f"{field_name} must stay inside the project.")
        return
    if not resolved.is_file():
        errors.append(f"{field_name} does not exist: {source}")


_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def _color(value: Any, field_name: str, errors: list[str], default: str) -> str:
    if value is None:
        return default
    if not isinstance(value, str) or not _HEX_RE.fullmatch(value.strip()):
        errors.append(f"{field_name} must be a six-digit hexadecimal color such as #72b7ff.")
        return default
    return value.strip().lower()


def _boolean(value: Any, field_name: str, errors: list[str], default: bool) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        errors.append(f"{field_name} must be true or false.")
        return default
    return value


def _parse_presentation(value: Any, errors: list[str]) -> CoursePresentation:
    if value is None:
        return CoursePresentation()
    if not isinstance(value, dict):
        errors.append("course.presentation must be a YAML mapping.")
        return CoursePresentation()
    theme = _text(value.get("theme", "midnight"), "course.presentation.theme", errors) or "midnight"
    allowed_themes = {"midnight", "paper", "forest", "sunset"}
    if theme not in allowed_themes:
        errors.append("course.presentation.theme must be one of: " + ", ".join(sorted(allowed_themes)) + ".")
        theme = "midnight"
    palettes = {
        "midnight": {"accent": "#72b7ff", "accent_secondary": "#26734d", "surface": "#ffffff", "background": "#f6f8fb", "ink": "#172033", "muted": "#536176"},
        "paper": {"accent": "#9a4d2f", "accent_secondary": "#55734b", "surface": "#fffdf7", "background": "#f2eee4", "ink": "#30281f", "muted": "#6f6255"},
        "forest": {"accent": "#86c7a5", "accent_secondary": "#d4a85c", "surface": "#f8fcf8", "background": "#eaf3ed", "ink": "#17352a", "muted": "#547366"},
        "sunset": {"accent": "#ffb07c", "accent_secondary": "#7d568c", "surface": "#fffaf8", "background": "#f8eeeb", "ink": "#402532", "muted": "#80626b"},
    }
    palette = palettes[theme]
    return CoursePresentation(
        theme=theme,
        accent=_color(value.get("accent"), "course.presentation.accent", errors, palette["accent"]),
        accent_secondary=_color(value.get("accent_secondary"), "course.presentation.accent_secondary", errors, palette["accent_secondary"]),
        surface=_color(value.get("surface"), "course.presentation.surface", errors, palette["surface"]),
        background=_color(value.get("background"), "course.presentation.background", errors, palette["background"]),
        ink=_color(value.get("ink"), "course.presentation.ink", errors, palette["ink"]),
        muted=_color(value.get("muted"), "course.presentation.muted", errors, palette["muted"]),
        show_contents=_boolean(value.get("show_contents"), "course.presentation.show_contents", errors, True),
        show_progress=_boolean(value.get("show_progress"), "course.presentation.show_progress", errors, True),
        show_objectives=_boolean(value.get("show_objectives"), "course.presentation.show_objectives", errors, True),
        show_competencies=_boolean(value.get("show_competencies"), "course.presentation.show_competencies", errors, True),
        show_prerequisites=_boolean(value.get("show_prerequisites"), "course.presentation.show_prerequisites", errors, True),
        show_lesson_navigation=_boolean(value.get("show_lesson_navigation"), "course.presentation.show_lesson_navigation", errors, True),
    )


def _validate_lesson_source(
    project_root: Path,
    source: str,
    field_name: str,
    errors: list[str],
) -> None:
    """Validate a linked Knowledge Model without parsing its lesson body."""
    path = (project_root / source).resolve()
    if not path.is_file():
        return
    try:
        load_knowledge_model(path)
    except (KnowledgeError, OSError, UnicodeError) as exc:
        errors.append(f"{field_name} is not a valid Knowledge Model: {exc}")



def _relative_diagnostic_path(value: str, project_root: Path) -> str | None:
    """Return a project-relative path when a diagnostic contains a file path."""
    candidate = Path(value)
    try:
        return candidate.resolve().relative_to(project_root.resolve()).as_posix()
    except (ValueError, OSError):
        return value.replace("\\", "/") if value else None


def _diagnostic_for_message(
    message: str,
    project_root: Path,
    severity: str,
    manifest: CourseManifest | None = None,
) -> CourseDiagnostic:
    """Map stable validation messages to codes and manifest fields."""
    field_name = (message.split(" ", 1)[0] if message.startswith("course.") else None)
    prerequisite_match = re.search(
        r"(?:Unknown prerequisite|Lesson) .*?lesson '([^']+)'",
        message,
        flags=re.IGNORECASE,
    )
    if prerequisite_match and manifest is not None:
        lesson_id = prerequisite_match.group(1)
        for module_number, module in enumerate(manifest.modules, start=1):
            for lesson_number, lesson in enumerate(module.lessons, start=1):
                if lesson.lesson_id == lesson_id:
                    field_name = (
                        f"course.modules[{module_number}].lessons[{lesson_number}].prerequisites"
                    )
                    break
    lower = message.lower()
    path_value: str | None = None
    if "knowledge model '" in message.lower():
        start = lower.index("knowledge model '") + len("knowledge model '")
        end = lower.find("'", start)
        if end > start:
            path_value = _relative_diagnostic_path(message[start:end], project_root)
    elif "does not exist: " in message:
        path_value = message.rsplit("does not exist: ", 1)[1].strip()
        path_value = _relative_diagnostic_path(path_value, project_root)

    if "is not a valid knowledge model" in lower:
        if "missing yaml front matter" in lower or "missing the yaml frontmatter" in lower:
            code = "COURSE_SOURCE_FRONTMATTER_MISSING"
        elif "missing required front matter fields" in lower or "missing required frontmatter fields" in lower:
            code = "COURSE_SOURCE_REQUIRED_FIELD"
        elif "invalid yaml" in lower or "unclosed yaml" in lower:
            code = "COURSE_SOURCE_FRONTMATTER_INVALID"
        else:
            code = "COURSE_SOURCE_INVALID"
        return CourseDiagnostic(code, message, severity, field_name, path_value)
    if ".source does not exist:" in lower:
        return CourseDiagnostic("COURSE_SOURCE_NOT_FOUND", message, severity, field_name, path_value)
    if ".source must" in lower or ".source is outside" in lower:
        return CourseDiagnostic("COURSE_SOURCE_PATH_INVALID", message, severity, field_name)
    if "unknown prerequisite" in lower:
        return CourseDiagnostic("COURSE_PREREQUISITE_UNKNOWN", message, severity, field_name)
    if "prerequisite cycle" in lower or "cannot be its own prerequisite" in lower:
        return CourseDiagnostic("COURSE_PREREQUISITE_CYCLE", message, severity, field_name)
    if "course.presentation" in lower:
        return CourseDiagnostic("COURSE_PRESENTATION_INVALID", message, severity, field_name)
    if "no lesson duration_minutes values were provided" in lower:
        return CourseDiagnostic("COURSE_DURATION_UNDECLARED", message, severity, field_name)
    return CourseDiagnostic("COURSE_MANIFEST_INVALID", message, severity, field_name)


def _diagnostics(
    errors: list[str],
    warnings: list[str],
    project_root: Path,
    manifest: CourseManifest | None = None,
) -> list[CourseDiagnostic]:
    """Build ordered diagnostics while preserving the legacy message lists."""
    return [
        *(_diagnostic_for_message(message, project_root, "error", manifest) for message in errors),
        *(_diagnostic_for_message(message, project_root, "warning", manifest) for message in warnings),
    ]

def _parse_manifest(raw: Any, project_root: Path, manifest_path: Path) -> CourseValidation:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(raw, dict):
        error = "Manifest must be a YAML mapping."
        return CourseValidation(str(manifest_path), False, [error], [], diagnostics=[_diagnostic_for_message(error, project_root, "error")])

    data = raw.get("course", raw)
    if not isinstance(data, dict):
        error = "course must be a YAML mapping."
        return CourseValidation(str(manifest_path), False, [error], [], diagnostics=[_diagnostic_for_message(error, project_root, "error")])

    course_id = _text(data.get("id"), "course.id", errors, required=True)
    title = _text(data.get("title"), "course.title", errors, required=True)
    if course_id and not _ID_RE.fullmatch(course_id):
        errors.append("course.id must contain only lowercase letters, numbers, '_' or '-'.")
    language = _text(data.get("language", "en"), "course.language", errors) or "en"
    level = _text(data.get("level", ""), "course.level", errors)
    version = _text(data.get("version", "1.0.0"), "course.version", errors) or "1.0.0"
    author = _text(data.get("author", ""), "course.author", errors)
    description = _text(data.get("description", ""), "course.description", errors)
    presentation = _parse_presentation(data.get("presentation"), errors)
    objectives = _string_list(data.get("objectives"), "course.objectives", errors)
    competencies = _string_list(
        data.get("competencies", data.get("skills")),
        "course.competencies",
        errors,
    )
    estimated_duration = _duration(
        data.get("estimated_duration_minutes"),
        "course.estimated_duration_minutes",
        errors,
    )

    modules_raw = data.get("modules")
    if not isinstance(modules_raw, list) or not modules_raw:
        errors.append("course.modules must be a non-empty list.")
        modules_raw = []

    modules: list[CourseModule] = []
    module_ids: set[str] = set()
    lesson_ids: set[str] = set()
    for module_index, module_raw in enumerate(modules_raw, start=1):
        prefix = f"course.modules[{module_index}]"
        if not isinstance(module_raw, dict):
            errors.append(f"{prefix} must be a mapping.")
            continue
        module_id = _text(module_raw.get("id"), f"{prefix}.id", errors, required=True)
        module_title = _text(module_raw.get("title"), f"{prefix}.title", errors, required=True)
        module_description = _text(module_raw.get("description", ""), f"{prefix}.description", errors)
        if module_id and not _ID_RE.fullmatch(module_id):
            errors.append(f"{prefix}.id must contain only lowercase letters, numbers, '_' or '-'.")
        if module_id in module_ids:
            errors.append(f"Duplicate module id: {module_id}.")
        module_ids.add(module_id)

        lessons_raw = module_raw.get("lessons")
        if not isinstance(lessons_raw, list) or not lessons_raw:
            errors.append(f"{prefix}.lessons must be a non-empty list.")
            lessons_raw = []
        lessons: list[CourseLesson] = []
        for lesson_index, lesson_raw in enumerate(lessons_raw, start=1):
            lesson_prefix = f"{prefix}.lessons[{lesson_index}]"
            if not isinstance(lesson_raw, dict):
                errors.append(f"{lesson_prefix} must be a mapping.")
                continue
            lesson_id = _text(lesson_raw.get("id"), f"{lesson_prefix}.id", errors, required=True)
            lesson_title = _text(lesson_raw.get("title"), f"{lesson_prefix}.title", errors, required=True)
            source = _text(
                lesson_raw.get("source", lesson_raw.get("path")),
                f"{lesson_prefix}.source",
                errors,
                required=True,
            )
            if lesson_id and not _ID_RE.fullmatch(lesson_id):
                errors.append(f"{lesson_prefix}.id must contain only lowercase letters, numbers, '_' or '-'.")
            if lesson_id in lesson_ids:
                errors.append(f"Duplicate lesson id: {lesson_id}.")
            lesson_ids.add(lesson_id)
            if source:
                source_field = f"{lesson_prefix}.source"
                _safe_source(project_root, source, source_field, errors)
                if not any(error.startswith(source_field + " ") for error in errors):
                    _validate_lesson_source(project_root, source, source_field, errors)
            duration = _duration(lesson_raw.get("duration_minutes"), f"{lesson_prefix}.duration_minutes", errors)
            lesson_objectives = _string_list(
                lesson_raw.get("objectives"),
                f"{lesson_prefix}.objectives",
                errors,
            )
            tags = _string_list(lesson_raw.get("tags"), f"{lesson_prefix}.tags", errors)
            prerequisites = _string_list(
                lesson_raw.get("prerequisites", lesson_raw.get("requires")),
                f"{lesson_prefix}.prerequisites",
                errors,
            )
            if len(set(prerequisites)) != len(prerequisites):
                errors.append(f"{lesson_prefix}.prerequisites must not contain duplicates.")
            lessons.append(
                CourseLesson(
                    lesson_id,
                    lesson_title,
                    source,
                    _text(lesson_raw.get("description", ""), f"{lesson_prefix}.description", errors),
                    duration,
                    lesson_objectives,
                    tags,
                    prerequisites,
                )
            )
        modules.append(CourseModule(module_id, module_title, module_description, tuple(lessons)))

    if not modules:
        errors.append("The course must contain at least one module with one lesson.")

    all_lessons = [lesson for module in modules for lesson in module.lessons]
    known_lesson_ids = {lesson.lesson_id for lesson in all_lessons if lesson.lesson_id}
    dependencies = {
        lesson.lesson_id: set(lesson.prerequisites)
        for lesson in all_lessons
        if lesson.lesson_id
    }
    for lesson in all_lessons:
        for prerequisite in lesson.prerequisites:
            if prerequisite not in known_lesson_ids:
                errors.append(
                    f"Unknown prerequisite '{prerequisite}' for lesson '{lesson.lesson_id}'."
                )
            if prerequisite == lesson.lesson_id:
                errors.append(
                    f"Lesson '{lesson.lesson_id}' cannot be its own prerequisite."
                )

    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def find_cycle(node: str) -> list[str] | None:
        if node in visiting:
            start = stack.index(node)
            return stack[start:] + [node]
        if node in visited:
            return None
        visiting.add(node)
        stack.append(node)
        for prerequisite in dependencies.get(node, set()):
            if prerequisite not in dependencies:
                continue
            cycle = find_cycle(prerequisite)
            if cycle:
                return cycle
        stack.pop()
        visiting.remove(node)
        visited.add(node)
        return None

    for lesson_id in dependencies:
        cycle = find_cycle(lesson_id)
        if cycle:
            errors.append("Prerequisite cycle detected: " + " -> ".join(cycle) + ".")
            break

    manifest = CourseManifest(
        course_id,
        title,
        language,
        level,
        version,
        author,
        description,
        objectives,
        competencies,
        estimated_duration,
        presentation,
        tuple(modules),
    )
    if manifest.duration_minutes == 0:
        warnings.append("No lesson duration_minutes values were provided.")
    return CourseValidation(
        str(manifest_path),
        not errors,
        errors,
        warnings,
        manifest if not errors else None,
        _diagnostics(errors, warnings, project_root, manifest),
    )


def load_course_manifest(path: Path, project_root: Path | None = None) -> CourseValidation:
    """Load and validate a YAML course manifest."""
    project_root = (project_root or path.parent).resolve()
    if not path.is_file():
        error = f"Course manifest not found: {path}"
        return CourseValidation(str(path), False, [error], [], diagnostics=[_diagnostic_for_message(error, project_root, "error")])
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        error = f"Could not read course manifest: {exc}"
        return CourseValidation(str(path), False, [error], [], diagnostics=[_diagnostic_for_message(error, project_root, "error")])
    return _parse_manifest(raw, project_root, path)


def validate_course(path: Path, project_root: Path | None = None) -> CourseValidation:
    """Public validation entry point."""
    return load_course_manifest(path, project_root)


def _labels(language: str) -> dict[str, str]:
    code = language.lower().replace("_", "-").split("-", 1)[0]
    if code == "it":
        return {
            "modules": "Moduli", "lessons": "Lezioni", "duration": "Durata",
            "minutes": "min", "contents": "Indice del corso", "prerequisites": "Prerequisiti",
            "locked": "Bloccata", "available": "Disponibile", "completed": "Completata",
            "mark_complete": "Segna come completata", "mark_incomplete": "Segna come non completata",
            "complete_first": "Completa prima", "lesson_gate": "Questa lezione è bloccata.",
            "goals": "Obiettivi del corso", "competencies": "Competenze", "progress": "Progressi",
            "completed_lessons": "lezioni completate", "remaining": "rimanenti", "percent": "% completato",
        }
    if code == "ja":
        return {
            "modules": "モジュール", "lessons": "レッスン", "duration": "時間",
            "minutes": "分", "contents": "コース目次", "prerequisites": "前提レッスン",
            "locked": "ロック中", "available": "利用可能", "completed": "完了",
            "mark_complete": "レッスンを完了にする", "mark_incomplete": "完了を取り消す",
            "complete_first": "先に完了してください", "lesson_gate": "このレッスンはロックされています。",
            "goals": "コースの目標", "competencies": "身につく力", "progress": "進捗",
            "completed_lessons": "レッスン完了", "remaining": "残り", "percent": "% 完了",
        }
    return {
        "modules": "Modules", "lessons": "Lessons", "duration": "Duration",
        "minutes": "min", "contents": "Course contents", "prerequisites": "Prerequisites",
        "locked": "Locked", "available": "Available", "completed": "Completed",
        "mark_complete": "Mark lesson complete", "mark_incomplete": "Mark as incomplete",
        "complete_first": "Complete first", "lesson_gate": "This lesson is locked.",
        "goals": "Course goals", "competencies": "Skills you will build", "progress": "Progress",
        "completed_lessons": "lessons completed", "remaining": "remaining", "percent": "% complete",
    }


def render_course_html(manifest: CourseManifest, lesson_links: dict[str, str] | None = None) -> str:
    """Render a self-contained course index with dependency-aware progress UI."""
    labels = _labels(manifest.language)
    presentation = manifest.presentation
    lesson_links = lesson_links or {}
    lesson_names = {
        lesson.lesson_id: lesson.title
        for module in manifest.modules
        for lesson in module.lessons
    }
    module_html: list[str] = []
    for module_number, module in enumerate(manifest.modules, start=1):
        lessons = []
        for lesson_number, lesson in enumerate(module.lessons, start=1):
            meta = []
            if lesson.duration_minutes:
                meta.append(f"{lesson.duration_minutes} {html.escape(labels['minutes'])}")
            if lesson.tags:
                meta.append(", ".join(html.escape(tag) for tag in lesson.tags))
            if lesson.prerequisites and presentation.show_prerequisites:
                prerequisite_names = [
                    lesson_names.get(item, item) for item in lesson.prerequisites
                ]
                meta.append(
                    f"{html.escape(labels['prerequisites'])}: "
                    + ", ".join(html.escape(item) for item in prerequisite_names)
                )
            details = (
                f"<p class=\"lesson-description\">{html.escape(lesson.description)}</p>"
                if lesson.description else ""
            )
            lesson_objectives = ""
            if lesson.objectives:
                lesson_objectives = (
                    "<ul class=\"objectives\">"
                    + "".join(f"<li>{html.escape(item)}</li>" for item in lesson.objectives)
                    + "</ul>"
                )
            href = lesson_links.get(lesson.lesson_id, "../" + lesson.source)
            link_label = "Open lesson" if lesson.lesson_id in lesson_links else "Open lesson source"
            link_href = html.escape(href, quote=True)
            prerequisite_ids = html.escape(
                json.dumps(list(lesson.prerequisites), ensure_ascii=False), quote=True
            )
            prerequisite_names_json = html.escape(
                json.dumps(
                    [lesson_names.get(item, item) for item in lesson.prerequisites],
                    ensure_ascii=False,
                ),
                quote=True,
            )
            lessons.append(
                f"<li class=\"lesson\" id=\"lesson-{html.escape(lesson.lesson_id)}\">"
                f"<span class=\"lesson-number\">{module_number}.{lesson_number}</span>"
                f"<div><h3>{html.escape(lesson.title)}</h3>"
                f"<p class=\"lesson-meta\">{' · '.join(meta) if meta else ''}</p>"
                f"{details}{lesson_objectives}"
                f"<a class=\"lesson-link\" href=\"{link_href}\""
                f" data-lesson-id=\"{html.escape(lesson.lesson_id, quote=True)}\""
                f" data-prerequisites=\"{prerequisite_ids}\""
                f" data-prerequisite-names=\"{prerequisite_names_json}\""
                f" data-duration-minutes=\"{lesson.duration_minutes or 0}\">{link_label}</a>"
                f"<button type=\"button\" class=\"lesson-complete\""
                f" data-mark-complete=\"{html.escape(lesson.lesson_id, quote=True)}\""
                f" aria-label=\"{html.escape(labels['mark_complete'], quote=True)}\">"
                f"{html.escape(labels['mark_complete'])}</button>"
                f"<span class=\"lesson-lock\" aria-live=\"polite\"></span></div></li>"
            )
        module_description = (
            f"<p>{html.escape(module.description)}</p>" if module.description else ""
        )
        module_html.append(
            f"<section class=\"module\" id=\"module-{html.escape(module.module_id)}\" "
            f"aria-labelledby=\"module-title-{html.escape(module.module_id)}\">"
            f"<p class=\"eyebrow\">{html.escape(labels['modules'])} {module_number}</p>"
            f"<h2 id=\"module-title-{html.escape(module.module_id)}\">{html.escape(module.title)}</h2>"
            f"{module_description}<ol class=\"lessons\">{''.join(lessons)}</ol></section>"
        )
    duration = (
        f"{manifest.duration_minutes} {html.escape(labels['minutes'])}"
        if manifest.duration_minutes else "Self-paced"
    )
    author = f"<p class=\"author\">{html.escape(manifest.author)}</p>" if manifest.author else ""
    level = f"<span>{html.escape(manifest.level)}</span>" if manifest.level else ""
    goals_html = ""
    if manifest.objectives and presentation.show_objectives:
        goals_html += (
            f"<section class=\"course-meta-section\" aria-labelledby=\"goals-title\">"
            f"<h2 id=\"goals-title\">{html.escape(labels['goals'])}</h2>"
            f"<ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in manifest.objectives)
            + "</ul></section>"
        )
    if manifest.competencies and presentation.show_competencies:
        goals_html += (
            f"<section class=\"course-meta-section\" aria-labelledby=\"competencies-title\">"
            f"<h2 id=\"competencies-title\">{html.escape(labels['competencies'])}</h2>"
            f"<ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in manifest.competencies)
            + "</ul></section>"
        )
    course_key = json.dumps(f"edutex:course:{manifest.course_id}:completed")
    theme_name = presentation.theme
    contents_html = ""
    if presentation.show_contents:
        contents_html = (
            f"<nav class=\"contents\" aria-labelledby=\"contents-title\">"
            f"<h2 id=\"contents-title\">{html.escape(labels['contents'])}</h2><ol>"
            + "".join(
                f"<li><a href=\"#module-{html.escape(module.module_id)}\">"
                f"{html.escape(module.title)}</a></li>"
                for module in manifest.modules
            )
            + "</ol></nav>"
        )
    progress_html = ""
    if presentation.show_progress:
        progress_html = (
            f"<section class=\"progress-card\" aria-labelledby=\"progress-title\">"
            f"<div class=\"progress-heading\"><h2 id=\"progress-title\">{html.escape(labels['progress'])}</h2>"
            f"<span data-course-progress-text aria-live=\"polite\">"
            f"0/{manifest.lesson_count} {html.escape(labels['completed_lessons'])} · "
            f"0{html.escape(labels['percent'])} · {manifest.duration_minutes} "
            f"{html.escape(labels['minutes'])} {html.escape(labels['remaining'])}</span></div>"
            f"<div class=\"progress-track\" role=\"progressbar\" aria-label=\"{html.escape(labels['progress'])}\" "
            f"aria-valuemin=\"0\" aria-valuemax=\"100\" aria-valuenow=\"0\">"
            f"<span data-course-progress-bar></span></div></section>"
        )
    script_labels = json.dumps(
        {
            "locked": labels["locked"],
            "available": labels["available"],
            "completed": labels["completed"],
            "complete_first": labels["complete_first"],
            "completed_lessons": labels["completed_lessons"],
            "remaining": labels["remaining"],
            "percent": labels["percent"],
            "minutes": labels["minutes"],
        },
        ensure_ascii=False,
    )
    script = f"""<script>
(() => {{
  const storageKey = {course_key};
  const labels = {script_labels};
  let completed = new Set();
  try {{ completed = new Set(JSON.parse(localStorage.getItem(storageKey) || "[]")); }}
  catch (error) {{ completed = new Set(); }}
  const save = () => {{
    try {{ localStorage.setItem(storageKey, JSON.stringify([...completed])); }}
    catch (error) {{ /* Static exports may disable browser storage. */ }}
  }};
  const refresh = () => {{
    const allLessons = [...document.querySelectorAll(".lesson-link[data-lesson-id]")];
    const completedItems = allLessons.filter((link) => completed.has(link.dataset.lessonId));
    const completedCount = completedItems.length;
    const total = allLessons.length;
    const totalMinutes = {manifest.duration_minutes};
    const completedMinutes = completedItems.reduce(
      (sum, link) => sum + Number(link.dataset.durationMinutes || 0), 0
    );
    const remainingMinutes = Math.max(0, totalMinutes - completedMinutes);
    const percent = total ? Math.round((completedCount / total) * 100) : 0;
    const progressBar = document.querySelector("[data-course-progress-bar]");
    const progressText = document.querySelector("[data-course-progress-text]");
    if (progressBar) progressBar.style.width = `${{percent}}%`;
    if (progressBar) progressBar.setAttribute("aria-valuenow", String(percent));
    if (progressText) progressText.textContent = `${{completedCount}}/${{total}} ${{labels.completed_lessons}} · ${{percent}}${{labels.percent}} · ${{remainingMinutes}} ${{labels.minutes}} ${{labels.remaining}}`;
    document.querySelectorAll(".lesson-link[data-lesson-id]").forEach((link) => {{
      const prerequisites = JSON.parse(link.dataset.prerequisites || "[]");
      const names = JSON.parse(link.dataset.prerequisiteNames || "[]");
      const missing = prerequisites.filter((item) => !completed.has(item));
      const locked = missing.length > 0;
      link.classList.toggle("is-locked", locked);
      link.classList.toggle("is-completed", completed.has(link.dataset.lessonId));
      link.setAttribute("aria-disabled", String(locked));
      const status = link.parentElement.querySelector(".lesson-lock");
      if (status) {{
        status.textContent = locked
          ? `${{labels.locked}} - ${{labels.complete_first}}: ${{names.filter((_, i) => missing.includes(prerequisites[i])).join(", ")}}`
          : (completed.has(link.dataset.lessonId) ? labels.completed : labels.available);
        status.classList.toggle("is-visible", true);
      }}
    }});
  }};
  document.querySelectorAll(".lesson-link").forEach((link) => link.addEventListener("click", (event) => {{
    const prerequisites = JSON.parse(link.dataset.prerequisites || "[]");
    if (prerequisites.some((item) => !completed.has(item))) event.preventDefault();
  }}));
  document.querySelectorAll("[data-mark-complete]").forEach((button) => button.addEventListener("click", () => {{
    completed.add(button.dataset.markComplete); save(); refresh();
  }}));
  refresh();
}})();
</script>"""
    return f"""<!doctype html>
<html lang="{html.escape(manifest.language)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="generator" content="EduTeX Course Management">
<meta name="edutex-course-theme" content="{html.escape(theme_name, quote=True)}">
<title>{html.escape(manifest.title)}</title>
<style>
.skip-link {{ position:absolute; left:1rem; top:-4rem; z-index:10; padding:.55rem .8rem; background:var(--ink); color:#fff; font-weight:800; }}
.skip-link:focus-visible {{ top:1rem; }}
:root {{ color-scheme: light; --ink:{presentation.ink}; --muted:{presentation.muted}; --line:{presentation.muted}55; --accent:{presentation.accent}; --accent-secondary:{presentation.accent_secondary}; --paper:{presentation.background}; --card:{presentation.surface}; }}
* {{ box-sizing:border-box; }} body {{ margin:0; background:var(--paper); color:var(--ink); font-family:Inter,"Segoe UI",Arial,sans-serif; line-height:1.6; }}
main {{ max-width:980px; margin:0 auto; padding:2rem 1.1rem 5rem; }}
.hero {{ background:var(--ink); color:#fff; padding:clamp(2rem,6vw,5rem); border-bottom:8px solid var(--accent); }}
.kicker,.eyebrow {{ color:var(--accent); text-transform:uppercase; letter-spacing:.12em; font-weight:800; font-size:.76rem; }}
h1 {{ max-width:760px; margin:.35rem 0 .8rem; font-size:clamp(2.25rem,6vw,4.7rem); line-height:1.02; letter-spacing:-.045em; }}
.author {{ color:#c9d7eb; margin:0; }} .summary {{ display:flex; gap:1.5rem; flex-wrap:wrap; margin-top:2rem; color:#dce8f7; }}
.summary strong {{ display:block; color:#fff; font-size:1.55rem; }} .contents {{ margin:2rem 0; background:var(--card); border-left:5px solid var(--accent); padding:1.1rem 1.4rem; }}
.contents h2 {{ margin-top:0; font-size:1rem; }} .contents a {{ color:var(--accent); font-weight:700; }}
.progress-card,.course-meta-section {{ background:var(--card); border:1px solid var(--line); padding:1.1rem 1.4rem; margin:1.5rem 0; }}
.progress-heading {{ display:flex; gap:1rem; justify-content:space-between; align-items:baseline; flex-wrap:wrap; }}
.progress-heading h2,.course-meta-section h2 {{ margin:0 0 .65rem; font-size:1.15rem; }} .progress-heading span {{ color:var(--muted); font-size:.9rem; }}
.progress-track {{ height:.75rem; overflow:hidden; border-radius:999px; background:#e3e9f1; }} .progress-track span {{ display:block; width:0; height:100%; background:var(--accent-secondary); transition:width .25s ease; }}
.course-meta-section ul {{ margin:.2rem 0 0; color:var(--muted); }}
.module {{ background:var(--card); margin:1.5rem 0; padding:1.5rem; border:1px solid var(--line); }} .module h2 {{ margin:.2rem 0 .5rem; font-size:1.8rem; }}
.module > p:not(.eyebrow) {{ color:var(--muted); }} .lessons {{ list-style:none; padding:0; margin:1.25rem 0 0; }}
.lesson {{ display:grid; grid-template-columns:3.2rem 1fr; gap:1rem; padding:1rem 0; border-top:1px solid var(--line); }} .lesson-number {{ color:var(--accent); font-weight:800; }}
.lesson h3 {{ margin:0; font-size:1.12rem; }} .lesson-meta {{ color:var(--muted); font-size:.9rem; margin:.15rem 0 .4rem; }} .lesson-description {{ margin:.3rem 0; }}
.lesson a {{ color:var(--accent); font-weight:700; }} .lesson-link.is-locked {{ color:var(--muted); cursor:not-allowed; opacity:.65; }} .lesson-link.is-completed {{ color:#26734d; }}
.lesson-lock {{ display:block; color:var(--muted); font-size:.82rem; }} .lesson-lock.is-visible {{ margin-top:.25rem; }} .objectives {{ margin:.5rem 0; color:var(--muted); }}
:focus-visible {{ outline:3px solid #f0bf76; outline-offset:3px; }}
@media (max-width:600px) {{ .lesson {{ grid-template-columns:2rem 1fr; gap:.6rem; }} .module {{ padding:1rem; }} }}
</style>
</head>
<body><a class="skip-link" href="#course-content">Skip to course content</a><main id="course-content" tabindex="-1" aria-labelledby="course-title">
<header class="hero"><p class="kicker">EduTeX course</p><h1 id="course-title">{html.escape(manifest.title)}</h1>{author}
<div class="summary"><div><strong>{manifest.module_count}</strong>{html.escape(labels['modules'])}</div><div><strong>{manifest.lesson_count}</strong>{html.escape(labels['lessons'])}</div><div><strong>{html.escape(duration)}</strong>{html.escape(labels['duration'])}</div>{f'<div><strong>{level}</strong>Level</div>' if level else ''}</div></header>
{contents_html}
{progress_html}
{goals_html}<article>{''.join(module_html)}</article>
</main>{script}</body></html>"""


def _latex_escape(value: str) -> str:
    replacements = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}"}
    return "".join(replacements.get(char, char) for char in value)


def _pdf_language_tag(language: str) -> str:
    """Return a stable BCP 47-style language tag for PDF metadata."""
    normalized = language.strip().replace("_", "-")
    if not normalized:
        return "en-US"
    parts = [part for part in normalized.split("-") if part]
    if not parts:
        return "en-US"
    base = parts[0].lower()
    default_regions = {
        "de": "DE",
        "en": "US",
        "es": "ES",
        "fr": "FR",
        "it": "IT",
        "ja": "JP",
        "ko": "KR",
        "pt": "BR",
        "zh": "CN",
    }
    if len(parts) == 1 and base in default_regions:
        return f"{base}-{default_regions[base]}"
    normalized_parts = [base]
    for part in parts[1:]:
        if len(part) == 2 and part.isalpha():
            normalized_parts.append(part.upper())
        elif len(part) == 4 and part.isalpha():
            normalized_parts.append(part.title())
        else:
            normalized_parts.append(part)
    return "-".join(normalized_parts)


def render_course_latex(manifest: CourseManifest) -> str:
    """Render a printable course roadmap as LaTeX source."""
    cjk = manifest.language.lower().split("-", 1)[0] in {"ja", "zh", "ko"}
    if cjk:
        packages = r"\usepackage{fontspec}" + "\n" + r"\usepackage{xeCJK}"
    else:
        # cmap gives pdfLaTeX a usable ToUnicode map for copy/search operations.
        packages = "\n".join(
            [r"\usepackage{cmap}", r"\usepackage[utf8]{inputenc}", r"\usepackage[T1]{fontenc}"]
        )
    title = _latex_escape(manifest.title)
    author = _latex_escape(manifest.author or "EduTeX")
    subject = _latex_escape(manifest.description or "EduTeX course roadmap")
    language_tag = _pdf_language_tag(manifest.language)
    lines = [
        r"\documentclass[12pt,a4paper]{article}", "", packages,
        r"\usepackage[margin=25mm]{geometry}", r"\usepackage{xcolor}", r"\usepackage{hyperref}",
        r"\definecolor{CourseBlue}{HTML}{2A4A7F}",
        # Keep text searchable/copyable and make the document outline explicit.
        r"\ifdefined\pdfgentounicode",
        r"  \IfFileExists{glyphtounicode.tex}{\input glyphtounicode}{}",
        r"  \pdfgentounicode=1",
        r"\fi",
        (r"\hypersetup{colorlinks=true,linkcolor=CourseBlue,urlcolor=CourseBlue,"
         r"unicode=true,bookmarks=true,bookmarksopen=true,bookmarksnumbered=true,"
         f"pdftitle={{{title}}},pdfauthor={{{author}}},"
         f"pdfsubject={{{subject}}},pdflang={{{language_tag}}}}}"),
        r"\title{" + title + "}", r"\author{" + author + "}", r"\date{}", "",
        r"\begin{document}", r"\maketitle", r"\tableofcontents", "",
    ]
    if manifest.description:
        lines.extend([_latex_escape(manifest.description), ""])
    for index, module in enumerate(manifest.modules, start=1):
        lines.extend([r"\section{" + _latex_escape(module.title) + "}"])
        if module.description:
            lines.append(_latex_escape(module.description))
        lines.append(r"\begin{description}")
        for lesson in module.lessons:
            meta = []
            if lesson.duration_minutes:
                meta.append(f"{lesson.duration_minutes} min")
            if lesson.tags:
                meta.append(", ".join(lesson.tags))
            label = _latex_escape(lesson.title)
            detail = _latex_escape(lesson.description)
            if meta:
                detail = (detail + " " if detail else "") + "(" + "; ".join(meta) + ")"
            lines.append(r"\item[" + label + r"] " + detail + r"\newline\texttt{" + _latex_escape(lesson.source) + "}")
        lines.extend([r"\end{description}", ""])
    lines.append(r"\end{document}")
    return "\n".join(lines) + "\n"


def _compile_pdf(tex_path: Path, output_dir: Path, output_file: str, language: str) -> Path:
    code = language.lower().split("-", 1)[0]
    if code in {"ja", "zh", "ko"}:
        if shutil.which("latexmk") and shutil.which("xelatex"):
            command = ["latexmk", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", f"-outdir={output_dir}", str(tex_path)]
        elif shutil.which("xelatex"):
            command = ["xelatex", "-interaction=nonstopmode", "-halt-on-error", f"-output-directory={output_dir}", str(tex_path)]
        else:
            raise CourseBuildError("CJK PDF output requires xelatex or latexmk with xelatex.")
    elif shutil.which("latexmk"):
        command = ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", f"-outdir={output_dir}", str(tex_path)]
    elif shutil.which("pdflatex"):
        command = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", f"-output-directory={output_dir}", str(tex_path)]
    else:
        raise CourseBuildError("PDF output requires latexmk or pdflatex.")
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CourseBuildError(f"PDF compilation failed: {exc}") from exc
    if result.returncode != 0:
        raise CourseBuildError((result.stderr or result.stdout)[-3000:])
    pdf_path = output_dir / f"{output_file}.pdf"
    if not pdf_path.is_file():
        raise CourseBuildError(f"PDF compiler completed but did not create {pdf_path}.")
    return pdf_path


def _clean_stale_lesson_pages(output_dir: Path, expected_lesson_ids: set[str]) -> None:
    """Remove obsolete generated lesson pages from the owned output folder.

    Course HTML builds own only ``output/lessons/*.html``.  Cleanup is limited
    to that immediate directory and to filenames matching the validated lesson
    ID syntax, so unrelated files elsewhere in the project are untouched.
    """
    lesson_dir = output_dir / "lessons"
    if not lesson_dir.is_dir():
        return
    for page in lesson_dir.glob("*.html"):
        if not page.is_file() or not _ID_RE.fullmatch(page.stem):
            continue
        if page.stem in expected_lesson_ids:
            continue
        try:
            source = page.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        generated_marker = '<meta name="generator" content="EduTeX">'
        navigation_marker = 'aria-label="Course navigation"'
        if generated_marker in source and navigation_marker in source:
            page.unlink()


def build_course(
    manifest_path: Path,
    project_root: Path,
    output_format: str,
    output_path: Path | None = None,
    lesson_builder: Callable[[CourseManifest, CourseLesson, int, int], Path] | None = None,
) -> Path:
    """Validate and render a course index in HTML, LaTeX, or PDF format.

    When ``lesson_builder`` is supplied, HTML builds also render every lesson
    through the caller's official lesson pipeline before writing the index.
    The callback receives the manifest, lesson, module number, and lesson
    number, and must return the generated lesson path.
    """
    report = validate_course(manifest_path, project_root)
    if not report.valid or report.manifest is None:
        raise CourseBuildError("Course manifest is invalid: " + " ".join(report.errors))
    output_format = output_format.lower()
    if output_format not in {"html", "latex", "pdf"}:
        raise CourseBuildError("Course output format must be html, latex, or pdf.")
    output_dir = project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    if output_path is None:
        output_file = "course"
        destination = output_dir / f"{output_file}.{output_format if output_format != 'latex' else 'tex'}"
    else:
        destination = output_path if output_path.is_absolute() else project_root / output_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        output_file = destination.stem
    if output_format == "html":
        lesson_links: dict[str, str] = {}
        if lesson_builder is not None:
            expected_lesson_ids = {
                lesson.lesson_id
                for module in report.manifest.modules
                for lesson in module.lessons
            }
            _clean_stale_lesson_pages(output_dir, expected_lesson_ids)
            for module_number, module in enumerate(report.manifest.modules, start=1):
                for lesson_number, lesson in enumerate(module.lessons, start=1):
                    try:
                        generated = lesson_builder(
                            report.manifest,
                            lesson,
                            module_number,
                            lesson_number,
                        )
                    except Exception as exc:
                        raise CourseBuildError(
                            f"Could not build lesson '{lesson.lesson_id}': {exc}"
                        ) from exc
                    try:
                        lesson_links[lesson.lesson_id] = generated.relative_to(
                            destination.parent
                        ).as_posix()
                    except ValueError as exc:
                        raise CourseBuildError(
                            f"Generated lesson '{lesson.lesson_id}' is outside the course output directory."
                        ) from exc
        destination.write_text(
            render_course_html(report.manifest, lesson_links),
            encoding="utf-8",
        )
        return destination
    tex_path = destination if output_format == "latex" else destination.with_suffix(".tex")
    tex_path.write_text(render_course_latex(report.manifest), encoding="utf-8")
    if output_format == "latex":
        return tex_path
    return _compile_pdf(tex_path, tex_path.parent, tex_path.stem, report.manifest.language)
