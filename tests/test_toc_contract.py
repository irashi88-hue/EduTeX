from pathlib import Path


RENDERER = Path(__file__).parents[1] / "src" / "edutex" / "build" / "html_renderer.py"


def _source() -> str:
    return RENDERER.read_text(encoding="utf-8")


def test_toc_renders_nested_ordered_lists():
    source = _source()
    start = source.index("    def _render_toc(self) -> str:")
    end = source.index("    def _kv_table(", start)
    method = source[start:end]
    assert "def render_nodes(nodes: list[dict[str, object]]) -> str:" in method
    assert "parts = [\"<ol>\"]" in method
    assert "if children:" in method
    assert "parts.append(render_nodes(children))" in method


def test_toc_suppresses_only_consecutive_duplicate_titles():
    source = _source()
    start = source.index("    def _render_toc(self) -> str:")
    end = source.index("    def _kv_table(", start)
    method = source[start:end]
    assert "previous_key" in method
    assert "normalized_label = \" \".join(label.split()).casefold()" in method
    assert "if key == previous_key:" in method
    assert "entries.append((level, heading_id, label))" in method


def test_toc_css_supports_nested_lists():
    source = _source()
    assert ".toc ol ol {{ margin-top: .15rem; }}" in source


def test_renderer_source_compiles():
    compile(_source(), str(RENDERER), "exec")