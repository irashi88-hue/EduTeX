"""
EduTeX Layout Service
Component: Layout (COMP-LAYOUT-001)
Contracts: LAYOUT-001 (Layout Contract), LAYOUT-002 (Layout Rules Contract)

Orchestrates Layout Processing:
  1. Loads the active layout asset from the ActivatedState (ACT-001).
  2. Builds the LayoutModel from layout.yaml (LAYOUT-002).
  3. Assigns placement rules to every StyledNode from Theme (THEME-001).
  4. Determines final document element order.
  5. Collects solution nodes into the appendix.
  6. Produces the DocumentStructure (LAYOUT-001) — read-only after processing.

Layout SHALL NOT own educational knowledge or visual styling rules.
Layout SHALL NOT modify the StyledContent produced by Theme.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml

from edutex.activator.activator import ActivatedState
from edutex.core.errors import LayoutError
from edutex.knowledge.models import TextBlock
from edutex.layout.models import (
    AppendixConfig, DocumentElement, DocumentStructure,
    LayoutModel, PageConfig, PlacementRule, SolutionReference,
)
from edutex.registry.models import EntityType
from edutex.theme.models import StyledContent, StyledNode
from edutex.theme.service import ThemeService


class LayoutService:
    """
    Layout Service — orchestrates Layout Processing (COMP-LAYOUT-001).

    Usage:
        service = LayoutService()
        service.process(state, theme_service, project_root)

        doc    = service.document    # LAYOUT-001
        model  = service.layout_model  # LAYOUT-002
    """

    def __init__(self) -> None:
        self._document:     DocumentStructure | None = None
        self._layout_model: LayoutModel | None = None

    # ------------------------------------------------------------------
    # LAYOUT-001 — Layout Contract
    # ------------------------------------------------------------------

    @property
    def document(self) -> DocumentStructure:
        """The complete document structure (LAYOUT-001). Read-only."""
        if self._document is None:
            raise LayoutError(
                "Document structure is not available — process() has not been called."
            )
        return deepcopy(self._document)

    # ------------------------------------------------------------------
    # LAYOUT-002 — Layout Rules Contract
    # ------------------------------------------------------------------

    @property
    def layout_model(self) -> LayoutModel:
        """The resolved layout rules (LAYOUT-002). Read-only."""
        if self._layout_model is None:
            raise LayoutError(
                "Layout model is not available — process() has not been called."
            )
        return deepcopy(self._layout_model)

    # ------------------------------------------------------------------
    # Processing entry point
    # ------------------------------------------------------------------

    def process(
        self,
        state: ActivatedState,
        theme: ThemeService,
        project_root: Path,
    ) -> None:
        """
        Execute Layout Processing.

        Args:
            state:        Activated framework state (ACT-001).
            theme:        Completed Theme Service (THEME-001, THEME-002).
            project_root: Project root for resolving asset paths.

        Raises:
            LayoutError: If no layout is activated or the layout asset
                         cannot be loaded (CC-003).
        """
        # Step 1 — resolve active layout from ACT-001
        layout_entity = state.get_first(EntityType.LAYOUT)
        if layout_entity is None:
            raise LayoutError(
                "No Layout is activated. "
                "Register a Layout entity before running Layout Processing."
            )

        configured_path = project_root / layout_entity.source_path
        layout_path = (
            configured_path / "layout.yaml"
            if configured_path.is_dir()
            else configured_path
        )

        # Step 2 — load layout asset → LayoutModel (LAYOUT-002)
        self._layout_model = self._load_layout(layout_path)

        # Step 3 — assign placement rules and build DocumentStructure (LAYOUT-001)
        styled_content = theme.styled_content
        self._document = self._build_structure(styled_content, self._layout_model)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_layout(self, layout_path: Path) -> LayoutModel:
        """Load and validate the layout.yaml asset."""
        if not layout_path.exists():
            raise LayoutError(f"Layout asset not found: {layout_path}")

        try:
            raw = yaml.safe_load(layout_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise LayoutError(f"Failed to parse layout asset: {exc}") from exc

        if not isinstance(raw, dict):
            raise LayoutError("Layout asset must be a YAML mapping.")

        # Page config
        page_raw = raw.get("page", {})
        page = PageConfig(
            size=str(page_raw.get("size", "A4")),
            margin_top_mm=float(page_raw.get("margin_top_mm", 25)),
            margin_bottom_mm=float(page_raw.get("margin_bottom_mm", 25)),
            margin_left_mm=float(page_raw.get("margin_left_mm", 30)),
            margin_right_mm=float(page_raw.get("margin_right_mm", 25)),
            columns=int(page_raw.get("columns", 1)),
        )

        # Placement rules
        placement: dict[str, PlacementRule] = {}
        for node_type, rule_data in raw.get("placement", {}).items():
            if not isinstance(rule_data, dict):
                continue
            placement[node_type] = PlacementRule(
                page_break_before=bool(rule_data.get("page_break_before", False)),
                keep_with_next=bool(rule_data.get("keep_with_next", False)),
                spacing_before_mm=float(rule_data.get("spacing_before_mm", 4)),
                spacing_after_mm=float(rule_data.get("spacing_after_mm", 4)),
            )

        # Appendix config
        appendix_raw = raw.get("appendix", {})
        appendix = AppendixConfig(
            enabled=bool(appendix_raw.get("enabled", False)),
            title=str(appendix_raw.get("title", "Solutions")),
            page_break_before=bool(appendix_raw.get("page_break_before", True)),
        )

        return LayoutModel(
            layout_id=str(raw.get("id", "unknown")),
            layout_name=str(raw.get("name", "")),
            version=str(raw.get("version", "1.0.0")),
            page=page,
            placement=placement,
            section_order=list(raw.get("section_order", [])),
            appendix=appendix,
        )

    def _build_structure(
        self, styled_content: StyledContent, layout_model: LayoutModel
    ) -> DocumentStructure:
        """Build ordered elements and stable exercise/solution references."""
        elements: list[DocumentElement] = []
        prose_blocks: list[tuple[int, TextBlock]] = []
        appendix_nodes: list[StyledNode] = []
        solution_references: list[SolutionReference] = []
        position = 0
        exercise_index = 0

        for item in styled_content.items:
            if isinstance(item, TextBlock):
                prose_blocks.append((position, item))
                position += 1
                continue
            if not isinstance(item, StyledNode):
                continue

            exercise_id = ""
            solution_id = ""
            solution_index = 0
            if item.node_type == "exercise":
                exercise_index += 1
                exercise_id = f"exercise-{exercise_index}"
                solution = next(
                    (child for child in item.children if child.node_type == "solution"),
                    None,
                )
                if solution is not None and layout_model.appendix.enabled:
                    solution_index = exercise_index
                    solution_id = f"solution-{solution_index}"
                    exercise_title = self._extract_title(item.body)[0]
                    solution_title = self._extract_title(solution.body)[0]
                    appendix_nodes.append(solution)
                    solution_references.append(SolutionReference(
                        index=solution_index,
                        exercise_id=exercise_id,
                        solution_id=solution_id,
                        exercise_title=exercise_title,
                        solution_title=solution_title,
                    ))

            # Solutions remain semantic children of exercises and never become
            # body elements. Top-level solutions are also kept out of the body.
            if item.node_type == "solution":
                if layout_model.appendix.enabled:
                    appendix_nodes.append(item)
                continue

            placement = layout_model.get_placement(item.node_type)
            elements.append(DocumentElement(
                styled_node=item,
                placement=placement,
                position_index=position,
                exercise_id=exercise_id,
                solution_id=solution_id,
                solution_index=solution_index,
            ))
            position += 1

        return DocumentStructure(
            elements=elements,
            prose_blocks=prose_blocks,
            layout_model=layout_model,
            appendix_nodes=appendix_nodes,
            solution_references=solution_references,
        )

    @staticmethod
    def _extract_title(body: str) -> tuple[str, str]:
        lines = body.strip().splitlines()
        if lines and lines[0].startswith("title:"):
            return lines[0][len("title:"):].strip(), "\n".join(lines[1:]).lstrip("\n")
        return "", body.strip()
