"""
EduTeX Extension Service (MECH-EXT-001).

Coordinates validated extension contributions at declared extension points.
The first implemented point is ``layout.post_structure``. Extensions receive
isolated document snapshots and return a new DocumentStructure; they never
receive live service state.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from edutex.activator.activator import ActivatedState
from edutex.core.errors import ExtensionError
from edutex.extension.loader import ExtensionLoader
from edutex.extension.models import ExtensionContext, LoadedExtension
from edutex.extension.registry import ExtensionPointRegistry
from edutex.layout.models import DocumentStructure
from edutex.layout.service import LayoutService
from edutex.registry.models import EntityType


class ExtensionService:
    """Extension Processing stage, after Layout and before Build."""

    def __init__(self) -> None:
        self._document: DocumentStructure | None = None
        self._loaded: list[LoadedExtension] = []
        self._points = ExtensionPointRegistry.default()

    @property
    def document(self) -> DocumentStructure:
        """The post-extension document structure consumed by Build."""
        if self._document is None:
            raise ExtensionError(
                "Extended document is not available — process() has not been called."
            )
        return self._document

    @property
    def loaded_extensions(self) -> tuple[LoadedExtension, ...]:
        """Validated extensions loaded during the last processing pass."""
        return tuple(self._loaded)

    def terminate(self) -> None:
        """Release extension-processing state during runtime termination."""
        self._document = None
        self._loaded = []

    @property
    def extension_points(self) -> ExtensionPointRegistry:
        """The EXT-002 registry of declared extension points."""
        return self._points

    def process(
        self,
        state: ActivatedState,
        layout: LayoutService,
        project_root: Path,
    ) -> None:
        """Load, validate, order, and apply all activated extensions."""
        current = deepcopy(layout.document)
        self._loaded = []
        loader = ExtensionLoader()

        extension_entities = state.get_by_type(EntityType.EXTENSION)
        for entity in extension_entities:
            loaded = loader.load(entity.source_path, expected_id=entity.entity_id)
            point = self._points.get(loaded.manifest.target)
            if point is None:
                raise ExtensionError(
                    f"Extension {loaded.manifest.extension_id!r} targets undeclared "
                    f"extension point {loaded.manifest.target!r}."
                )
            self._loaded.append(loaded)

            if point.point_id != "layout.post_structure":
                raise ExtensionError(
                    f"Extension point {point.point_id!r} is declared but not yet "
                    "supported by this processing stage."
                )

            context = ExtensionContext(
                extension_point=point,
                document=deepcopy(current),
            )
            try:
                result = loaded.handler(context)
            except Exception as exc:
                raise ExtensionError(
                    f"Extension {loaded.manifest.extension_id!r} failed at "
                    f"{point.point_id!r}: {exc}"
                ) from exc

            if not isinstance(result, DocumentStructure):
                raise ExtensionError(
                    f"Extension {loaded.manifest.extension_id!r} returned "
                    f"{type(result).__name__}; expected DocumentStructure."
                )
            current = deepcopy(result)

        self._document = current
