"""Explicit optional-extension loading with controlled fallback."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from edutex.core.errors import ExtensionError
from edutex.extension.loader import ExtensionLoader, LoadedExtension
from edutex.extension.models import ExtensionDiagnostic, ExtensionManifest


@dataclass(frozen=True)
class OptionalExtensionResult:
    """Result of loading one extension through the optional fallback boundary."""

    manifest: ExtensionManifest
    loaded: LoadedExtension | None
    diagnostic: ExtensionDiagnostic | None = None

    @property
    def skipped(self) -> bool:
        """Whether the optional extension was skipped without failing the caller."""
        return self.loaded is None


def load_extension_with_fallback(
    manifest_path: Path,
    *,
    expected_id: str | None = None,
    loader: ExtensionLoader | None = None,
) -> OptionalExtensionResult:
    """Load an extension, skipping failures only for ``optional: true`` manifests.

    A missing or malformed manifest cannot declare optionality and therefore
    remains a hard ``ExtensionError``. Once a valid manifest is read, module,
    entrypoint, version, and compatibility failures may be converted to one
    deterministic diagnostic only when the manifest is explicitly optional.
    """
    extension_loader = loader or ExtensionLoader()
    manifest = extension_loader.read_manifest(manifest_path, expected_id=expected_id)
    try:
        loaded = extension_loader.load(manifest_path, expected_id=expected_id)
    except ExtensionError as exc:
        if not manifest.optional:
            raise
        diagnostic = ExtensionDiagnostic(
            extension_id=manifest.extension_id,
            point_id=None,
            phase="loading",
            message=str(exc),
        )
        return OptionalExtensionResult(
            manifest=manifest,
            loaded=None,
            diagnostic=diagnostic,
        )
    return OptionalExtensionResult(manifest=manifest, loaded=loaded)
