from pathlib import Path


RENDERER = Path(__file__).parents[1] / "src" / "edutex" / "build" / "html_renderer.py"


def _css() -> str:
    source = RENDERER.read_text(encoding="utf-8")
    start = source.index("  <style>")
    end = source.index("  </style>", start)
    return source[start:end]


def test_mobile_exercise_layout_stacks_wide_rows():
    css = _css()
    assert "@media (max-width: 640px)" in css
    assert ".matching-row {{" in css
    assert "grid-template-columns: 1fr;" in css
    assert ".true-false-row {{" in css


def test_mobile_exercise_controls_use_full_width_without_side_offsets():
    css = _css()
    assert ".true-false-controls {{" in css
    assert "width: 100%;" in css
    assert ".matching-check," in css
    assert ".true-false-reset {{" in css
    assert "margin-left: 0;" in css
    assert "width: 100%;" in css


def test_small_mobile_nodes_reduce_horizontal_padding():
    css = _css()
    assert "@media (max-width: 520px)" in css
    assert ".node {{ padding: .9rem .85rem; }}" in css


def test_renderer_source_compiles():
    compile(RENDERER.read_text(encoding="utf-8"), str(RENDERER), "exec")