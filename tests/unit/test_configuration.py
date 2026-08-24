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
