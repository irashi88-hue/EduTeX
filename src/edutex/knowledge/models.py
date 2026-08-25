"""
EduTeX Knowledge Content Model
Component: Knowledge (COMP-KNOW-001)
Contract: KNOW-001 (Knowledge Content Contract)

Defines the ContentModel — the structured, validated, typed representation
of a Knowledge Model's educational content, produced after parsing.

This is the primary artifact exposed through KNOW-001 to Theme and Layout.
It is strictly read-only after Knowledge Processing completes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContentNode:
    """
    A single parsed shortcode node within the content model.

    Corresponds to a ShortcodeNode from the parser, but typed and validated.
    """
    node_type:  str                          # e.g. "rule", "example", "vocab"
    subtype:    str | None                   # e.g. "simple", "math"
    fields:     list[str]                    # positional pipe-separated fields
    body:       str                          # main text body
    children:   list[ContentNode] = field(default_factory=list)  # nested nodes
    source_line: int = 0

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0


@dataclass
class TextBlock:
    """A block of plain Markdown prose between shortcode nodes."""
    content: str


# A content item is either a ContentNode (shortcode) or a TextBlock (prose)
ContentItem = ContentNode | TextBlock


@dataclass
class ContentModel:
    """
    The fully parsed, validated educational content model.
    Exposed through KNOW-001 (Knowledge Content Contract).

    Immutable after Knowledge Processing completes (KNOW-C-001).
    Consumers (Theme, Layout) SHALL NOT modify this model.
    """
    items: list[ContentItem] = field(default_factory=list)

    def nodes(self) -> list[ContentNode]:
        """Return only the shortcode nodes (no prose blocks)."""
        return [item for item in self.items if isinstance(item, ContentNode)]

    def nodes_of_type(self, node_type: str) -> list[ContentNode]:
        """Return all shortcode nodes of a given type."""
        return [n for n in self.nodes() if n.node_type == node_type]

    def __len__(self) -> int:
        return len(self.items)
