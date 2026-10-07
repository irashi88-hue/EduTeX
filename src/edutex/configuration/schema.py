"""Validated EduTeX configuration schema with user-facing constraints."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class _ImmutableConfigModel(BaseModel):
    """Base model enforcing configuration immutability."""

    model_config = ConfigDict(frozen=True)


class _ImmutableList(list[str]):
    """List-compatible container that rejects all in-place mutations."""

    @staticmethod
    def _reject_mutation(*args: object, **kwargs: object) -> None:
        raise TypeError("configuration collections are immutable")

    __setitem__ = _reject_mutation
    __delitem__ = _reject_mutation
    __iadd__ = _reject_mutation
    __imul__ = _reject_mutation
    append = _reject_mutation
    clear = _reject_mutation
    extend = _reject_mutation
    insert = _reject_mutation
    pop = _reject_mutation
    remove = _reject_mutation
    reverse = _reject_mutation
    sort = _reject_mutation


class OutputFormat(str, Enum):
    pdf = "pdf"
    latex = "latex"
    html = "html"


class LogLevel(str, Enum):
    debug = "DEBUG"
    info = "INFO"
    warning = "WARNING"
    error = "ERROR"


class KnowledgeConfig(_ImmutableConfigModel):
    model: Path = Field(..., description="Path to the Knowledge Model source file.")

    @field_validator("model", mode="before")
    @classmethod
    def validate_model_path(cls, value: object) -> object:
        if value is None or not str(value).strip():
            raise ValueError("the Knowledge Model path must not be empty")
        return value


class ThemeConfig(_ImmutableConfigModel):
    name: str = Field("default", description="Name of the theme to apply.")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("the theme name must not be empty")
        return value


class LayoutConfig(_ImmutableConfigModel):
    name: str = Field(..., description="Name of the layout to apply.")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("the layout name must not be empty")
        return value


class BuildConfig(_ImmutableConfigModel):
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


class ExtensionsConfig(_ImmutableConfigModel):
    enabled: list[str] = Field(default_factory=list, description="Enabled extension names.")

    @field_validator("enabled")
    @classmethod
    def validate_extension_names(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value]
        if any(not item for item in cleaned):
            raise ValueError("extension names must not be empty")
        return cleaned

    @model_validator(mode="after")
    def freeze_enabled(self) -> "ExtensionsConfig":
        object.__setattr__(
            self,
            "enabled",
            _ImmutableList(self.enabled),
        )
        return self


class LoggingConfig(_ImmutableConfigModel):
    level: LogLevel = Field(LogLevel.info, description="Logging level.")


class EduTexVersionConfig(_ImmutableConfigModel):
    version: str = Field(..., min_length=1, description="EduTeX framework version.")

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("the EduTeX version must not be empty")
        return value


class EduTexConfig(_ImmutableConfigModel):
    """Root configuration model for the EduTeX framework."""

    edutex: EduTexVersionConfig
    knowledge: KnowledgeConfig
    theme: ThemeConfig = Field(default_factory=ThemeConfig, description="Theme to apply; omitted selects the bundled default.")
    layout: LayoutConfig
    build: BuildConfig = Field(default_factory=BuildConfig)
    extensions: ExtensionsConfig = Field(default_factory=ExtensionsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
