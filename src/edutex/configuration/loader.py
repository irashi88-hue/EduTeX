"""EduTeX configuration loader with concise, actionable diagnostics."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
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


def _validate_profile_override(
    value: Mapping[object, object],
    profile_name: str,
    path: str = "",
    model_type=EduTexConfig,
) -> None:
    """Reject malformed or unknown profile fields before selection."""
    fields = getattr(model_type, "model_fields", {})
    for key, nested in value.items():
        location = f"{path}.{key}" if path else str(key)
        if not isinstance(key, str):
            raise ConfigurationError(
                f"Configuration profile '{profile_name}.{path}' contains a non-string key."
            )
        if key not in fields:
            raise ConfigurationError(
                f"Configuration profile '{profile_name}' contains unknown field '{location}'."
            )
        if isinstance(nested, Mapping):
            nested_model = fields[key].annotation
            if not isinstance(nested_model, type) or not hasattr(nested_model, "model_fields"):
                raise ConfigurationError(
                    f"Configuration profile field '{profile_name}.{location}' must not be a mapping."
                )
            _validate_profile_override(
                nested,
                profile_name,
                location,
                nested_model,
            )


def _deep_merge(
    base: Mapping[str, object],
    override: Mapping[str, object],
    *,
    path: str = "",
) -> dict[str, object]:
    """Return a recursive mapping merge without mutating either input."""
    merged = deepcopy(dict(base))
    for key, value in override.items():
        if not isinstance(key, str):
            location = path or "configuration"
            raise ConfigurationError(
                f"Configuration profile override at '{location}' contains a non-string key."
            )
        current = merged.get(key)
        if isinstance(current, Mapping) and isinstance(value, Mapping):
            child_path = f"{path}.{key}" if path else key
            merged[key] = _deep_merge(current, value, path=child_path)
        else:
            merged[key] = deepcopy(value)
    return merged


def _resolve_profile(
    raw: Mapping[str, object],
    profile: str | None,
) -> dict[str, object]:
    """Select a named profile and merge it into an independent base mapping."""
    base = dict(raw)
    definitions = base.pop("profiles", {})
    if not isinstance(definitions, Mapping):
        raise ConfigurationError("Configuration 'profiles' must be a YAML mapping.")

    for name, overrides in definitions.items():
        if not isinstance(name, str) or not name.strip() or name != name.strip():
            raise ConfigurationError(
                "Configuration profile names must be non-empty strings without surrounding whitespace."
            )
        if not isinstance(overrides, Mapping):
            raise ConfigurationError(
                f"Configuration profile '{name}' must be a YAML mapping."
            )
        _validate_profile_override(overrides, name)

    if profile is None:
        return deepcopy(base)
    if not isinstance(profile, str) or not profile.strip() or profile != profile.strip():
        raise ConfigurationError(
            "Configuration profile selection must be a non-empty name without surrounding whitespace."
        )
    if profile not in definitions:
        available = ", ".join(sorted(str(name) for name in definitions)) or "none"
        raise ConfigurationError(
            f"Unknown configuration profile '{profile}'. Available profiles: {available}."
        )
    return _deep_merge(base, definitions[profile])


def load_config(
    config_path: Path,
    *,
    profile: str | None = None,
) -> EduTexConfig:
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
        effective_raw = _resolve_profile(raw, profile)
        return EduTexConfig.model_validate(effective_raw)
    except ValidationError as exc:
        details = _format_validation_error(exc)
        raise ConfigurationError(
            f"Configuration validation failed for '{config_path}':\n{details}"
        ) from exc
