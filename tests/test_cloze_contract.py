from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "src" / "edutex" / "build" / "html_renderer.py"


def _renderer_source() -> str:
    return RENDERER.read_text(encoding="utf-8")


def test_cloze_dispatch_and_authoring_aliases() -> None:
    source = _renderer_source()

    assert "def _is_cloze_exercise" in source
    assert "def _render_cloze_exercise" in source

    assert '"type: cloze"' in source
    assert '"type: fill"' in source
    assert '"type: fill-in"' in source

    assert 'lower.startswith("sentence:")' in source
    assert 'lower == "answers:" or lower.startswith("answers:")' in source
    assert 're.split(r"_{2,}", sentence)' in source

    cloze_dispatch = source.index("elif self._is_cloze_exercise")
    true_false_dispatch = source.index("elif self._is_true_false_exercise")
    assert cloze_dispatch < true_false_dispatch


def test_cloze_markup_contains_accessible_interactive_controls() -> None:
    source = _renderer_source()

    assert 'class="cloze-exercise"' in source
    assert 'class="cloze-sentence"' in source
    assert 'class="cloze-blank"' in source
    assert 'class="cloze-token"' in source

    assert 'type="button"' in source
    assert 'data-answer=' in source
    assert 'data-placeholder=' in source
    assert 'data-token-index=' in source
    assert 'data-token=' in source

    assert 'role="group"' in source
    assert 'class="cloze-result" role="status" aria-live="polite"' in source


def test_cloze_markup_contains_check_and_reset_actions() -> None:
    source = _renderer_source()

    assert 'class="cloze-check"' in source
    assert 'class="cloze-reset"' in source
    assert 'self._labels["check_cloze"]' in source
    assert 'self._labels["reset_cloze"]' in source


def test_cloze_interaction_supports_selection_removal_check_and_reset() -> None:
    source = _renderer_source()

    assert "const normalizeClozeText" in source
    assert "const initializeCloze" in source

    assert "blank.dataset.tokenIndex = token.dataset.tokenIndex" in source
    assert "blank.dataset.selected = token.dataset.token" in source
    assert "token.disabled = true" in source

    assert "delete blank.dataset.tokenIndex" in source
    assert "delete blank.dataset.selected" in source
    assert "token.disabled = false" in source

    assert 'blank.classList.add("is-correct")' in source
    assert 'blank.classList.add("is-wrong")' in source
    assert 'blank.classList.add("is-missing")' in source
    assert 'result.textContent = `${{correct}} / ${{blanks.length}}`' in source

    assert 'blank.classList.remove("is-filled", "is-correct", "is-wrong", "is-missing")' in source
    assert 'tokens.forEach((token) => {{ token.disabled = false; }});' in source


def test_cloze_escapes_authored_values_and_preserves_inline_markup() -> None:
    source = _renderer_source()

    assert 'html.escape(answers[index], quote=True)' in source
    assert 'html.escape(answer, quote=True)' in source
    assert 'sentence_markup.append(self._inline(part))' in source
    assert "f'{self._inline(answer)}</button>'" in source


def test_cloze_is_initialized_for_each_rendered_exercise() -> None:
    source = _renderer_source()

    assert 'document.querySelectorAll(".cloze-exercise").forEach(initializeCloze);' in source