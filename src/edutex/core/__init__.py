"""EduTeX Core public API."""

from edutex.core.context import LifecyclePhase, RuntimeContext
from edutex.core.diagnostics import format_diagnostics_text, serialize_diagnostic, serialize_diagnostics
from edutex.core.errors import (
    ActivationError,
    BuildError,
    ConfigurationError,
    EduTeXError,
    ExtensionError,
    KnowledgeError,
    LayoutError,
    RegistryError,
    ResolverError,
    ThemeError,
)

__all__ = [
    "ActivationError",
    "BuildError",
    "ConfigurationError",
    "EduTeXError",
    "ExtensionError",
    "format_diagnostics_text",
    "serialize_diagnostic",
    "serialize_diagnostics",
    "KnowledgeError",
    "LayoutError",
    "LifecyclePhase",
    "RegistryError",
    "ResolverError",
    "RuntimeContext",
    "ThemeError",
]
