import re
import pytest

from pathlib import Path

from edutex.activator.activator import Activator
from edutex.build.html_renderer import HtmlRenderer
from edutex.configuration.loader import load_config
from edutex.core.cli import _register_project_assets
from edutex.extension.service import ExtensionService
from edutex.knowledge.service import KnowledgeService
from edutex.layout.service import LayoutService
from edutex.resolver.resolver import Resolver
from edutex.theme.service import ThemeService

PROJECT = Path(__file__).resolve().parents[2]


def render_in_memory() -> str:
    config = load_config(PROJECT / "edutex.config.yaml")
    registry = _register_project_assets(config, PROJECT)
    state = Activator().activate(Resolver(registry).resolve())

    knowledge = KnowledgeService()
    knowledge.process(state, PROJECT)
    theme = ThemeService()
    theme.process(state, knowledge, PROJECT)
    layout = LayoutService()
    layout.process(state, theme, PROJECT)
    extensions = ExtensionService()
    extensions.process(state, layout, PROJECT)

    assert config.extensions.enabled == []
    assert not extensions.loaded_extensions
    assert len(extensions.document.appendix_nodes) == 3
    return HtmlRenderer().render(extensions.document, knowledge.meta, theme.theme_model)


def test_generation_contract() -> None:
    source = render_in_memory()

    for forbidden in (
        "Reading tip",
        "Notice how the verb",
        "Subject",
        "Meaning",
        "Solution:",
        "I am",
        "you are",
        "he/she",
        "they/you",
        "to be",
        "Word",
        "Translation",
    ):
        assert forbidden not in source

    assert source.count('class="solution-inline"') == 3
    assert source.count('class="solution-inline"><a ') == 3

    for expected in (
        "Soluzioni",
        "Soluzione",
        "Hallo",
        "Guten Morgen",
        "buongiorno, al mattino",
    ):
        assert expected in source


def test_choice_exercise_contract() -> None:
    source = render_in_memory()

    assert source.count("data-choice-exercise") == 2
    assert 'data-answer="[&quot;Guten Morgen&quot;]"' in source
    assert 'data-answer="[&quot;Hallo&quot;,&quot;Tschüss&quot;]"' in source
    assert 'value="Guten Morgen"' in source
    assert 'type="radio"' in source
    assert 'type="checkbox"' in source
    assert 'class="choice-result" role="status" aria-live="polite"' in source
    assert 'function sameValues' in source
    assert "choice_correct" not in source

def _exercise_contract_renderer() -> HtmlRenderer:
    renderer = HtmlRenderer()
    renderer._labels = {
        "short_answer": "Risposta breve",
        "short_prompt": "Risposta",
        "short_placeholder": "Scrivi la tua risposta",
        "short_instruction": "Scrivi la risposta nel campo qui sotto, poi seleziona Verifica risposta.",
        "check_short": "Verifica risposta",
        "reset_short": "Azzera risposta",
        "special_chars": "Caratteri speciali",
        "options": "Opzioni",
        "check_choice": "Verifica risposta",
        "reset_choice": "Azzera esercizio",
        "choice_result": "Risultato scelta",
    }
    return renderer


def test_short_answer_has_default_guidance_and_optional_response_hint() -> None:
    renderer = _exercise_contract_renderer()
    source = renderer._render_short_answer(
        "type: short_answer\n"
        "prompt: Completa le due forme.\n"
        "response_hint: Scrivi solo le due parole, in ordine, separate da uno spazio.\n"
        "answer: heißt heiße",
        "short-answer-contract",
    )

    assert "class=\"short-answer-instruction\"" in source
    assert "poi seleziona Verifica risposta" in source
    assert "class=\"short-answer-format-hint\"" in source
    assert "Scrivi solo le due parole" in source
    assert 'data-character="ä"' in source
    assert 'data-character="ß"' in source


def test_choice_requires_answer_metadata_and_matching_option() -> None:
    renderer = _exercise_contract_renderer()
    missing_answer = (
        "type: choice\nquestion: Scegli la forma corretta.\n"
        "options:\n- heißen\n- heiße\n- heißt"
    )
    with pytest.raises(ValueError, match="missing required answer metadata"):
        renderer._render_choice_exercise(missing_answer, "choice-missing-answer")

    unmatched_answer = missing_answer + "\nanswer: geheißen"
    with pytest.raises(ValueError, match="do not match any configured option"):
        renderer._render_choice_exercise(unmatched_answer, "choice-unmatched-answer")


def test_translation_exercise_contract() -> None:
    source = render_in_memory()

    for expected in (
        "\u00dcbersetze den Satz",
        "Mi chiamo Luca.",
        "Ich hei\u00dfe Luca.",
        "Ich heisse Luca.",
    ):
        assert expected in source

    assert 'class="translation"' in source
    assert 'class="translation-answer"' in source
    assert 'data-answers="Ich hei\u00dfe Luca.|Ich heisse Luca."' in source
    assert 'class="translation-check"' in source
    assert 'class="translation-reset"' in source
    assert 'role="status" aria-live="polite"' in source

def test_translation_authoring_aliases_and_solution_fallback() -> None:
    renderer = HtmlRenderer()
    renderer._labels = {
        "translation": "Traduzione",
        "translation_prompt": "Testo da tradurre",
        "write_translation": "Scrivi la traduzione",
        "translation_check": "Verifica traduzione",
        "translation_reset": "Azzera traduzione",
    }

    alias_source = renderer._render_translation_exercise(
        "\n".join(
            (
                "type: translation",
                "prompt: Mi chiamo Luca.",
                "expected: Ich hei\u00dfe Luca. | Ich heisse Luca.",
            )
        ),
        "exercise-alias",
    )

    assert "Mi chiamo Luca." in alias_source
    assert (
        'data-answers="Ich hei\u00dfe Luca.|Ich heisse Luca."'
        in alias_source
    )

    fallback_source = renderer._render_translation_exercise(
        "\n".join(
            (
                "type: translation",
                "source: Mi chiamo Luca.",
            )
        ),
        "exercise-fallback",
        "Ich hei\u00dfe Luca.\nSeconda riga ignorata.",
    )

    assert "Mi chiamo Luca." in fallback_source
    assert 'data-answers="Ich hei\u00dfe Luca."' in fallback_source

def test_translation_accessibility_contract() -> None:
    source = render_in_memory()

    translation_start = source.index('<div class="translation"')
    translation_source = source[translation_start:]

    label_match = re.search(
        r'<label class="translation-label" for="([^"]+)">',
        translation_source,
    )
    textarea_match = re.search(
        r'<textarea class="translation-answer" id="([^"]+)" '
        r'name="([^"]+)"',
        translation_source,
    )

    assert label_match is not None
    assert textarea_match is not None

    label_target = label_match.group(1)
    textarea_id = textarea_match.group(1)
    textarea_name = textarea_match.group(2)

    assert label_target == textarea_id
    assert textarea_id == textarea_name

    for expected in (
        'aria-label="Scrivi la traduzione"',
        '<button type="button" class="translation-check">',
        '<button type="button" class="translation-reset">',
        'role="status" aria-live="polite"',
    ):
        assert expected in translation_source

def test_release_smoke_preserves_current_interactive_fixture() -> None:
    source = render_in_memory()

    for expected in (
        "<!doctype html>",
        '<meta charset="utf-8">',
        '<meta name="generator" content="EduTeX">',
        'data-choice-exercise',
        'class="short-answer"',
        'class="translation"',
        'class="translation-answer"',
        'class="translation-check"',
        'class="translation-reset"',
        'role="status" aria-live="polite"',
        'class="solutions"',
        'class="solution-inline"',
    ):
        assert expected in source

    assert source.count('class="solution-inline"') == 3
    assert source.count('data-choice-exercise') == 2
    assert source.count('class="translation"') == 1

    assert '<script src=' not in source
    assert '<link rel="stylesheet" href=' not in source
    assert "http://" not in source
    assert "https://" not in source
