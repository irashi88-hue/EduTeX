from pathlib import Path


RENDERER = Path(__file__).parents[1] / "src" / "edutex" / "build" / "html_renderer.py"


def _css_template() -> str:
    source = RENDERER.read_text(encoding="utf-8")
    start = source.index("  <style>")
    end = source.index("  </style>", start)
    return source[start:end]


def test_renderer_declares_light_and_dark_color_schemes():
    css = _css_template()
    assert "color-scheme: light;" in css
    assert "@media (prefers-color-scheme: dark)" in css
    assert "color-scheme: dark;" in css


def test_renderer_uses_semantic_surface_and_control_tokens():
    css = _css_template()
    for token in (
        "--canvas-bg",
        "--surface",
        "--surface-subtle",
        "--control-bg",
        "--input-bg",
        "--code-bg",
        "--on-accent",
        "--success-bg",
        "--danger-bg",
        "--warning-bg",
    ):
        assert token in css
    # The renderer stores doubled braces because the CSS lives in a Python f-string.
    normalized = css.replace("{{", "{").replace("}}", "}")
    assert "background: var(--canvas-bg);" in normalized
    assert "background: var(--surface);" in normalized
    assert "background: var(--input-bg);" in normalized
    assert "background: var(--code-bg);" in normalized


def test_dark_palette_covers_document_and_exercise_states():
    css = _css_template()
    dark_start = css.index("@media (prefers-color-scheme: dark)")
    dark_css = css[dark_start:]
    for value in (
        "--page-bg: #0f172a",
        "--canvas-bg: #020617",
        "--surface: #111827",
        "--ink: #e5e7eb",
        "--control-bg: #0f172a",
        "--success-bg: #052e16",
        "--danger-bg: #450a0a",
        "--warning-bg: #422006",
        "--exercise-bg: #1e1b4b",
        "--solution-bg: #052e16",
    ):
        assert value in dark_css


def test_renderer_source_compiles():
    compile(RENDERER.read_text(encoding="utf-8"), str(RENDERER), "exec")