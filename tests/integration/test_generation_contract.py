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
