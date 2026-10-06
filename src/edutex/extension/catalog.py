"""Deterministic catalog of official EduTeX extensions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExtensionCatalogEntry:
    """Public metadata for one official extension."""

    extension_id: str
    name: str
    version: str
    framework: str | None
    target: str
    optional: bool
    description: str

    def to_dict(self) -> dict[str, object]:
        """Return a detached JSON-ready representation."""
        return {
            "id": self.extension_id,
            "name": self.name,
            "version": self.version,
            "framework": self.framework,
            "target": self.target,
            "optional": self.optional,
            "description": self.description,
        }


_OFFICIAL_EXTENSIONS = (
    ExtensionCatalogEntry(
        extension_id="reading_tip",
        name="Reading tip",
        version="1.0.0",
        framework=">=1.0.0,<2.0.0",
        target="layout.post_structure",
        optional=False,
        description="Adds a reading tip to the generated document structure.",
    ),
)


def official_extension_catalog() -> tuple[ExtensionCatalogEntry, ...]:
    """Return official extensions in stable identifier order."""
    return tuple(_OFFICIAL_EXTENSIONS)


def get_official_extension(extension_id: str) -> ExtensionCatalogEntry | None:
    """Return one official extension by ID, or None when not cataloged."""
    for entry in _OFFICIAL_EXTENSIONS:
        if entry.extension_id == extension_id:
            return entry
    return None


def search_official_extensions(query: str) -> tuple[ExtensionCatalogEntry, ...]:
    """Search IDs, names, targets, and descriptions without changing order."""
    needle = query.strip().casefold()
    if not needle:
        return official_extension_catalog()
    return tuple(
        entry
        for entry in _OFFICIAL_EXTENSIONS
        if needle
        in " ".join(
            (
                entry.extension_id,
                entry.name,
                entry.target,
                entry.description,
            )
        ).casefold()
    )
