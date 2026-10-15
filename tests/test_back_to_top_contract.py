"""Contract tests for the accessible lesson back-to-top control."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "src" / "edutex" / "build" / "html_renderer.py"


def test_back_to_top_arrow_is_centered_large_and_accessible() -> None:
    source = RENDERER.read_text(encoding="utf-8")
    for marker in (
        'class="back-to-top" href="#"',
        'aria-label="{back_to_top_label}"',
        'class="back-to-top-icon" aria-hidden="true" viewBox="0 0 24 24" focusable="false"',
        '<path d="M12 19V5M6 11l6-6 6 6"/>',
        '.back-to-top {{',
        'width: 3.5rem;',
        'height: 3.5rem;',
        'place-items: center;',
        '.back-to-top-icon {{',
        'width: 2rem;',
        'height: 2rem;',
        'stroke: currentColor;',
        'stroke-linecap: round;',
        '@media (prefers-reduced-motion: reduce) {{',
        '<html lang="{language}">',
        '<body>\n  <a class="back-to-top" href="#"',
    ):
        assert marker in source, f"Missing back-to-top visual contract marker: {marker}"
    assert '<span aria-hidden="true">↑</span>' not in source
    assert '<html lang="{language}" id="page-top">' not in source
    assert '<body id="page-top">' not in source
