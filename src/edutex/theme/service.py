"""
EduTeX Theme Service
Component: Theme (COMP-THEME-001)
Contracts: THEME-001 (Theme Contract), THEME-002 (Style Contract)

Orchestrates Theme Processing:
  1. Loads the active theme asset from the ActivatedState (ACT-001).
  2. Builds the ThemeModel from theme.yaml (THEME-002).
  3. Applies style rules to every node in the ContentModel (KNOW-001).
  4. Produces the StyledContent (THEME-001) — read-only after processing.

Theme SHALL NOT modify the educational content model.
Theme SHALL NOT define document structure (owned by Layout).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from edutex.activator.activator import ActivatedState
from edutex.core.errors import ThemeError
from edutex.knowledge.models import ContentModel, ContentNode, TextBlock
from edutex.knowledge.service import KnowledgeService
from edutex.registry.models import EntityType
from edutex.theme.models import StyleRule, StyledContent, StyledNode, ThemeModel


class ThemeService:
    """
    Theme Service — orchestrates Theme Processing (COMP-THEME-001).

    Usage:
        service = ThemeService()
        service.process(state, knowledge_service, project_root)

        styled  = service.styled_content  # THEME-001
        model   = service.theme_model     # THEME-002
    """

    def __init__(self) -> None:
        self._styled_content: StyledContent | None = None
        self._theme_model:    ThemeModel | None = None

    # ------------------------------------------------------------------
    # THEME-001 — Theme Contract
    # ------------------------------------------------------------------

    @property
    def styled_content(self) -> StyledContent:
        """Styled content representation (THEME-001). Read-only."""
        if self._styled_content is None:
            raise ThemeError(
                "Styled content is not available — process() has not been called."
            )
        return self._styled_content

    # ------------------------------------------------------------------
    # THEME-002 — Style Contract
    # ------------------------------------------------------------------

    @property
    def theme_model(self) -> ThemeModel:
        """Resolved style rules for the active theme (THEME-002). Read-only."""
        if self._theme_model is None:
            raise ThemeError(
                "Theme model is not available — process() has not been called."
            )
        return self._theme_model

    # ------------------------------------------------------------------
    # Processing entry point
    # ------------------------------------------------------------------

    def process(
        self,
        state: ActivatedState,
        knowledge: KnowledgeService,
        project_root: Path,
    ) -> None:
        """
        Execute Theme Processing.

        Args:
            state:        Activated framework state (ACT-001).
            knowledge:    Completed Knowledge Service (KNOW-001, KNOW-002).
            project_root: Project root for resolving asset paths.

        Raises:
            ThemeError: If no theme is activated, the theme asset cannot be
                        loaded, or a node type has no style rule (CC-003).
        """
        # Step 1 — resolve active theme from ACT-001
        theme_entity = state.get_first(EntityType.THEME)
        if theme_entity is None:
            raise ThemeError(
                "No Theme is activated. "
                "Register a Theme entity before running Theme Processing."
            )

        theme_path = project_root / theme_entity.source_path / "theme.yaml"

        # Step 2 — load theme asset → ThemeModel (THEME-002)
        self._theme_model = self._load_theme(theme_path)

        # Step 3 — apply style rules to ContentModel (KNOW-001) → StyledContent (THEME-001)
        content_model = knowledge.content
        self._styled_content = self._apply_styles(content_model, self._theme_model)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_theme(self, theme_path: Path) -> ThemeModel:
        """Load and validate the theme.yaml asset."""
        if not theme_path.exists():
            raise ThemeError(f"Theme asset not found: {theme_path}")

        try:
            raw = yaml.safe_load(theme_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ThemeError(f"Failed to parse theme asset: {exc}") from exc

        if not isinstance(raw, dict):
            raise ThemeError("Theme asset must be a YAML mapping.")

        styles_raw = raw.get("styles", {})
        styles: dict[str, StyleRule] = {}
        for node_type, rule_data in styles_raw.items():
            if not isinstance(rule_data, dict):
                continue
            styles[node_type] = StyleRule(
                label=str(rule_data.get("label", "")),
                border_color=str(rule_data.get("border_color", "")),
                background_color=str(rule_data.get("background_color", "")),
                font_weight=str(rule_data.get("font_weight", "normal")),
                display=str(rule_data.get("display", "block")),
            )

        return ThemeModel(
            theme_id=str(raw.get("id", "unknown")),
            theme_name=str(raw.get("name", "")),
            version=str(raw.get("version", "1.0.0")),
            styles=styles,
        )

    def _apply_styles(
        self, content_model: ContentModel, theme_model: ThemeModel
    ) -> StyledContent:
        """Apply style rules to every node in the ContentModel."""
        items = []
        for item in content_model.items:
            if isinstance(item, TextBlock):
                items.append(item)
            elif isinstance(item, ContentNode):
                items.append(self._style_node(item, theme_model))
        return StyledContent(items=items, theme_model=theme_model)

    def _style_node(self, node: ContentNode, theme_model: ThemeModel) -> StyledNode:
        """Recursively apply style rules to a ContentNode and its children."""
        style = theme_model.get_style(node.node_type)
        children = [self._style_node(c, theme_model) for c in node.children]
        return StyledNode(node=node, style=style, children=children)
