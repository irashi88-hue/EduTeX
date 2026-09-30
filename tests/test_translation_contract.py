from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "src" / "edutex" / "build" / "html_renderer.py"


def _renderer_source() -> str:
    return RENDERER.read_text(encoding="utf-8")


def test_translation_dispatch_and_authoring_contract() -> None:
    source = _renderer_source()

    assert "def _is_translation_exercise" in source
    assert "def _render_translation_exercise" in source
    assert 'line.strip().lower() == "type: translation"' in source

    assert 'lower.startswith("source:") or lower.startswith("prompt:")' in source
    assert "source_lines" in source
    assert "prompt_lines" in source
    assert "in_source = True" in source

    matching_dispatch = source.index("elif self._is_matching_exercise")
    translation_dispatch = source.index("elif self._is_translation_exercise")
    choice_dispatch = source.index("elif self._is_choice_exercise")

    assert matching_dispatch < translation_dispatch < choice_dispatch


def test_translation_renders_source_and_prompt_content() -> None:
    source = _renderer_source()

    assert 'source_lines.append(line.split(":", 1)[1].strip())' in source
    assert "if in_source and line:" in source
    assert "source_lines.append(raw_line)" in source
    assert "source = chr(10).join(source_lines).strip()" in source

    assert "for line in prompt_lines:" in source
    assert 'f\'<div class="body-line">{self._inline(line)}</div>\'' in source

    assert 'class="translation-source"' in source
    assert 'class="translation-label"' in source
    assert 'self._labels["translation_prompt"]' in source
    assert "self._inline(source)" in source


def test_translation_uses_an_accessible_multiline_answer_control() -> None:
    source = _renderer_source()

    assert 'answer_id = f"{exercise_id}-translation"' in source
    assert 'f\'<label class="translation-label" for="{html.escape(answer_id)}">\'' in source
    assert 'self._labels["write_translation"]' in source

    assert 'f\'<textarea class="translation-answer" \'' in source
    assert 'f\'id="{html.escape(answer_id)}" \'' in source
    assert 'f\'name="{html.escape(answer_id)}" \'' in source
    assert 'aria-label="{html.escape(self._labels["write_translation"])}"' in source
    assert "</textarea>" in source


def test_translation_supports_source_and_prompt_aliases() -> None:
    source = _renderer_source()

    source_alias = 'lower.startswith("source:") or lower.startswith("prompt:")'
    assert source_alias in source

    alias_start = source.index(source_alias)
    answer_start = source.index('answer_id = f"{exercise_id}-translation"')

    alias_block = source[alias_start:answer_start]
    assert '"source:"' in alias_block
    assert '"prompt:"' in alias_block
    assert "source_lines.append" in alias_block


def test_translation_preserves_inline_markup_and_escapes_identifiers() -> None:
    source = _renderer_source()

    assert "self._inline(line)" in source
    assert "self._inline(source)" in source
    assert 'html.escape(answer_id)' in source


def test_translation_is_rendered_without_interactive_javascript_dependency() -> None:
    source = _renderer_source()

    translation_method_start = source.index("def _render_translation_exercise")
    choice_method_start = source.index("def _is_choice_exercise")

    translation_method = source[translation_method_start:choice_method_start]

    assert "textarea" in translation_method
    assert "addEventListener" not in translation_method
    assert "check_translation" not in translation_method
    assert "reset_translation" not in translation_method

def test_shared_alternative_answer_parser_is_preserved() -> None:
    source = _renderer_source()

    assert 'const parseAcceptedAnswers = (value) => String(value || "")' in source
    assert 'const answers = parseAcceptedAnswers(input.dataset.answer);' in source
    assert 'const answers = parseAcceptedAnswers(input.dataset.answers);' in source
    assert '.split("|")' in source
    assert '.map(normalizeShortAnswer)' in source
    assert '.filter(Boolean)' in source


def test_translation_feedback_uses_theme_semantic_tokens() -> None:
    source = _renderer_source()

    for marker in (
        'color: var(--on-accent);',
        'background: var(--control-bg);',
        'border-color: var(--success-border);',
        'background: var(--success-bg);',
        'border-color: var(--danger-border);',
        'background: var(--danger-bg);',
        '.translation-check:hover, .translation-reset:hover',
    ):
        assert marker in source

def test_translation_fixture_is_authorable_and_utf8() -> None:
    fixture = (
        ROOT / "assets" / "knowledge_models" / "choice-verifica.md"
    ).read_text(encoding="utf-8")

    assert "title: Übersetze den Satz" in fixture
    assert "type: translation" in fixture
    assert "source: Mi chiamo Luca." in fixture
    assert "answer: Ich heiße Luca. | Ich heisse Luca." in fixture
    assert "::: solution" in fixture
    assert "Ich heiße Luca." in fixture

def test_translation_labels_cover_italian_and_english() -> None:
    source = _renderer_source()

    for marker in (
        '"translation_prompt": "Text to translate"',
        '"write_translation": "Write your translation"',
        '"translation_check": "Check translation"',
        '"translation_reset": "Reset translation"',
        '"translation_correct": "Correct"',
        '"translation_wrong": "Not correct"',
        '"translation_empty": "Write a translation first"',
        '"translation_prompt": "Testo da tradurre"',
        '"write_translation": "Scrivi la traduzione"',
        '"translation_check": "Verifica traduzione"',
        '"translation_reset": "Azzera traduzione"',
        '"translation_correct": "Corretta"',
        '"translation_wrong": "Non corretta"',
        '"translation_empty": "Scrivi prima una traduzione"',
    ):
        assert marker in source
