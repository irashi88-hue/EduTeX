"""EduTeX Knowledge Model loader with actionable front matter diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from edutex.core.errors import KnowledgeError


@dataclass
class KnowledgeModelMeta:
    id: str
    title: str
    language: str
    level: str
    version: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    author: str = ""

    REQUIRED_FIELDS = ("id", "title", "language", "level", "version")


def load_knowledge_model(path: Path) -> tuple[KnowledgeModelMeta, str]:
    """Load a Markdown Knowledge Model and validate its YAML front matter."""
    if not path.is_file():
        raise KnowledgeError(
            f"Knowledge Model file not found: {path}. "
            "Check knowledge.model in edutex.config.yaml."
        )

    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise KnowledgeError(
            f"Knowledge Model '{path}' is not valid UTF-8. "
            "Save the Markdown file as UTF-8 and try again."
        ) from exc
    except OSError as exc:
        raise KnowledgeError(f"Knowledge Model '{path}' could not be read: {exc}") from exc

    return _split_frontmatter(raw, path)


def _split_frontmatter(raw: str, path: Path) -> tuple[KnowledgeModelMeta, str]:
    lines = raw.splitlines()
    if not lines or lines[0].lstrip("\ufeff").strip() != "---":
        raise KnowledgeError(
            f"Knowledge Model '{path}' is missing YAML front matter at line 1. "
            "The file must begin with '---'."
        )

    closing_index = next(
        (index for index in range(1, len(lines)) if lines[index].strip() == "---"),
        None,
    )
    if closing_index is None:
        raise KnowledgeError(
            f"Knowledge Model '{path}' has an unclosed YAML front matter block "
            "starting at line 1. Add a closing '---'."
        )

    frontmatter_raw = "\n".join(lines[1:closing_index]).strip()
    body = "\n".join(lines[closing_index + 1:]).strip()

    try:
        data = yaml.safe_load(frontmatter_raw)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        line = mark.line + 2 if mark is not None else 2
        raise KnowledgeError(
            f"Knowledge Model '{path}' has invalid YAML front matter at line {line}: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise KnowledgeError(
            f"Knowledge Model '{path}' has invalid front matter: "
            "the content between the '---' markers must be a YAML mapping."
        )

    missing = [field_name for field_name in KnowledgeModelMeta.REQUIRED_FIELDS if field_name not in data]
    if missing:
        fields = ", ".join(f"'{field_name}'" for field_name in missing)
        raise KnowledgeError(
            f"Knowledge Model '{path}' is missing required front matter fields: {fields}. "
            "Add them between the opening and closing '---' markers."
        )

    values: dict[str, str] = {}
    for field_name in KnowledgeModelMeta.REQUIRED_FIELDS:
        value = data[field_name]
        if value is None or not str(value).strip():
            raise KnowledgeError(
                f"Knowledge Model '{path}' has an empty required front matter field "
                f"'{field_name}'. Set a non-empty value at line 2 or later."
            )
        values[field_name] = str(value).strip()

    tags_raw = data.get("tags", [])
    if tags_raw is None:
        tags_raw = []
    if not isinstance(tags_raw, list):
        raise KnowledgeError(
            f"Knowledge Model '{path}' has an invalid 'tags' field. "
            "Use a YAML list, for example: tags: [grammar, A1]."
        )
    tags = [str(tag).strip() for tag in tags_raw]
    if any(not tag for tag in tags):
        raise KnowledgeError(
            f"Knowledge Model '{path}' contains an empty tag. "
            "Remove it or provide a tag name."
        )

    meta = KnowledgeModelMeta(
        id=values["id"],
        title=values["title"],
        language=values["language"],
        level=values["level"],
        version=values["version"],
        description=str(data.get("description") or "").strip(),
        tags=tags,
        author=str(data.get("author") or "").strip(),
    )
    return meta, body
