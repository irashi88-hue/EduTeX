"""EduTeX configuration loader with concise, actionable diagnostics."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from edutex.configuration.schema import EduTexConfig
from edutex.core.errors import ConfigurationError


def _format_validation_error(error: ValidationError) -> str:
    """Convert Pydantic's technical error tree into readable bullet points."""
    messages: list[str] = []
    for item in error.errors():
        location = ".".join(str(part) for part in item.get("loc", ())) or "configuration"
        message = str(item.get("msg", "invalid value"))
        messages.append(f"- {location}: {message}")
    return "\n".join(messages)


def load_config(config_path: Path) -> EduTexConfig:
    """Load and validate a project configuration file."""
    if not config_path.is_file():
        raise ConfigurationError(
            f"Configuration file not found: {config_path}. "
            "Run the command from the project root or check --config."
        )

    try:
        raw_text = config_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ConfigurationError(
            f"Configuration file '{config_path}' is not valid UTF-8. "
            "Save it as UTF-8 and try again."
        ) from exc
    except OSError as exc:
        raise ConfigurationError(
            f"Configuration file '{config_path}' could not be read: {exc}"
        ) from exc

    try:
        raw = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        location = f" at line {mark.line + 1}" if mark is not None else ""
        raise ConfigurationError(
            f"Invalid YAML in configuration file '{config_path}'{location}: {exc}"
        ) from exc

    if raw is None:
        raise ConfigurationError(
            f"Configuration file '{config_path}' is empty. "
            "Add the edutex, knowledge, theme, and layout sections."
        )
    if not isinstance(raw, dict):
        raise ConfigurationError(
            f"Configuration file '{config_path}' must contain a YAML mapping. "
            "Check the indentation and the top-level sections."
        )

    try:
        return EduTexConfig.model_validate(raw)
    except ValidationError as exc:
        details = _format_validation_error(exc)
        raise ConfigurationError(
            f"Configuration validation failed for '{config_path}':\n{details}"
        ) from exc
