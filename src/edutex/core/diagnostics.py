"""Shared serialization helpers for structured diagnostics."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, is_dataclass
from typing import Any


def serialize_diagnostic(diagnostic: object) -> dict[str, Any]:
    """Convert one supported diagnostic object to a JSON-ready mapping."""
    to_dict = getattr(diagnostic, "to_dict", None)
    if callable(to_dict):
        value = to_dict()
    elif is_dataclass(diagnostic) and not isinstance(diagnostic, type):
        value = asdict(diagnostic)
    elif isinstance(diagnostic, Mapping):
        value = dict(diagnostic)
    else:
        raise TypeError(
            "Diagnostic must be a dataclass, mapping, or expose to_dict()."
        )

    if not isinstance(value, Mapping):
        raise TypeError("Diagnostic to_dict() must return a mapping.")

    return {str(key): item for key, item in value.items()}


def serialize_diagnostics(
    diagnostics: Iterable[object],
) -> list[dict[str, Any]]:
    """Convert diagnostics in input order without changing their contracts."""
    return [serialize_diagnostic(diagnostic) for diagnostic in diagnostics]


def format_diagnostics_text(diagnostics: Iterable[object]) -> str:
    """Format structured diagnostics for the human-readable CLI channel."""
    lines = ["Extension diagnostics:"]
    for diagnostic in serialize_diagnostics(diagnostics):
        lines.append(
            "- extension_id={extension_id}; point_id={point_id}; "
            "phase={phase}; message={message}".format(**diagnostic)
        )
    return "\n".join(lines)
