"""
EduTeX Knowledge Loader
Component: Knowledge (COMP-KNOW-001)

Reads a Knowledge Model source file (.md) and returns:
  - validated YAML frontmatter (KnowledgeModelMeta)
  - raw body text (to be parsed by the shortcode parser)

This module is responsible for the file I/O and frontmatter validation layer.
It does NOT parse shortcodes — that is the parser's responsibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from edutex.core.errors import KnowledgeError


@dataclass
class KnowledgeModelMeta:
    """
    Validated YAML frontmatter of a Knowledge Model.
    Exposed through KNOW-002 (Knowledge Model Contract).
    """
    id:          str
    title:       str
    language:    str
    level:       str
    version:     str
    description: str = ""
    tags:        list[str] = field(default_factory=list)
    author:      str = ""

    REQUIRED_FIELDS = ("id", "title", "language", "level", "version")


def load_knowledge_model(path: Path) -> tuple[KnowledgeModelMeta, str]:
    """
    Load a Knowledge Model source file.

    Args:
        path: Path to the .md Knowledge Model file.

    Returns:
        A tuple of (KnowledgeModelMeta, body_text).

    Raises:
        KnowledgeError: If the file cannot be read, frontmatter is missing
                        or required fields are absent (CC-003).
    """
    if not path.exists():
        raise KnowledgeError(f"Knowledge Model file not found: {path}")

    raw = path.read_text(encoding="utf-8")

    meta, body = _split_frontmatter(raw, path)
    return meta, body


def _split_frontmatter(raw: str, path: Path) -> tuple[KnowledgeModelMeta, str]:
    """
    Split the raw file content into frontmatter and body.
    The file must start with --- and contain a closing ---.
    """
    if not raw.startswith("---"):
        raise KnowledgeError(
            f"Knowledge Model '{path}' is missing the YAML frontmatter block. "
            f"The file must begin with '---'."
        )

    # Find closing ---
    end = raw.find("\n---", 3)
    if end == -1:
        raise KnowledgeError(
            f"Knowledge Model '{path}' has an unclosed YAML frontmatter block."
        )

    frontmatter_raw = raw[3:end].strip()
    body = raw[end + 4:].strip()  # skip the closing ---\n

    try:
        data = yaml.safe_load(frontmatter_raw)
    except yaml.YAMLError as exc:
        raise KnowledgeError(
            f"Knowledge Model '{path}' has invalid YAML frontmatter: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise KnowledgeError(
            f"Knowledge Model '{path}' frontmatter must be a YAML mapping."
        )

    # Validate required fields
    missing = [f for f in KnowledgeModelMeta.REQUIRED_FIELDS if f not in data]
    if missing:
        raise KnowledgeError(
            f"Knowledge Model '{path}' is missing required frontmatter fields: "
            + ", ".join(f"'{f}'" for f in missing)
        )

    meta = KnowledgeModelMeta(
        id=str(data["id"]),
        title=str(data["title"]),
        language=str(data["language"]),
        level=str(data["level"]),
        version=str(data["version"]),
        description=str(data.get("description", "")),
        tags=list(data.get("tags", [])),
        author=str(data.get("author", "")),
    )

    return meta, body
