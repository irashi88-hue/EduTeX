"""Validated EduTeX configuration schema with user-facing constraints."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Literal

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


class RuntimeIdentity(_ImmutableConfigModel):
    type: Literal["knowledge_model", "theme", "layout", "extension", "component"]
    id: str = Field(..., min_length=1)

    @field_validator("id")
    @classmethod
    def valid_id(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("runtime entity IDs must be non-empty without surrounding whitespace")
        return value


class RuntimeAsset(RuntimeIdentity):
    path: Path

    @field_validator("path", mode="before")
    @classmethod
    def valid_path(cls, value: object) -> object:
        if value is None or not str(value).strip():
            raise ValueError("runtime asset path must not be empty")
        return value


class RuntimeReference(_ImmutableConfigModel):
    source: RuntimeIdentity
    target: RuntimeIdentity
    reference_type: str = Field("requires", min_length=1)
    optional: bool = False


class RuntimeConfig(_ImmutableConfigModel):
    assets: tuple[RuntimeAsset, ...] = ()
    references: tuple[RuntimeReference, ...] = ()


class DialogueConfig(_ImmutableConfigModel):
    """Optional text-only dialogue exercises backed by a local model endpoint."""

    enabled: bool = False
    endpoint: str = "http://localhost:11434"
    model: str = ""
    timeout_seconds: int = Field(default=60, ge=1, le=600)
    langdock_url: str = ""

    @field_validator("endpoint")
    @classmethod
    def _endpoint_must_be_http(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError("dialogue endpoint must start with http:// or https://")
        return value

    @model_validator(mode="after")
    def _model_required_when_enabled(self) -> "DialogueConfig":
        if self.enabled and not self.model.strip():
            raise ValueError("dialogue.model is required when dialogue.enabled is true")
        return self


class EduTexConfig(_ImmutableConfigModel):
    """Root configuration model for the EduTeX framework."""

    edutex: EduTexVersionConfig
    knowledge: KnowledgeConfig
    theme: ThemeConfig = Field(default_factory=ThemeConfig, description="Theme to apply; omitted selects the bundled default.")
    layout: LayoutConfig
    build: BuildConfig = Field(default_factory=BuildConfig)
    extensions: ExtensionsConfig = Field(default_factory=ExtensionsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    dialogue: DialogueConfig = Field(default_factory=DialogueConfig)
