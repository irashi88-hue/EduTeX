"""Extension point registry (EXT-002)."""

from __future__ import annotations

from edutex.core.errors import ExtensionError
from edutex.extension.models import ExtensionPoint


class ExtensionPointRegistry:
    """Registry of extension points exposed by framework services."""

    def __init__(self) -> None:
        self._points: dict[str, ExtensionPoint] = {}

    def declare(self, point: ExtensionPoint) -> None:
        if point.point_id in self._points:
            raise ExtensionError(
                f"Duplicate extension point declaration: {point.point_id!r}."
            )
        self._points[point.point_id] = point

    def get(self, point_id: str) -> ExtensionPoint | None:
        return self._points.get(point_id)

    def all(self) -> tuple[ExtensionPoint, ...]:
        return tuple(self._points.values())

    @classmethod
    def default(cls) -> "ExtensionPointRegistry":
        """Return the extension points currently exposed by EduTeX."""
        registry = cls()
        registry.declare(ExtensionPoint(
            point_id="layout.post_structure",
            component="Layout",
            description="Transform an isolated DocumentStructure after Layout Processing.",
        ))
        return registry
