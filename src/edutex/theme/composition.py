"""Safe, deterministic composition of EduTeX theme assets."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
import re

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
