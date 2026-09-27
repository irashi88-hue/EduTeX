"""EduTeX Extension System public API."""

from edutex.extension.models import (
    ExtensionContext,
    ExtensionManifest,
    ExtensionPoint,
    LoadedExtension,
)
from edutex.extension.registry import ExtensionPointRegistry
from edutex.extension.service import ExtensionService

__all__ = [
    "ExtensionContext",
    "ExtensionManifest",
    "ExtensionPoint",
    "ExtensionPointRegistry",
    "ExtensionService",
    "LoadedExtension",
]
