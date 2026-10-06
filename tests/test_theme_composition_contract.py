from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from edutex.theme.composition import ThemeCompositionError, load_composed_theme
from edutex.theme.service import ThemeService


def write_theme(root: Path, theme_id: str, source: str) -> Path:
    folder = root / theme_id
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "theme.yaml"
    path.write_text(dedent(source).strip() + "\n", encoding="utf-8")
    return path


def test_ordered_layers_deep_merge_styles_palette_and_tokens(tmp_path: Path) -> None:
    root = tmp_path / "themes"
    write_theme(root, "base", """
        id: base
        name: Base
        version: "1.0.0"
        styles:
          exercise:
            border_color: "#111111"
            background_color: "#ffffff"
            display: block
        palette:
          canvas: "#eeeeee"
          link: "#000000"
        tokens:
          typography:
            family: ["Base Sans", "Fallback"]
            size_pt: 11
          spacing:
            unit_mm: 4
    """)
    write_theme(root, "brand", """
        id: brand
        styles:
          exercise:
            label: Branded
            border_color: "#222222"
        palette:
          link: "#123456"
        tokens:
          typography:
            family: ["Brand Sans"]
          color:
            accent: "#123456"
    """)
    selected = write_theme(root, "school", """
        id: school
        name: School theme
        version: "2.0.0"
        extends: [base, brand]
        styles:
          exercise:
            background_color: "#eaf2ff"
        palette:
          canvas: "#f8fbff"
        tokens:
          spacing:
            unit_mm: 6
    """)

    result = load_composed_theme(selected, root)
    exercise = result["styles"]["exercise"]
    assert result["id"] == "school"
    assert result["name"] == "School theme"
    assert exercise == {
        "border_color": "#222222",
        "background_color": "#eaf2ff",
        "display": "block",
        "label": "Branded",
    }
    assert result["palette"] == {"canvas": "#f8fbff", "link": "#123456"}
    assert result["tokens"]["typography"] == {"family": ["Brand Sans"], "size_pt": 11}
    assert result["tokens"]["spacing"]["unit_mm"] == 6
    assert result["tokens"]["color"]["accent"] == "#123456"


def test_legacy_theme_without_extends_keeps_its_values(tmp_path: Path) -> None:
    root = tmp_path / "themes"
    selected = write_theme(root, "legacy", """
        id: legacy
        name: Legacy
        version: "1.0.0"
        styles:
          _default:
            display: block
        palette:
          ink: "#172033"
    """)
    result = load_composed_theme(selected, root)
    assert result["id"] == "legacy"
    assert result["styles"] == {"_default": {"display": "block"}}
    assert result["palette"] == {"ink": "#172033"}
    assert result["tokens"] == {}


def test_theme_service_builds_model_from_composed_layers(tmp_path: Path) -> None:
    root = tmp_path / "themes"
    write_theme(root, "default", """
        id: default
        styles:
          exercise:
            border_color: "#111111"
            background_color: "#ffffff"
            font_weight: normal
            display: block
        tokens:
          spacing:
            unit_mm: 4
    """)
    selected = write_theme(root, "dark", """
        id: dark
        name: Dark
        extends: [default]
        styles:
          exercise:
            background_color: "#111827"
        tokens:
          spacing:
            unit_mm: 5
    """)
    model = ThemeService()._load_theme(selected, root)
    assert model.theme_id == "dark"
    assert model.styles["exercise"].border_color == "#111111"
    assert model.styles["exercise"].background_color == "#111827"
    assert model.tokens["spacing"]["unit_mm"] == 5


def test_missing_parent_and_invalid_parent_ids_are_rejected(tmp_path: Path) -> None:
    root = tmp_path / "themes"
    missing = write_theme(root, "missing-child", """
        id: missing-child
        extends: [not-installed]
    """)
    with pytest.raises(ThemeCompositionError, match="not-installed"):
        load_composed_theme(missing, root)

    unsafe = write_theme(root, "unsafe", """
        id: unsafe
        extends: [../outside]
    """)
    with pytest.raises(ThemeCompositionError, match="simple theme IDs"):
        load_composed_theme(unsafe, root)


def test_duplicate_parent_and_inheritance_cycle_are_rejected(tmp_path: Path) -> None:
    root = tmp_path / "themes"
    duplicate = write_theme(root, "duplicate", """
        id: duplicate
        extends: [base, base]
    """)
    write_theme(root, "base", "id: base")
    with pytest.raises(ThemeCompositionError, match="duplicate theme parent"):
        load_composed_theme(duplicate, root)

    alpha = write_theme(root, "alpha", """
        id: alpha
        extends: [beta]
    """)
    write_theme(root, "beta", """
        id: beta
        extends: [alpha]
    """)
    with pytest.raises(ThemeCompositionError, match="cycle"):
        load_composed_theme(alpha, root)


def test_selected_theme_must_remain_inside_theme_root(tmp_path: Path) -> None:
    root = tmp_path / "themes"
    root.mkdir()
    outside = write_theme(tmp_path / "outside", "theme", "id: outside")
    with pytest.raises(ThemeCompositionError, match="outside theme root"):
        load_composed_theme(outside, root)
