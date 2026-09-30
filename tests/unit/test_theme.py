"""Unit tests for the Theme public contracts."""

from pathlib import Path


def test_public_theme_api_exports_contract():
    import edutex.theme as public_theme
    from edutex.theme.models import StyleRule, StyledContent, StyledNode, ThemeModel
    from edutex.theme.service import ThemeService

    expected = {
        "StyleRule": StyleRule,
        "StyledContent": StyledContent,
        "StyledNode": StyledNode,
        "ThemeModel": ThemeModel,
        "ThemeService": ThemeService,
    }

    for name, expected_value in expected.items():
        assert getattr(public_theme, name) is expected_value
        assert name in public_theme.__all__


def test_theme_service_contract_requires_processing():
    import pytest

    from edutex.core.errors import ThemeError
    from edutex.theme import ThemeService

    service = ThemeService()

    with pytest.raises(ThemeError, match="process"):
        _ = service.styled_content

    with pytest.raises(ThemeError, match="process"):
        _ = service.theme_model

def test_theme_service_does_not_expose_mutable_state(tmp_path):
    from edutex.activator.activator import ActivatedEntity, ActivatedState
    from edutex.knowledge import KnowledgeService
    from edutex.registry.models import EntityRecord, EntityType
    from edutex.theme import ThemeService

    knowledge_path = tmp_path / "knowledge.md"
    knowledge_path.write_text(
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
        ]
    )

    knowledge = KnowledgeService()
    knowledge.process(state, tmp_path)

    service = ThemeService()
    service.process(state, knowledge, tmp_path)

    exposed_content = service.styled_content
    exposed_model = service.theme_model

    exposed_content.items.clear()
    exposed_model.styles.clear()

    assert len(service.styled_content.items) == 1
    assert "_default" in service.theme_model.styles
