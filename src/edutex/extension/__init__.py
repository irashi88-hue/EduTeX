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


from edutex.extension.catalog import (
    ExtensionCatalogEntry,
    get_official_extension,
    official_extension_catalog,
    search_official_extensions,
)
