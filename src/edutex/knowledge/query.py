"""Read-only query helpers for the EduTeX content model."""

from __future__ import annotations

from copy import deepcopy
from typing import Iterator

from edutex.knowledge.models import ContentModel, ContentNode


def _walk(nodes: list[ContentNode]) -> Iterator[ContentNode]:
    """Yield nodes in deterministic preorder, including nested nodes."""
    for node in nodes:
        yield node
        yield from _walk(node.children)


def _filter_value(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value.strip().casefold()


class ContentQuery:
    """Read-only, deterministic queries over a parsed content model.

    The query takes a detached snapshot of the model. Every returned node is
    copied again, so callers cannot mutate the snapshot or the source model
    through a query result.
    """

    def __init__(self, model: ContentModel) -> None:
        if not isinstance(model, ContentModel):
            raise TypeError("model must be a ContentModel instance.")
        self._nodes = tuple(deepcopy(list(_walk(model.nodes()))))

    def all(self) -> list[ContentNode]:
        """Return all nodes in deterministic preorder, including nested nodes."""
        return deepcopy(list(self._nodes))

    def by_type(self, node_type: str) -> list[ContentNode]:
        """Return nodes whose type matches case-insensitively."""
        needle = _filter_value(node_type, "node_type")
        return deepcopy(
            [node for node in self._nodes if node.node_type.casefold() == needle]
        )

    def by_subtype(self, subtype: str) -> list[ContentNode]:
        """Return nodes with the requested non-null subtype."""
        needle = _filter_value(subtype, "subtype")
        return deepcopy(
            [
                node
                for node in self._nodes
                if node.subtype is not None and node.subtype.casefold() == needle
            ]
        )

    def search(self, text: str) -> list[ContentNode]:
        """Return nodes whose type, subtype, fields, or body contains text."""
        needle = _filter_value(text, "text")
        matches: list[ContentNode] = []
        for node in self._nodes:
            searchable = " ".join(
                [node.node_type, node.subtype or "", *node.fields, node.body]
            ).casefold()
            if needle in searchable:
                matches.append(node)
        return deepcopy(matches)

    def count(self, node_type: str | None = None) -> int:
        """Return the total node count or the count for one node type."""
        if node_type is None:
            return len(self._nodes)
        return len(self.by_type(node_type))

    def __len__(self) -> int:
        return len(self._nodes)


def query_content(model: ContentModel) -> ContentQuery:
    """Create a read-only query over a parsed content model."""
    return ContentQuery(model)
