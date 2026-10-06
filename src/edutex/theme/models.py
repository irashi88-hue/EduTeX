"""
EduTeX Theme Models
Component: Theme (COMP-THEME-001)
Contracts: THEME-001 (Theme Contract), THEME-002 (Style Contract)

Defines the data structures produced by Theme Processing:
  - StyleRule      — visual rules for a single content node type
  - ThemeModel     — the full set of style rules for the active theme
  - StyledNode     — a ContentNode augmented with its StyleRule
  - StyledContent  — the complete styled content representation (THEME-001)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from edutex.knowledge.models import ContentNode, TextBlock


@dataclass(frozen=True)
class StyleRule:
    """
    Visual style rule for a single content node type.
    Exposed through THEME-002 (Style Contract).
    """
    label:            str   # display label (e.g. "Rule", "Note", "")
    border_color:     str   # hex color string or ""
    background_color: str   # hex color string or ""
    font_weight:      str   # "bold" | "normal"
    display:          str   # "block" | "card" | "table" | "centered"


@dataclass
class ThemeModel:
    """
    The full set of style rules for the active theme.
    Loaded from the theme asset (theme.yaml).
    Exposed through THEME-002.
    """
    theme_id:   str
    theme_name: str
    version:    str
    styles:     dict[str, StyleRule] = field(default_factory=dict)
    palette:    dict[str, str] = field(default_factory=dict)
    tokens: dict[str, object] = field(default_factory=dict)

    def get_style(self, node_type: str) -> StyleRule:
        """
        Return the StyleRule for a given node type.
        Falls back to '_default' if the type has no explicit rule.
        """
        if node_type in self.styles:
            return self.styles[node_type]
        if "_default" in self.styles:
            return self.styles["_default"]
        # Hard fallback — should never be reached if theme is valid
        return StyleRule(
            label="", border_color="#cccccc",
            background_color="#ffffff", font_weight="normal", display="block"
        )


@dataclass
class StyledNode:
    """
    A ContentNode augmented with its resolved StyleRule.
    Part of the StyledContent exposed through THEME-001.
    """
    node:     ContentNode
    style:    StyleRule
    children: list[StyledNode] = field(default_factory=list)

    @property
    def node_type(self) -> str:
        return self.node.node_type

    @property
    def body(self) -> str:
        return self.node.body

    @property
    def fields(self) -> list[str]:
        return self.node.fields

    @property
    def subtype(self) -> str | None:
        return self.node.subtype


@dataclass
class StyledContent:
    """
    The complete styled content representation.
    Primary artifact of Theme Processing, exposed through THEME-001.
    Immutable after Theme Processing completes (THEME-C-006).
    Consumers SHALL NOT modify this object.
    """
    items:      list[StyledNode | TextBlock]
    theme_model: ThemeModel

    def styled_nodes(self) -> list[StyledNode]:
        """Return only the styled shortcode nodes."""
        return [i for i in self.items if isinstance(i, StyledNode)]

    def nodes_of_type(self, node_type: str) -> list[StyledNode]:
        return [n for n in self.styled_nodes() if n.node_type == node_type]
