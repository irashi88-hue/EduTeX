"""Safe, deterministic composition of EduTeX theme assets."""

from __future__ import annotations

import re
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path

import yaml

_THEME_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_COMPOSABLE_FIELDS = ("styles", "palette", "tokens")


class ThemeCompositionError(ValueError):
    """Raised when theme inheritance is invalid or unsafe."""


def _merge_mapping(target: dict, layer: Mapping) -> None:
    """Recursively merge mappings; non-mapping values (including lists) replace."""
    for key, value in layer.items():
        if isinstance(value, Mapping) and isinstance(target.get(key), Mapping):
            nested = dict(target[key])
            _merge_mapping(nested, value)
            target[key] = nested
        elif isinstance(value, Mapping):
            nested = {}
            _merge_mapping(nested, value)
            target[key] = nested
        else:
            target[key] = deepcopy(value)


def _theme_mapping(path: Path) -> dict:
    if not path.is_file():
        raise ThemeCompositionError(f"Theme asset not found: {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ThemeCompositionError(f"Could not load theme asset {path}: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise ThemeCompositionError(f"Theme asset must be a YAML mapping: {path}")
    return dict(raw)


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _load_layer(path: Path, root: Path, stack: tuple[Path, ...]) -> dict:
    resolved = path.resolve()
    if not _within(resolved, root):
        raise ThemeCompositionError(f"Theme reference escapes theme root: {path}")
    if resolved in stack:
        chain = " -> ".join(item.name for item in (*stack, resolved))
        raise ThemeCompositionError(f"Theme inheritance cycle: {chain}")

    raw = _theme_mapping(resolved)
    parents = raw.get("extends", [])
    if not isinstance(parents, list):
        raise ThemeCompositionError("theme.extends must be a list of theme directory IDs")
    seen: set[str] = set()
    merged = {field: {} for field in _COMPOSABLE_FIELDS}
    next_stack = (*stack, resolved)

    for parent in parents:
        if not isinstance(parent, str) or not _THEME_ID.fullmatch(parent):
            raise ThemeCompositionError("theme.extends entries must be simple theme IDs")
        if parent in seen:
            raise ThemeCompositionError(f"duplicate theme parent: {parent}")
        seen.add(parent)
        parent_path = root / parent / "theme.yaml"
        inherited = _load_layer(parent_path, root, next_stack)
        for field in _COMPOSABLE_FIELDS:
            _merge_mapping(merged[field], inherited.get(field, {}))

    for field in _COMPOSABLE_FIELDS:
        layer = raw.get(field, {})
        if not isinstance(layer, Mapping):
            raise ThemeCompositionError(f"theme.{field} must be a mapping")
        _merge_mapping(merged[field], layer)

    # Identity and other metadata always come from the selected theme, never parents.
    result = {key: deepcopy(value) for key, value in raw.items() if key not in (*_COMPOSABLE_FIELDS, "extends")}
    result.update(merged)
    return result


def load_composed_theme(theme_path: Path, theme_root: Path | None = None) -> dict:
    """Load a theme and its ordered parents, confined to sibling theme folders."""
    selected = Path(theme_path).resolve()
    root = Path(theme_root).resolve() if theme_root is not None else selected.parent.parent.resolve()
    if not _within(selected, root):
        raise ThemeCompositionError(f"Selected theme is outside theme root: {selected}")
    return _load_layer(selected, root, ())

def inspect_composed_theme(
    theme_path: Path,
    theme_root: Path | None = None,
) -> dict[str, object]:
    """Return effective theme styles and deterministic layer provenance.

    ``source`` paths are relative to ``theme_root``. Layers are listed in
    application order (base first, selected theme last). Theme style fields
    are materialized with the same defaults used by ``ThemeService``.
    """
    selected = Path(theme_path).resolve()
    root = Path(theme_root).resolve() if theme_root is not None else selected.parent.parent.resolve()
    effective = load_composed_theme(selected, root)
    layers: list[tuple[str, dict[str, object]]] = []

    def collect(path: Path, active_stack: tuple[Path, ...]) -> None:
        resolved = path.resolve()
        if not _within(resolved, root):
            raise ThemeCompositionError(f"Theme reference escapes theme root: {path}")
        if resolved in active_stack:
            chain = " -> ".join(item.name for item in (*active_stack, resolved))
            raise ThemeCompositionError(f"Theme inheritance cycle: {chain}")
        raw = _theme_mapping(resolved)
        parents = raw.get("extends", [])
        for parent in parents:
            collect(root / parent / "theme.yaml", (*active_stack, resolved))
        own = {
            field: deepcopy(raw.get(field, {}))
            for field in _COMPOSABLE_FIELDS
        }
        source = resolved.relative_to(root).as_posix()
        metadata = {
            "id": raw.get("id"),
            "name": raw.get("name"),
            "version": raw.get("version"),
        }
        layers.append((source, {**own, **metadata}))

    collect(selected, ())

    provenance: dict[str, str] = {}
    overrides: list[dict[str, str]] = []

    def record_fields(value: object, prefix: str, source: str) -> None:
        if isinstance(value, Mapping) and value:
            for key, child in value.items():
                field = f"{prefix}.{key}" if prefix else str(key)
                record_fields(child, field, source)
            return
        previous = provenance.get(prefix)
        if previous is not None:
            overrides.append({
                "field": prefix,
                "overridden_from": previous,
                "overridden_by": source,
            })
        provenance[prefix] = source

    layer_records: list[dict[str, object]] = []
    for source, definition in layers:
        layer_records.append({
            "source": source,
            "id": definition.get("id"),
            "name": definition.get("name"),
            "version": definition.get("version"),
        })
        for field in _COMPOSABLE_FIELDS:
            value = definition.get(field, {})
            if isinstance(value, Mapping):
                for key, child in value.items():
                    record_fields(child, f"{field}.{key}", source)

    effective.setdefault("id", "unknown")
    effective.setdefault("name", "")
    effective.setdefault("version", "1.0.0")
    raw_styles = effective.get("styles", {})
    resolved_styles: dict[str, dict[str, str]] = {}
    if isinstance(raw_styles, Mapping):
        for node_type, rule in raw_styles.items():
            if not isinstance(rule, Mapping):
                continue
            resolved_styles[str(node_type)] = {
                "label": str(rule.get("label", "")),
                "border_color": str(rule.get("border_color", "")),
                "background_color": str(rule.get("background_color", "")),
                "font_weight": str(rule.get("font_weight", "normal")),
                "display": str(rule.get("display", "block")),
            }
    effective["styles"] = resolved_styles
    palette = effective.get("palette", {})
    if isinstance(palette, Mapping):
        effective["palette"] = {str(key): str(value) for key, value in palette.items()}

    return {
        "source_path": selected.relative_to(root).as_posix(),
        "effective": effective,
        "composition": {
            "layers": layer_records,
            "provenance": provenance,
            "overrides": overrides,
        },
    }
