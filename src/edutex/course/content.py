"""Load all lesson ContentModels declared by a course manifest."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from edutex.course.service import CourseBuildError, CourseManifest, validate_course
from edutex.knowledge.loader import KnowledgeModelMeta, load_knowledge_model
from edutex.knowledge.models import ContentModel
from edutex.knowledge.service import parse_content_model


@dataclass(frozen=True)
class CourseContentEntry:
    """One ordered lesson and its processed ContentModel."""

    lesson_id: str
    title: str
    source_path: Path
    meta: KnowledgeModelMeta
    content: ContentModel


class CourseContentCollection:
    """Read-only ordered collection of lesson content indexed by lesson ID."""

    def __init__(self, entries: tuple[CourseContentEntry, ...]) -> None:
        ids = [entry.lesson_id for entry in entries]
        if len(ids) != len(set(ids)):
            raise ValueError("Course content lesson IDs must be unique.")
        self._entries = tuple(deepcopy(entries))
        self._by_id = {entry.lesson_id: entry for entry in self._entries}

    @property
    def ids(self) -> tuple[str, ...]:
        """Return lesson IDs in manifest order."""
        return tuple(entry.lesson_id for entry in self._entries)

    def all(self) -> list[CourseContentEntry]:
        """Return all entries in manifest order as detached copies."""
        return deepcopy(list(self._entries))

    def get(self, lesson_id: str) -> CourseContentEntry | None:
        """Return one detached entry by lesson ID, or ``None``."""
        if not isinstance(lesson_id, str):
            raise TypeError("lesson_id must be a string.")
        entry = self._by_id.get(lesson_id)
        return deepcopy(entry) if entry is not None else None

    def __getitem__(self, lesson_id: str) -> CourseContentEntry:
        entry = self.get(lesson_id)
        if entry is None:
            raise KeyError(lesson_id)
        return entry

    def __contains__(self, lesson_id: object) -> bool:
        return lesson_id in self._by_id

    def __len__(self) -> int:
        return len(self._entries)


def load_course_content(
    manifest_path: Path,
    project_root: Path | None = None,
) -> CourseContentCollection:
    """Validate a course and process every linked Knowledge Model in order."""
    project_root = (project_root or manifest_path.parent).resolve()
    report = validate_course(manifest_path, project_root)
    if not report.valid or report.manifest is None:
        message = "Course manifest is invalid: " + " ".join(report.errors)
        raise CourseBuildError(message)

    entries: list[CourseContentEntry] = []
    for module in report.manifest.modules:
        for lesson in module.lessons:
            source_path = (project_root / lesson.source).resolve()
            try:
                meta, body = load_knowledge_model(source_path)
                content = parse_content_model(body)
            except Exception as exc:
                raise CourseBuildError(
                    f"Could not load lesson '{lesson.lesson_id}': {exc}"
                ) from exc
            entries.append(
                CourseContentEntry(
                    lesson_id=lesson.lesson_id,
                    title=lesson.title,
                    source_path=source_path,
                    meta=meta,
                    content=content,
                )
            )
    return CourseContentCollection(tuple(entries))
