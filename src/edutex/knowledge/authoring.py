"""Authoring validation for Knowledge Model source files."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from edutex.core.errors import KnowledgeError
from edutex.knowledge.loader import load_knowledge_model
from edutex.knowledge.shortcode_lint import ShortcodeLinter, format_text


@dataclass
class AuthoringReport:
    """Stable authoring validation report for CLI and tooling consumers."""

    path: str
    valid: bool
    errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, str] | None = None

    @property
    def diagnostics(self) -> list[dict[str, Any]]:
        """Return errors followed by warnings in stable order."""
        return [*self.errors, *self.warnings]

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "path": self.path,
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "diagnostics": self.diagnostics,
        }
        if self.metadata is not None:
            result["metadata"] = dict(self.metadata)
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_text(self) -> str:
        lines: list[str] = []
        for item in self.diagnostics:
            severity = str(item.get("severity", "error")).upper()
            code = item.get("code", "KM000")
            message = item.get("message", "")
            location = str(item.get("path", self.path))
            line = item.get("line")
            if line is not None:
                location += f":{line}"
            lines.append(f"{severity} {location} [{code}] {message}")
            suggestion = item.get("suggestion")
            if suggestion:
                lines.append(f"Suggestion: {suggestion}")
        if not lines:
            lines.append(f"OK {self.path}")
            lines.append("Knowledge Model frontmatter and shortcode authoring are valid.")
        lines.append(f"{len(self.errors)} errors, {len(self.warnings)} warnings.")
        return "\n".join(lines)


def _frontmatter_error(path: Path, exc: Exception) -> dict[str, object]:
    return {
        "severity": "error",
        "code": "KM001",
        "message": str(exc),
        "path": str(path),
    }


def _source_error(path: Path, exc: Exception) -> dict[str, object]:
    return {
        "severity": "error",
        "code": "KM002",
        "message": str(exc),
        "path": str(path),
    }


def validate_authoring(path: Path) -> AuthoringReport:
    """Validate frontmatter and shortcode authoring without changing lint."""
    source_path = path.expanduser().resolve()
    if not source_path.is_file():
        error = _source_error(
            source_path,
            KnowledgeError(f"Knowledge Model file not found: {source_path}"),
        )
        return AuthoringReport(str(source_path), False, errors=[error])

    errors: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []
    metadata: dict[str, str] | None = None
    try:
        meta, _ = load_knowledge_model(source_path)
        metadata = {
            "id": meta.id,
            "title": meta.title,
            "language": meta.language,
            "level": meta.level,
            "version": meta.version,
        }
    except KnowledgeError as exc:
        errors.append(_frontmatter_error(source_path, exc))

    try:
        lint_report = ShortcodeLinter().lint_file(source_path)
    except (OSError, UnicodeError) as exc:
        errors.append(_source_error(source_path, exc))
    else:
        errors.extend(item.to_dict() for item in lint_report.errors)
        warnings.extend(item.to_dict() for item in lint_report.warnings)

    return AuthoringReport(
        str(source_path),
        not errors,
        errors=errors,
        warnings=warnings,
        metadata=metadata,
    )
