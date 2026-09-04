"""Validated EduTeX configuration schema with user-facing constraints."""

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

    @field_validator("model", mode="before")
    @classmethod
    def validate_model_path(cls, value: object) -> object:
        if value is None or not str(value).strip():
            raise ValueError("the Knowledge Model path must not be empty")
        return value


class ThemeConfig(BaseModel):
    name: str = Field(..., description="Name of the theme to apply.")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("the theme name must not be empty")
        return value


class LayoutConfig(BaseModel):
    name: str = Field(..., description="Name of the layout to apply.")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("the layout name must not be empty")
        return value


class BuildConfig(BaseModel):
    output_format: OutputFormat = Field(OutputFormat.pdf, description="Output format.")
    output_dir: Path = Field(Path("output"), description="Output directory.")
    output_file: str = Field("document", min_length=1, description="Output filename without extension.")

    @field_validator("output_file")
    @classmethod
    def validate_output_file(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("the output filename must not be empty")
        return value


class ExtensionsConfig(BaseModel):
    enabled: list[str] = Field(default_factory=list, description="Enabled extension names.")

    @field_validator("enabled")
    @classmethod
    def validate_extension_names(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value]
        if any(not item for item in cleaned):
            raise ValueError("extension names must not be empty")
        return cleaned


class LoggingConfig(BaseModel):
    level: LogLevel = Field(LogLevel.info, description="Logging level.")


class EduTexVersionConfig(BaseModel):
    version: str = Field(..., min_length=1, description="EduTeX framework version.")

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("the EduTeX version must not be empty")
        return value


class EduTexConfig(BaseModel):
    """Root configuration model for the EduTeX framework."""

    edutex: EduTexVersionConfig
    knowledge: KnowledgeConfig
    theme: ThemeConfig
    layout: LayoutConfig
    build: BuildConfig = Field(default_factory=BuildConfig)
    extensions: ExtensionsConfig = Field(default_factory=ExtensionsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
