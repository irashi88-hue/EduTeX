from pathlib import Path


RENDERER = Path(__file__).parents[1] / "src" / "edutex" / "build" / "html_renderer.py"


def _source() -> str:
    return RENDERER.read_text(encoding="utf-8")


def test_true_false_focus_does_not_depend_on_has_selector():
    source = _source()
    assert ".true-false-option:has(input:focus-visible)" not in source
    assert ".true-false-option:focus-within {{" in source


def test_true_false_focus_contract_keeps_keyboard_focus_indicator():
    source = _source()
    assert ":focus-visible {{ outline: 3px solid var(--rule-color);" in source
    assert ".true-false-option:focus-within {{" in source
    assert "outline: 3px solid var(--exercise-color);" in source
    assert "outline-offset: 2px;" in source


def test_true_false_radio_markup_remains_label_associated():
    source = _source()
    assert 'label class="true-false-option"' in source
    assert 'input type="radio" class="true-false-choice"' in source
    assert 'for="{html.escape(true_id)}"' in source
    assert 'for="{html.escape(false_id)}"' in source


def test_renderer_source_compiles():
    compile(_source(), str(RENDERER), "exec")