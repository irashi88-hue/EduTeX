from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "src" / "edutex" / "build" / "html_renderer.py"


def _renderer_source() -> str:
    return RENDERER.read_text(encoding="utf-8")


def test_sentence_builder_dispatch_and_authoring_aliases() -> None:
    source = _renderer_source()

    assert "def _is_sentence_builder_exercise" in source
    assert "def _render_sentence_builder" in source

    assert '"type: builder"' in source
    assert '"type: sentence-builder"' in source

    assert 'lower == "tokens:" or lower.startswith("tokens:")' in source
    assert 'lower.startswith("answer:")' in source
    assert 'expected = " ".join(answer_lines).strip()' in source
    assert 'if not expected and solution_body:' in source

    builder_dispatch = source.index("elif self._is_sentence_builder_exercise")
    matching_dispatch = source.index("elif self._is_matching_exercise")
    assert builder_dispatch < matching_dispatch


def test_sentence_builder_markup_contains_accessible_controls() -> None:
    source = _renderer_source()

    assert 'class="sentence-builder"' in source
    assert 'data-answer=' in source
    assert 'data-placeholder=' in source
    assert 'aria-label=' in source

    assert 'class="builder-answer"' in source
    assert 'class="builder-tokens"' in source
    assert 'class="builder-token"' in source
    assert 'item.className = "builder-answer-token"' in source

    assert 'role="status" aria-live="polite"' in source
    assert 'role="group"' in source
    assert 'type="button"' in source
    assert 'data-token-index=' in source
    assert 'data-token=' in source

    assert 'class="builder-check"' in source
    assert 'class="builder-reset"' in source
    assert 'class="builder-result"' in source


def test_sentence_builder_selection_and_removal_are_supported() -> None:
    source = _renderer_source()

    assert "const initializeBuilder" in source
    assert "const values = []" in source
    assert "const selectedTokens = []" in source

    assert "values.push(token.dataset.token)" in source
    assert "selectedTokens.push(token)" in source
    assert "token.disabled = true" in source

    assert "const originalToken = selectedTokens[index]" in source
    assert "values.splice(index, 1)" in source
    assert "selectedTokens.splice(index, 1)" in source
    assert "originalToken.disabled = false" in source

    assert "answer.replaceChildren()" in source
    assert 'placeholder.className = "builder-placeholder"' in source
    assert 'item.className = "builder-answer-token"' in source
    assert "item.addEventListener" in source


def test_sentence_builder_check_normalizes_and_reports_result() -> None:
    source = _renderer_source()

    assert "const normalizeBuilderText" in source
    assert '.replace(/\\\\s+/g, " ")' in source
    assert ".toLocaleLowerCase()" in source

    assert 'classList.remove("is-correct", "is-wrong")' in source
    assert 'classList.add("is-correct")' in source
    assert 'classList.add("is-wrong")' in source

    assert 'self._labels["builder_empty"]' in source
    assert 'self._labels["builder_correct"]' in source
    assert 'self._labels["builder_wrong"]' in source
    assert 'result.textContent = ""' in source


def test_sentence_builder_reset_restores_initial_state() -> None:
    source = _renderer_source()

    assert "values.length = 0" in source
    assert "selectedTokens.length = 0" in source
    assert "tokens.forEach((token) => {{ token.disabled = false; }});" in source
    assert 'renderAnswer();' in source


def test_sentence_builder_escapes_values_and_preserves_inline_markup() -> None:
    source = _renderer_source()

    assert 'html.escape(token, quote=True)' in source
    assert 'html.escape(expected, quote=True)' in source
    assert "f'{self._inline(token)}</button>'" in source


def test_sentence_builder_is_initialized_for_each_rendered_exercise() -> None:
    source = _renderer_source()

    assert (
        'document.querySelectorAll(".sentence-builder").forEach(initializeBuilder);'
        in source
    )