"""Opt-in, deterministic content-aware placement for EduTeX layouts."""

from __future__ import annotations

import math
from collections.abc import Collection, Mapping
from dataclasses import replace

from edutex.layout.models import AdaptivePlacementRule, PlacementRule


_RULE_KEYS = {
    "node_type",
    "min_count",
    "page_break_every",
    "spacing_before_mm",
    "spacing_after_mm",
}


def _spacing_value(value: object, field: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite non-negative number")
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"{field} must be a finite non-negative number")
    return result


def parse_adaptive_config(
    value: object,
) -> tuple[bool, dict[str, AdaptivePlacementRule]]:
    """Validate the optional adaptive YAML section without mutating it."""
    if not isinstance(value, Mapping):
        raise ValueError("adaptive must be a YAML mapping")
    unknown_top_level = set(value) - {"enabled", "rules"}
    if unknown_top_level:
        names = ", ".join(sorted(str(item) for item in unknown_top_level))
        raise ValueError(f"unknown adaptive fields: {names}")

    enabled = value.get("enabled", False)
    if not isinstance(enabled, bool):
        raise ValueError("adaptive.enabled must be a boolean")
    raw_rules = value.get("rules", [])
    if not isinstance(raw_rules, list):
        raise ValueError("adaptive.rules must be a list")

    rules: dict[str, AdaptivePlacementRule] = {}
    for index, raw_rule in enumerate(raw_rules, start=1):
        if not isinstance(raw_rule, Mapping):
            raise ValueError(f"adaptive rule {index} must be a mapping")
        unknown = set(raw_rule) - _RULE_KEYS
        if unknown:
            names = ", ".join(sorted(str(item) for item in unknown))
            raise ValueError(f"unknown adaptive rule fields: {names}")

        node_type = raw_rule.get("node_type")
        if (
            not isinstance(node_type, str)
            or not node_type
            or node_type != node_type.strip()
            or node_type == "_default"
        ):
            raise ValueError(f"adaptive rule {index} requires a concrete node_type")
        if node_type in rules:
            raise ValueError(f"duplicate adaptive node_type: {node_type}")

        min_count = raw_rule.get("min_count", 1)
        if type(min_count) is not int or min_count < 1:
            raise ValueError("min_count must be a positive integer")
        interval = raw_rule.get("page_break_every")
        if interval is not None and (type(interval) is not int or interval < 2):
            raise ValueError("page_break_every must be an integer of at least 2")
        spacing_before = _spacing_value(raw_rule.get("spacing_before_mm"), "spacing_before_mm")
        spacing_after = _spacing_value(raw_rule.get("spacing_after_mm"), "spacing_after_mm")
        if interval is None and spacing_before is None and spacing_after is None:
            raise ValueError(f"adaptive rule {node_type} must define at least one placement effect")

        rules[node_type] = AdaptivePlacementRule(
            node_type=node_type,
            min_count=min_count,
            page_break_every=interval,
            spacing_before_mm=spacing_before,
            spacing_after_mm=spacing_after,
        )
    return enabled, rules


def resolve_adaptive_placement(
    placement: PlacementRule,
    rule: AdaptivePlacementRule,
    *,
    occurrence_index: int,
    total_count: int,
    explicit_fields: Collection[str] = (),
) -> PlacementRule:
    """Apply an adaptive rule only after its total-count threshold is reached.

    Occurrence indices are one-based. Page breaks are introduced before each
    matching interval (never before the first item). Explicit per-node placement
    fields always win; `_default` remains a fallback for fields not specified on
    the concrete node type.
    """
    if occurrence_index < 1 or total_count < 0 or occurrence_index > total_count:
        raise ValueError("occurrence_index and total_count are inconsistent")
    if total_count < rule.min_count:
        return placement

    explicit = set(explicit_fields)
    changes: dict[str, object] = {}
    if (
        rule.page_break_every is not None
        and "page_break_before" not in explicit
        and occurrence_index > 1
        and occurrence_index % rule.page_break_every == 0
    ):
        changes["page_break_before"] = True
    if rule.spacing_before_mm is not None and "spacing_before_mm" not in explicit:
        changes["spacing_before_mm"] = rule.spacing_before_mm
    if rule.spacing_after_mm is not None and "spacing_after_mm" not in explicit:
        changes["spacing_after_mm"] = rule.spacing_after_mm
    return replace(placement, **changes) if changes else placement
