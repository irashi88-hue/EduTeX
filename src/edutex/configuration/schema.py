"""
EduTeX Configuration Schema
Component: Configuration (COMP-CONFIG-001)
Contracts: CFG-001 (Configuration Contract), CFG-002 (Configuration Schema Contract)

Defines the validated configuration model for the EduTeX framework.
All configuration consumed by other components is validated through this module.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class OutputFormat(str, Enum):
    pdf = "pdf"
    latex = "latex"
    html = "html"


class LogLevel(str, Enum):
    debug = "DEBUG"
    info = "INFO"
    warning = "WARNING"
    error = "ERROR"


class KnowledgeConfig(BaseModel):
    model: Path = Field(..., description="Path to the Knowledge Model source file.")


class ThemeConfig(BaseModel):
    name: str = Field(..., description="Name of the theme to apply.")


class LayoutConfig(BaseModel):
    name: str = Field(..., description="Name of the layout to apply.")


class BuildConfig(BaseModel):
    output_format: OutputFormat = Field(OutputFormat.pdf, description="Output format.")
    output_dir: Path = Field(Path("output"), description="Output directory.")
    output_file: str = Field("document", description="Output filename without extension.")


class ExtensionsConfig(BaseModel):
    enabled: list[str] = Field(default_factory=list, description="Enabled extension names.")


class LoggingConfig(BaseModel):
    level: LogLevel = Field(LogLevel.info, description="Logging level.")


class EduTexVersionConfig(BaseModel):
    version: str = Field(..., description="EduTeX framework version.")


class EduTexConfig(BaseModel):
    """
    Root configuration model for the EduTeX framework.
    Validated by the Configuration component (CFG-001).
    """
    edutex: EduTexVersionConfig
    knowledge: KnowledgeConfig
    theme: ThemeConfig
    layout: LayoutConfig
    build: BuildConfig = Field(default_factory=BuildConfig)
    extensions: ExtensionsConfig = Field(default_factory=ExtensionsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @field_validator("knowledge", mode="before")
    @classmethod
    def validate_knowledge(cls, v: object) -> object:
        return v
