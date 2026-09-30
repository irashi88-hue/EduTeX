from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "src" / "edutex" / "build" / "html_renderer.py"


def _renderer_source() -> str:
    return RENDERER.read_text(encoding="utf-8")


def test_matching_dispatch_and_authoring_contract() -> None:
    source = _renderer_source()

    assert "def _is_matching_exercise" in source
    assert "def _render_matching_exercise" in source
    assert 'line.strip().lower() == "type: matching"' in source

    assert 'lower == "words:" or lower.startswith("words:")' in source
    assert 'lower == "meanings:" or lower.startswith("meanings:")' in source
    assert 'pair_count = min(len(words), len(meanings))' in source

    matching_dispatch = source.index("elif self._is_matching_exercise")
    translation_dispatch = source.index("elif self._is_translation_exercise")
    assert matching_dispatch < translation_dispatch


def test_matching_markup_contains_accessible_selectors() -> None:
    source = _renderer_source()

    assert 'class="matching-list"' in source
    assert 'role="list"' in source
    assert 'data-matching-group=' in source

    assert 'class="matching-row"' in source
    assert 'class="matching-word"' in source
    assert 'class="matching-select"' in source
    assert 'class="matching-feedback"' in source

    assert 'id="{html.escape(select_id)}"' in source
    assert 'name="{html.escape(select_id)}"' in source
    assert 'data-answer="{html.escape(meanings[index - 1], quote=True)}"' in source
    assert 'aria-label="{html.escape(self._labels["matching_word"])}' in source

    assert 'class="matching-check"' in source
    assert 'class="matching-reset"' in source
    assert 'class="matching-result"' in source


def test_matching_markup_contains_placeholder_and_feedback_regions() -> None:
    source = _renderer_source()

    assert 'value="" selected' in source
    assert 'self._labels["choose_meaning"]' in source
    assert 'aria-live="polite"' in source
    assert 'self._labels["matching_result"]' in source
    assert 'self._labels["no_matching_data"]' in source


def test_matching_randomizes_options_and_prevents_duplicates() -> None:
    source = _renderer_source()

    assert "const randomizeMatchingGroup" in source
    assert "const updateMatchingGroup" in source
    assert "const handleMatchingChange" in source

    assert 'querySelectorAll("select.matching-select")' in source
    assert "const sourceOptions = Array.from(selects[0].options)" in source
    assert "const shuffledOptions = shuffle(sourceOptions)" in source
    assert "select.replaceChildren()" in source
    assert "option.cloneNode(true)" in source

    assert "const selectedValues = new Set" in source
    assert "option.disabled = selectedValues.has(option.value)" in source
    assert "const duplicate = changedSelect.value && Array.from(" in source
    assert 'changedSelect.value = ""' in source
    assert 'self._labels["matching_duplicate"]' in source


def test_matching_check_reports_missing_duplicate_correct_and_wrong() -> None:
    source = _renderer_source()

    assert "const checkMatchingGroup" in source
    assert "let correct = 0" in source
    assert "const selectedValues = new Set()" in source

    assert 'row.classList.add("is-missing")' in source
    assert 'row.classList.add("is-wrong")' in source
    assert 'row.classList.add("is-correct")' in source

    assert 'self._labels["matching_missing"]' in source
    assert 'self._labels["matching_duplicate"]' in source
    assert 'self._labels["matching_correct"]' in source
    assert 'self._labels["matching_wrong"]' in source

    assert 'select.value === select.dataset.answer' in source
    assert 'result.textContent = `${{correct}} / ${{rows.length}}`' in source


def test_matching_reset_clears_state_and_recomputes_options() -> None:
    source = _renderer_source()

    assert "const resetMatchingGroup" in source
    assert 'select.value = ""' in source
    assert 'row.classList.remove("is-correct", "is-wrong", "is-missing")' in source
    assert 'feedback.textContent = ""' in source
    assert 'result.textContent = ""' in source
    assert "updateMatchingGroup(group)" in source


def test_matching_escapes_authored_values_and_preserves_inline_markup() -> None:
    source = _renderer_source()

    assert 'html.escape(meaning)' in source
    assert 'html.escape(meanings[index - 1], quote=True)' in source
    assert "self._inline(meaning)" in source
    assert "self._inline(word)" in source


def test_matching_groups_are_initialized_on_page_load() -> None:
    source = _renderer_source()

    assert 'document.querySelectorAll(".matching-list").forEach((group) =>' in source
    assert 'randomizeMatchingGroup(group)' in source
    assert 'updateMatchingGroup(group)' in source