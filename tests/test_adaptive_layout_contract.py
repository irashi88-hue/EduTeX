from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from types import SimpleNamespace

import pytest

from edutex.layout.adaptive import parse_adaptive_config, resolve_adaptive_placement
from edutex.layout.models import (
    AdaptivePlacementRule,
    AppendixConfig,
    LayoutModel,
    PageConfig,
    PlacementRule,
)
from edutex.layout.service import LayoutService


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "ADAPTIVE_LAYOUT_CONTRACT.md"
ADAPTIVE = ROOT / "src" / "edutex" / "layout" / "adaptive.py"
SERVICE = ROOT / "src" / "edutex" / "layout" / "service.py"


def write_layout(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(text).strip() + "\n", encoding="utf-8")


def test_adaptive_config_is_opt_in_and_parses_rules() -> None:
    enabled, rules = parse_adaptive_config({})
    assert enabled is False
    assert rules == {}

    enabled, rules = parse_adaptive_config({
        "enabled": True,
        "rules": [{
            "node_type": "exercise",
            "min_count": 6,
            "page_break_every": 4,
            "spacing_before_mm": 10,
        }],
    })

    assert enabled is True
    assert rules["exercise"] == AdaptivePlacementRule(
        node_type="exercise",
        min_count=6,
        page_break_every=4,
        spacing_before_mm=10.0,
    )


def test_adaptive_config_rejects_invalid_rules() -> None:
    with pytest.raises(ValueError, match="mapping"):
        parse_adaptive_config([])
    with pytest.raises(ValueError, match="min_count"):
        parse_adaptive_config({"rules": [{"node_type": "exercise", "min_count": 0, "spacing_before_mm": 2}]})
    with pytest.raises(ValueError, match="page_break_every"):
        parse_adaptive_config({"rules": [{"node_type": "exercise", "page_break_every": 1}]})
    with pytest.raises(ValueError, match="duplicate adaptive node_type"):
        parse_adaptive_config({"rules": [
            {"node_type": "exercise", "spacing_before_mm": 2},
            {"node_type": "exercise", "spacing_after_mm": 3},
        ]})
    with pytest.raises(ValueError, match="unknown adaptive rule fields"):
        parse_adaptive_config({"rules": [{"node_type": "exercise", "column_count": 2}]})


def test_threshold_spacing_and_periodic_breaks_are_deterministic() -> None:
    base = PlacementRule(False, False, 4.0, 4.0)
    rule = AdaptivePlacementRule(
        node_type="exercise",
        min_count=6,
        page_break_every=4,
        spacing_before_mm=10.0,
    )

    assert resolve_adaptive_placement(
        base, rule, occurrence_index=4, total_count=5
    ) is base
    first = resolve_adaptive_placement(base, rule, occurrence_index=1, total_count=8)
    fourth = resolve_adaptive_placement(base, rule, occurrence_index=4, total_count=8)
    fifth = resolve_adaptive_placement(base, rule, occurrence_index=5, total_count=8)

    assert first.spacing_before_mm == 10.0
    assert first.page_break_before is False
    assert fourth.page_break_before is True
    assert fourth.spacing_before_mm == 10.0
    assert fifth.page_break_before is False


def test_explicit_per_type_values_override_adaptation_field_by_field() -> None:
    explicit = PlacementRule(False, True, 4.0, 6.0)
    rule = AdaptivePlacementRule(
        node_type="exercise",
        min_count=2,
        page_break_every=2,
        spacing_before_mm=9.0,
        spacing_after_mm=12.0,
    )

    result = resolve_adaptive_placement(
        explicit,
        rule,
        occurrence_index=2,
        total_count=4,
        explicit_fields={"page_break_before", "spacing_after_mm"},
    )

    assert result.page_break_before is False
    assert result.spacing_before_mm == 9.0
    assert result.spacing_after_mm == 6.0


def test_layout_loader_preserves_opt_in_and_explicit_field_provenance(tmp_path: Path) -> None:
    layout_path = tmp_path / "layouts" / "adaptive" / "layout.yaml"
    write_layout(layout_path, """
        id: adaptive
        name: Adaptive
        page:
          size: A4
        placement:
          _default:
            page_break_before: false
            spacing_before_mm: 4
          exercise:
            keep_with_next: true
        adaptive:
          enabled: true
          rules:
            - node_type: exercise
              min_count: 6
              page_break_every: 4
              spacing_before_mm: 10
    """)

    model = LayoutService()._load_layout(layout_path, tmp_path)

    assert model.adaptive_enabled is True
    assert model.adaptive_rules["exercise"].min_count == 6
    assert model.explicit_placement_fields["exercise"] == frozenset({"keep_with_next"})
    assert model.explicit_placement_fields["_default"] == frozenset({
        "page_break_before", "spacing_before_mm"
    })


def test_layout_service_applies_adaptive_rule_to_content_counts(monkeypatch) -> None:
    import edutex.layout.service as service_module

    class FakeNode:
        def __init__(self, node_type: str) -> None:
            self.node_type = node_type
            self.children = []
            self.body = ""

    monkeypatch.setattr(service_module, "StyledNode", FakeNode)
    content = SimpleNamespace(items=[FakeNode("exercise") for _ in range(6)])
    model = LayoutModel(
        layout_id="adaptive",
        layout_name="Adaptive",
        version="1.0.0",
        page=PageConfig("A4", 25, 25, 30, 25, 1),
        placement={"_default": PlacementRule(False, False, 4.0, 4.0)},
        appendix=AppendixConfig(False, "Solutions", True),
        adaptive_enabled=True,
        adaptive_rules={
            "exercise": AdaptivePlacementRule(
                "exercise", min_count=6, page_break_every=3, spacing_before_mm=8.0
            )
        },
    )

    document = LayoutService()._build_structure(content, model)
    placements = [element.placement for element in document.elements]

    assert len(placements) == 6
    assert [index + 1 for index, item in enumerate(placements) if item.page_break_before] == [3, 6]
    assert all(item.spacing_before_mm == 8.0 for item in placements)


def test_adaptive_contract_documentation_and_service_markers() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    adaptive = ADAPTIVE.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")

    for marker in ("opt-in", "page_break_every", "valori espliciti", "min_count", "determinismo"):
        assert marker in contract
    assert "resolve_adaptive_placement" in adaptive
    assert "parse_adaptive_config" in adaptive
    assert "resolve_adaptive_placement" in service
