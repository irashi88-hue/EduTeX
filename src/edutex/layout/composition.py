"""Deterministic loading and composition of EduTeX layout definitions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path

import yaml


class LayoutCompositionError(ValueError):
    """Raised when layout inheritance or layered composition is invalid."""


def _merge_mapping(base: Mapping[str, object], overlay: Mapping[str, object]) -> dict[str, object]:
    merged = deepcopy(dict(base))
    for key, value in overlay.items():
        current = merged.get(key)
        if isinstance(current, Mapping) and isinstance(value, Mapping):
            merged[key] = _merge_mapping(current, value)
        else:
            merged[key] = deepcopy(value)
    return merged


def compose_layout_definitions(
    layers: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Merge base-to-derived mappings; nested maps merge and other values replace.

    The final layer owns identity metadata. Lists are replaced atomically, which
    keeps ordered fields such as ``section_order`` predictable.
    """
    if not layers:
        raise LayoutCompositionError("At least one layout layer is required")

    merged: dict[str, object] = {}
    for index, layer in enumerate(layers):
        if not isinstance(layer, Mapping):
            raise LayoutCompositionError(f"Layout layer {index + 1} must be a mapping")
        if any(not isinstance(key, str) for key in layer):
            raise LayoutCompositionError(f"Layout layer {index + 1} keys must be strings")
        merged = _merge_mapping(merged, layer)

    active = layers[-1]
    merged.pop("extends", None)
    for key, default in (("id", "unknown"), ("name", ""), ("version", "1.0.0")):
        merged[key] = deepcopy(active.get(key, default))
    return merged


def _layout_file(path: Path, project_root: Path) -> Path:
    candidate = path if path.is_absolute() else project_root / path
    if candidate.is_dir() or not candidate.suffix:
        candidate = candidate / "layout.yaml"
    resolved = candidate.resolve()
    try:
        resolved.relative_to(project_root)
    except ValueError as exc:
        raise LayoutCompositionError(
            f"Layout reference resolves outside project_root: {resolved}"
        ) from exc
    return resolved


def load_composed_layout(layout_path: Path, project_root: Path) -> dict[str, object]:
    """Load an optional ``extends`` chain and return its deterministic composition.

    References are relative to the declaring layout file. Directory references
    resolve to ``layout.yaml``. Every resolved file must remain under project_root.
    """
    root = project_root.resolve()
    initial = _layout_file(layout_path, root)

    def load_layer(path: Path, active_stack: tuple[Path, ...]) -> dict[str, object]:
        resolved = _layout_file(path, root)
        if resolved in active_stack:
            chain = (*active_stack, resolved)
            rendered = " -> ".join(str(item) for item in chain)
            raise LayoutCompositionError(f"Layout composition cycle detected: {rendered}")
        if not resolved.is_file():
            raise LayoutCompositionError(f"Layout asset not found: {resolved}")

        try:
            raw = yaml.safe_load(resolved.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise LayoutCompositionError(f"Failed to parse layout asset: {exc}") from exc
        except OSError as exc:
            raise LayoutCompositionError(f"Failed to read layout asset {resolved}: {exc}") from exc
        if not isinstance(raw, Mapping):
            raise LayoutCompositionError("Layout asset must be a YAML mapping.")

        references = raw.get("extends", [])
        if isinstance(references, str):
            references = [references]
        elif not isinstance(references, list):
            raise LayoutCompositionError(
                "extends must be a relative path string or an ordered list of path strings"
            )

        parents: list[dict[str, object]] = []
        seen: set[Path] = set()
        for reference in references:
            if not isinstance(reference, str) or not reference or reference != reference.strip():
                raise LayoutCompositionError(
                    "extends entries must be non-empty path strings without surrounding whitespace"
                )
            reference_path = Path(reference)
            if reference_path.is_absolute():
                raise LayoutCompositionError("extends paths must be relative to the declaring layout")
            parent_path = _layout_file(resolved.parent / reference_path, root)
            if parent_path in seen:
                raise LayoutCompositionError(f"Duplicate layout reference in extends: {reference}")
            seen.add(parent_path)
            parents.append(load_layer(parent_path, (*active_stack, resolved)))

        own_layer = dict(raw)
        own_layer.pop("extends", None)
        return compose_layout_definitions((*parents, own_layer))

    return load_layer(initial, ())
