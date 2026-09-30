def test_public_configuration_api_exports_contract():
    import edutex.configuration as public_configuration
    from edutex.configuration.loader import load_config
    from edutex.configuration.schema import (
        BuildConfig,
        EduTexConfig,
        EduTexVersionConfig,
        ExtensionsConfig,
        KnowledgeConfig,
        LayoutConfig,
        LogLevel,
        LoggingConfig,
        OutputFormat,
        ThemeConfig,
    )

    expected = {
        "BuildConfig": BuildConfig,
        "EduTexConfig": EduTexConfig,
        "EduTexVersionConfig": EduTexVersionConfig,
        "ExtensionsConfig": ExtensionsConfig,
        "KnowledgeConfig": KnowledgeConfig,
        "LayoutConfig": LayoutConfig,
        "LogLevel": LogLevel,
        "LoggingConfig": LoggingConfig,
        "OutputFormat": OutputFormat,
        "ThemeConfig": ThemeConfig,
        "load_config": load_config,
    }

    for name, expected_value in expected.items():
        assert getattr(public_configuration, name) is expected_value
        assert name in public_configuration.__all__


"""
Unit tests for the Configuration component.
Component: Configuration (COMP-CONFIG-001)
"""

import textwrap
from pathlib import Path

import pytest

from edutex.configuration.loader import load_config
from edutex.configuration.schema import EduTexConfig, OutputFormat
from edutex.core.errors import ConfigurationError


def write_config(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "edutex.config.yaml"
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


def test_valid_minimal_config(tmp_path: Path) -> None:
    cfg_path = write_config(tmp_path, """
        edutex:
          version: "0.1.0"
        knowledge:
          model: "assets/knowledge_models/example.md"
        theme:
          name: "default"
        layout:
          name: "default"
    """)
    config = load_config(cfg_path)
    assert isinstance(config, EduTexConfig)
    assert config.edutex.version == "0.1.0"
    assert config.theme.name == "default"
    assert config.build.output_format == OutputFormat.pdf


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="not found"):
        load_config(tmp_path / "nonexistent.yaml")


def test_invalid_yaml_raises(tmp_path: Path) -> None:
    p = tmp_path / "edutex.config.yaml"
    p.write_text(": invalid: yaml: [", encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_config(p)


def test_missing_required_field_raises(tmp_path: Path) -> None:
    cfg_path = write_config(tmp_path, """
        edutex:
          version: "0.1.0"
        theme:
          name: "default"
        layout:
          name: "default"
    """)
    with pytest.raises(ConfigurationError, match="validation failed"):
        load_config(cfg_path)

def test_configuration_model_is_immutable_after_validation():
    import pytest
    from pydantic import ValidationError

    from edutex.configuration.schema import EduTexConfig, OutputFormat

    config = EduTexConfig.model_validate(
        {
            "edutex": {"version": "0.3.0"},
            "knowledge": {"model": "assets/km/example.md"},
            "theme": {"name": "default"},
            "layout": {"name": "standard"},
            "extensions": {"enabled": ["reading_tip"]},
        }
    )

    with pytest.raises((TypeError, ValidationError)):
        config.theme = config.theme.model_copy(update={"name": "other"})

    with pytest.raises((TypeError, ValidationError)):
        config.build.output_format = OutputFormat.html

    with pytest.raises(TypeError):
        config.extensions.enabled.append("another_extension")

    assert config.theme.name == "default"
    assert config.build.output_format == OutputFormat.pdf
    assert config.extensions.enabled == ["reading_tip"]
