"""Public models for the EduTeX Extension System (EXT-001, EXT-002)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from edutex.layout.models import DocumentStructure


@dataclass(frozen=True)
class ExtensionPoint:
    """A declared location where an extension may contribute."""

    point_id: str
    component: str
    description: str


@dataclass(frozen=True)
class ExtensionContext:
    """
    Read-only extension context.

    ``document`` is an isolated snapshot. The Extension System never gives an
    extension a live service instance or the live document object.
    """

    extension_point: ExtensionPoint
    document: DocumentStructure


@dataclass(frozen=True)
class ExtensionManifest:
    """Validated metadata loaded from an extension.yaml asset."""

    extension_id: str
    name: str
    version: str
    target: str
    module: str
    entrypoint: str
    framework: str | None = None


@dataclass(frozen=True)
class LoadedExtension:
    """A validated manifest paired with its callable contribution handler."""

    manifest: ExtensionManifest
    handler: Callable[[ExtensionContext], Any]

@dataclass(frozen=True)
class ExtensionDiagnostic:
    """Structured diagnostic emitted by extension processing."""

    extension_id: str | None
    point_id: str | None
    phase: str
    message: str
