"""
EduTeX Knowledge Service
Component: Knowledge (COMP-KNOW-001)
Contracts: KNOW-001 (Knowledge Content Contract), KNOW-002 (Knowledge Model Contract)

Orchestrates Knowledge Processing:
  1. Reads the active Knowledge Model path from the ActivatedState (ACT-001).
  2. Loads and validates the frontmatter via the loader.
  3. Parses the body via the shortcode parser.
  4. Produces the ContentModel (KNOW-001) and KnowledgeModelMeta (KNOW-002).

Both outputs are read-only after processing completes.

Note: the shortcode parser (parser.py) returns plain dicts, not dataclass instances.
"""

from __future__ import annotations

from pathlib import Path

from edutex.activator.activator import ActivatedState
from edutex.core.errors import KnowledgeError
from edutex.knowledge.loader import KnowledgeModelMeta, load_knowledge_model
from edutex.knowledge.models import ContentModel, ContentNode, TextBlock
from edutex.knowledge.parser import parse
from edutex.registry.models import EntityType


class KnowledgeService:
    """
    Knowledge Service — orchestrates Knowledge Processing (COMP-KNOW-001).

    Usage:
        service = KnowledgeService()
        service.process(activated_state, project_root)

        meta    = service.meta     # KNOW-002
        content = service.content  # KNOW-001
    """

    def __init__(self) -> None:
        self._meta:    KnowledgeModelMeta | None = None
        self._content: ContentModel | None = None

    # ------------------------------------------------------------------
    # KNOW-001 — Knowledge Content Contract
    # ------------------------------------------------------------------

    @property
    def content(self) -> ContentModel:
        """
        The fully parsed, validated content model (KNOW-001).
        Available only after process() completes successfully.
        """
        if self._content is None:
            raise KnowledgeError(
                "Knowledge content is not available — process() has not been called."
            )
        return self._content

    # ------------------------------------------------------------------
    # KNOW-002 — Knowledge Model Contract
    # ------------------------------------------------------------------

    @property
    def meta(self) -> KnowledgeModelMeta:
        """
        The validated Knowledge Model metadata (KNOW-002).
        Available only after process() completes successfully.
        """
        if self._meta is None:
            raise KnowledgeError(
                "Knowledge metadata is not available — process() has not been called."
            )
        return self._meta

    # ------------------------------------------------------------------
    # Processing entry point
    # ------------------------------------------------------------------

    def process(self, state: ActivatedState, project_root: Path) -> None:
        """
        Execute Knowledge Processing.

        Args:
            state:        The activated framework state (ACT-001).
            project_root: The project root directory (used to resolve relative paths).

        Raises:
            KnowledgeError: If no Knowledge Model is activated, the file cannot
                            be loaded, or parsing fails (CC-003).
        """
        # Step 1 — resolve the active Knowledge Model from ACT-001
        km_entity = state.get_first(EntityType.KNOWLEDGE_MODEL)
        if km_entity is None:
            raise KnowledgeError(
                "No Knowledge Model is activated. "
                "Register a Knowledge Model entity before running Knowledge Processing."
            )

        km_path = km_entity.source_path if km_entity.source_path.is_absolute() else project_root / km_entity.source_path

        # Step 2 — load and validate frontmatter (KNOW-002)
        meta, body = load_knowledge_model(km_path)
        self._meta = meta

        # Step 3 — parse shortcode body (KNOW-001)
        self._content = self._parse_body(body)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_body(self, body: str) -> ContentModel:
        """
        Parse the Knowledge Model body using the shortcode parser
        and convert the AST (list of dicts) into a typed ContentModel.
        """
        try:
            ast = parse(body)
        except Exception as exc:
            raise KnowledgeError(f"Shortcode parsing failed: {exc}") from exc

        items = []
        for node in ast:
            if node["kind"] == "text":
                if node["content"].strip():
                    items.append(TextBlock(content=node["content"]))
            elif node["kind"] == "shortcode":
                items.append(self._convert_node(node))

        return ContentModel(items=items)

    def _convert_node(self, node: dict) -> ContentNode:
        """Recursively convert a parser dict node into a typed ContentNode."""
        children = [
            self._convert_node(c)
            for c in node.get("children", [])
            if c.get("kind") == "shortcode"
        ]
        return ContentNode(
            node_type=node["type"],
            subtype=node.get("subtype"),
            fields=node.get("fields", []),
            body=node.get("body", ""),
            children=children,
            source_line=node.get("line", 0),
        )
