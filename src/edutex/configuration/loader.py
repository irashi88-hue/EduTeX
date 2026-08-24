"""
EduTeX Configuration Loader
Component: Configuration (COMP-CONFIG-001)
Contracts: CFG-001 (Configuration Contract), CFG-002 (Configuration Schema Contract)

Loads and validates the edutex.config.yaml file.
Exposes a validated EduTexConfig instance to all consuming components.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from edutex.configuration.schema import EduTexConfig
from edutex.core.errors import ConfigurationError


def load_config(config_path: Path) -> EduTexConfig:
    """
    Load and validate the EduTeX project configuration from a YAML file.

    Args:
        config_path: Path to the edutex.config.yaml file.

    Returns:
        A fully validated EduTexConfig instance (CFG-001).

    Raises:
        ConfigurationError: If the file cannot be read or validation fails (CC-003).
    """
    if not config_path.exists():
        raise ConfigurationError(f"Configuration file not found: {config_path}")

    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"Failed to parse configuration file: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigurationError("Configuration file must be a YAML mapping.")

    try:
        config = EduTexConfig.model_validate(raw)
    except ValidationError as exc:
        raise ConfigurationError(f"Configuration validation failed:\n{exc}") from exc

    return config
