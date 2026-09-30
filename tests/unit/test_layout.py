"""Unit tests for the Layout public contracts."""

from pathlib import Path


def test_public_layout_api_exports_contract():
    import edutex.layout as public_layout
    from edutex.layout.models import (
        AppendixConfig,
        DocumentElement,
        DocumentStructure,
        LayoutModel,
        PageConfig,
        PlacementRule,
        SolutionReference,
    )
    from edutex.layout.service import LayoutService

    expected = {
        "AppendixConfig": AppendixConfig,
        "DocumentElement": DocumentElement,
        "DocumentStructure": DocumentStructure,
        "LayoutModel": LayoutModel,
        "LayoutService": LayoutService,
        "PageConfig": PageConfig,
        "PlacementRule": PlacementRule,
        "SolutionReference": SolutionReference,
    }

    for name, expected_value in expected.items():
        assert getattr(public_layout, name) is expected_value
        assert name in public_layout.__all__


def test_layout_service_contract_requires_processing():
    import pytest

    from edutex.core.errors import LayoutError
    from edutex.layout import LayoutService

    service = LayoutService()

    with pytest.raises(LayoutError, match="process"):
        _ = service.document

    with pytest.raises(LayoutError, match="process"):
        _ = service.layout_model

def test_layout_service_does_not_expose_mutable_state(tmp_path):
    from edutex.activator.activator import ActivatedEntity, ActivatedState
    from edutex.knowledge import KnowledgeService
    from edutex.registry.models import EntityRecord, EntityType
    from edutex.theme import ThemeService
    from edutex.layout import LayoutService

    (tmp_path / "knowledge.md").write_text(
        """---
id: km-001
title: Test Knowledge Model
language: it
level: A1
version: 1.0.0
---

Plain educational content.
""",
        encoding="utf-8",
    )

    theme_path = tmp_path / "themes" / "default"
    theme_path.mkdir(parents=True)
    (theme_path / "theme.yaml").write_text(
        """id: theme-001
name: Default
version: 1.0.0
styles:
  _default:
    label: Default
    border_color: "#000000"
    background_color: "#ffffff"
    font_weight: normal
    display: block
""",
        encoding="utf-8",
    )

    layout_path = tmp_path / "layouts" / "default"
    layout_path.mkdir(parents=True)
    (layout_path / "layout.yaml").write_text(
        """id: layout-001
name: Default
version: 1.0.0
page:
  size: A4
  margin_top_mm: 25
  margin_bottom_mm: 25
  margin_left_mm: 30
  margin_right_mm: 25
  columns: 1
placement:
  _default:
    page_break_before: false
    keep_with_next: false
    spacing_before_mm: 4
    spacing_after_mm: 4
section_order: []
appendix:
  enabled: false
  title: Solutions
  page_break_before: true
""",
        encoding="utf-8",
    )

    state = ActivatedState(
        [
            ActivatedEntity(
                record=EntityRecord(
                    "km-001",
                    EntityType.KNOWLEDGE_MODEL,
                    Path("knowledge.md"),
                )
            ),
            ActivatedEntity(
                record=EntityRecord(
                    "theme-001",
                    EntityType.THEME,
                    Path("themes/default"),
                )
            ),
            ActivatedEntity(
                record=EntityRecord(
                    "layout-001",
                    EntityType.LAYOUT,
                    Path("layouts/default"),
                )
            ),
        ]
    )

    knowledge = KnowledgeService()
    knowledge.process(state, tmp_path)

    theme = ThemeService()
    theme.process(state, knowledge, tmp_path)

    service = LayoutService()
    service.process(state, theme, tmp_path)

    exposed_document = service.document
    exposed_model = service.layout_model

    exposed_document.prose_blocks.clear()
    exposed_model.placement.clear()

    assert len(service.document.prose_blocks) == 1
    assert "_default" in service.layout_model.placement
