from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from edutex.layout.composition import (
    LayoutCompositionError,
    compose_layout_definitions,
    load_composed_layout,
)
from edutex.layout.service import LayoutService


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "LAYOUT_COMPOSITION_CONTRACT.md"
COMPOSITION = ROOT / "src" / "edutex" / "layout" / "composition.py"
SERVICE = ROOT / "src" / "edutex" / "layout" / "service.py"


def write_layout(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(text).strip() + "\n", encoding="utf-8")


def test_composition_deep_merges_maps_replaces_lists_and_preserves_inputs() -> None:
    base = {
        "id": "base",
        "name": "Base",
        "version": "1.0.0",
        "page": {"size": "A4", "margins": {"top": 20, "left": 30}},
        "placement": {"exercise": {"keep_with_next": True, "spacing_before_mm": 4}},
        "section_order": ["rule", "exercise"],
    }
    overlay = {
        "id": "active",
        "name": "Active",
        "page": {"margins": {"top": 12, "right": 18}},
        "placement": {"exercise": {"spacing_after_mm": 7}},
        "section_order": ["exercise", "rule"],
    }
    original_base = {key: value.copy() if isinstance(value, dict) else value for key, value in base.items()}

    result = compose_layout_definitions((base, overlay))

    assert result["id"] == "active"
    assert result["version"] == "1.0.0"
    assert result["page"] == {"size": "A4", "margins": {"top": 12, "left": 30, "right": 18}}
    assert result["placement"] == {
        "exercise": {"keep_with_next": True, "spacing_before_mm": 4, "spacing_after_mm": 7}
    }
    assert result["section_order"] == ["exercise", "rule"]
    assert "extends" not in result
    assert base == original_base


def test_composition_rejects_empty_layers_and_non_mapping() -> None:
    with pytest.raises(LayoutCompositionError, match="At least one"):
        compose_layout_definitions(())
    with pytest.raises(LayoutCompositionError, match="mapping"):
        compose_layout_definitions(({"id": "base"}, 7))  # type: ignore[arg-type]


def test_ordered_extends_composes_multiple_parents_and_service_loads_model(tmp_path: Path) -> None:
    project = tmp_path / "project"
    write_layout(
        project / "layouts" / "base" / "layout.yaml",
        """
        id: base
        name: Base
        version: 1.0.0
        page:
          margin_top_mm: 10
          margin_left_mm: 20
        placement:
          exercise:
            keep_with_next: true
            spacing_before_mm: 6
        section_order: [rule, exercise]
        """,
    )
    write_layout(
        project / "layouts" / "spacing" / "layout.yaml",
        """
        id: spacing
        name: Spacing
        version: 1.0.0
        page:
          margin_top_mm: 15
        placement:
          exercise:
            spacing_after_mm: 7
        section_order: [example, exercise]
        """,
    )
    active = project / "layouts" / "active" / "layout.yaml"
    write_layout(
        active,
        """
        id: active
        name: Active
        version: 2.0.0
        extends:
          - ../base/layout.yaml
          - ../spacing/layout.yaml
        page:
          margin_right_mm: 18
        placement:
          exercise:
            page_break_before: true
        """,
    )

    resolved = load_composed_layout(active, project)
    model = LayoutService()._load_layout(active, project)

    assert resolved["id"] == "active"
    assert resolved["name"] == "Active"
    assert "extends" not in resolved
    assert resolved["page"] == {
        "margin_top_mm": 15,
        "margin_left_mm": 20,
        "margin_right_mm": 18,
    }
    assert resolved["section_order"] == ["example", "exercise"]
    exercise = resolved["placement"]["exercise"]
    assert exercise == {
        "keep_with_next": True,
        "spacing_before_mm": 6,
        "spacing_after_mm": 7,
        "page_break_before": True,
    }
    assert model.layout_id == "active"
    assert model.page.margin_top_mm == 15
    assert model.page.margin_left_mm == 20
    assert model.page.margin_right_mm == 18
    assert model.placement["exercise"].keep_with_next is True
    assert model.placement["exercise"].page_break_before is True
    assert model.placement["exercise"].spacing_before_mm == 6
    assert model.placement["exercise"].spacing_after_mm == 7
    assert model.section_order == ["example", "exercise"]


def test_single_layout_without_extends_retains_its_identity_and_values(tmp_path: Path) -> None:
    layout = tmp_path / "project" / "layouts" / "default" / "layout.yaml"
    write_layout(
        layout,
        """
        id: default
        name: Default
        version: 1.0.0
        page:
          size: A4
        section_order: [rule, exercise]
        """,
    )

    resolved = load_composed_layout(layout, layout.parents[2])

    assert resolved["id"] == "default"
    assert resolved["name"] == "Default"
    assert resolved["page"] == {"size": "A4"}
    assert resolved["section_order"] == ["rule", "exercise"]


def test_extends_rejects_cycles_missing_files_and_invalid_references(tmp_path: Path) -> None:
    project = tmp_path / "project"
    first = project / "layouts" / "first" / "layout.yaml"
    second = project / "layouts" / "second" / "layout.yaml"
    write_layout(first, """
        id: first
        extends: ../second/layout.yaml
    """)
    write_layout(second, """
        id: second
        extends: ../first/layout.yaml
    """)
    with pytest.raises(LayoutCompositionError, match="cycle"):
        load_composed_layout(first, project)

    missing = project / "layouts" / "missing-child" / "layout.yaml"
    write_layout(missing, """
        id: missing-child
        extends: ../absent/layout.yaml
    """)
    with pytest.raises(LayoutCompositionError, match="not found"):
        load_composed_layout(missing, project)

    invalid = project / "layouts" / "invalid" / "layout.yaml"
    write_layout(invalid, """
        id: invalid
        extends:
          - 7
    """)
    with pytest.raises(LayoutCompositionError, match="path strings"):
        load_composed_layout(invalid, project)


def test_extends_cannot_escape_project_root_or_use_absolute_paths(tmp_path: Path) -> None:
    project = tmp_path / "project"
    outside = project / "layouts" / "child" / "layout.yaml"
    write_layout(outside, """
        id: child
        extends: ../../../outside/layout.yaml
    """)
    with pytest.raises(LayoutCompositionError, match="outside project_root"):
        load_composed_layout(outside, project)

    absolute = project / "layouts" / "absolute" / "layout.yaml"
    write_layout(absolute, f"""
        id: absolute
        extends: {str(tmp_path / 'external' / 'layout.yaml')}
    """)
    with pytest.raises(LayoutCompositionError, match="must be relative"):
        load_composed_layout(absolute, project)


def test_layout_composition_contract_markers_are_present() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    implementation = COMPOSITION.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")

    for marker in ("extends", "ordine", "precedenza", "ciclo", "project_root"):
        assert marker in contract
    for marker in ("compose_layout_definitions", "load_composed_layout", "cycle"):
        assert marker in implementation
    assert "load_composed_layout" in service
