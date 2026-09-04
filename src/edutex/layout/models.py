"""
EduTeX Layout Models
Component: Layout (COMP-LAYOUT-001)
Contracts: LAYOUT-001 (Layout Contract), LAYOUT-002 (Layout Rules Contract)

Defines the data structures produced by Layout Processing:
  - PlacementRule   — structural placement directives per node type
  - PageConfig      — page geometry settings
  - LayoutModel     — the full layout definition loaded from layout.yaml
  - DocumentElement — a positioned, styled element ready for rendering
  - DocumentStructure — the complete ordered document (LAYOUT-001)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from edutex.theme.models import StyledNode, StyledContent
from edutex.knowledge.models import TextBlock


@dataclass(frozen=True)
class PlacementRule:
    """
    Structural placement directive for a content node type.
    Exposed through LAYOUT-002 (Layout Rules Contract).
    """
    page_break_before: bool
    keep_with_next:    bool
    spacing_before_mm: float
    spacing_after_mm:  float


@dataclass(frozen=True)
class PageConfig:
    """Page geometry settings."""
    size:              str    # e.g. "A4"
    margin_top_mm:     float
    margin_bottom_mm:  float
    margin_left_mm:    float
    margin_right_mm:   float
    columns:           int


@dataclass
class AppendixConfig:
    """Configuration for the solutions appendix."""
    enabled:           bool
    title:             str
    page_break_before: bool


@dataclass
class LayoutModel:
    """
    The full layout definition loaded from layout.yaml.
    Exposed through LAYOUT-002 (Layout Rules Contract).
    """
    layout_id:     str
    layout_name:   str
    version:       str
    page:          PageConfig
    placement:     dict[str, PlacementRule] = field(default_factory=dict)
    section_order: list[str] = field(default_factory=list)
    appendix:      AppendixConfig = field(
        default_factory=lambda: AppendixConfig(False, "Solutions", True)
    )

    def get_placement(self, node_type: str) -> PlacementRule:
        """Return the PlacementRule for a node type, falling back to _default."""
        if node_type in self.placement:
            return self.placement[node_type]
        if "_default" in self.placement:
            return self.placement["_default"]
        return PlacementRule(
            page_break_before=False, keep_with_next=False,
            spacing_before_mm=4.0,   spacing_after_mm=4.0
        )


@dataclass(frozen=True)
class SolutionReference:
    """Stable link between an exercise and its appendix solution."""
    index: int
    exercise_id: str
    solution_id: str
    exercise_title: str = ""
    solution_title: str = ""


@dataclass
class DocumentElement:
    """
    A single positioned element in the document structure.
    Combines a StyledNode with its PlacementRule.
    """
    styled_node:    StyledNode
    placement:      PlacementRule
    position_index: int    # order in the final document
    exercise_id: str = ""
    solution_id: str = ""
    solution_index: int = 0

    @property
    def node_type(self) -> str:
        return self.styled_node.node_type


@dataclass
class DocumentStructure:
    """
    The complete ordered document structure.
    Primary artifact of Layout Processing, exposed through LAYOUT-001.
    Immutable after Layout Processing completes.
    Consumed by the Build System to produce the final output.
    """
    elements:        list[DocumentElement]
    prose_blocks:    list[tuple[int, TextBlock]]  # (position_index, block)
    layout_model:    LayoutModel
    appendix_nodes:  list[StyledNode] = field(default_factory=list)
    solution_references: list[SolutionReference] = field(default_factory=list)

    def ordered_elements(self) -> list[DocumentElement]:
        """Return elements in their final document order."""
        return sorted(self.elements, key=lambda e: e.position_index)
