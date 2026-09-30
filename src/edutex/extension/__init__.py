"""EduTeX Extension System public API."""

from edutex.extension.models import (
    ExtensionContext,
    ExtensionDiagnostic,
    ExtensionManifest,
    ExtensionPoint,
    LoadedExtension,
)
from edutex.extension.registry import ExtensionPointRegistry
from edutex.extension.service import ExtensionService

__all__ = [
    "ExtensionContext",
    "ExtensionDiagnostic",
    "ExtensionManifest",
    "ExtensionPoint",
    "ExtensionPointRegistry",
    "ExtensionService",
    "LoadedExtension",
]
