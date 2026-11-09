"""Contract tests for the dialogue exercise HTML renderer."""

from __future__ import annotations

import json
import re
from types import SimpleNamespace

from edutex.build.dialogue import build_system_prompt, parse_dialogue_body
from edutex.build.dialogue_render import render_dialogue_exercise

VALID_BODY = """type: dialogue
level: A1
language: inglese
topic: al ristorante
role: cameriere
goal: ordinare un caffè
criteria:
- saluta
- chiede il conto
vocabulary:
- coffee
structures:
- I would like
"""

ENABLED = SimpleNamespace(enabled=True, endpoint="http://localhost:11434", model="llama3", timeout_seconds=60)
DISABLED = SimpleNamespace(enabled=False, endpoint="http://localhost:11434", model="", timeout_seconds=60)
CONFIG_PATTERN = r'<script type="application/json" data-dialogue-config>(.*?)</script>'


def test_disabled_renders_static_fallback_without_script() -> None:
    out = render_dialogue_exercise(VALID_BODY, "ex-1", ui_language="it", config=DISABLED)

    assert "<script" not in out
    assert "data-dialogue-fallback" in out
    assert "ordinare un caffè" in out
    assert "Dialogo guidato" in out


def test_missing_config_is_treated_as_disabled() -> None:
    out = render_dialogue_exercise(VALID_BODY, "ex-1", ui_language="en", config=None)

    assert "<script" not in out
    assert "Guided dialogue" in out


def test_enabled_embeds_prompt_and_only_the_configured_endpoint() -> None:
    out = render_dialogue_exercise(VALID_BODY, "ex-1", ui_language="it", config=ENABLED)

    assert "<script>" in out
    assert 'data-dialogue-config>' in out
    urls = set(re.findall(r"https?://[^\"'\s<]+", out))
    assert urls == {"http://localhost:11434"}


def test_embedded_system_prompt_matches_builder() -> None:
    out = render_dialogue_exercise(VALID_BODY, "ex-1", ui_language="it", config=ENABLED)

    match = re.search(CONFIG_PATTERN, out, re.S)
    assert match is not None
    data = json.loads(match.group(1))
    spec = parse_dialogue_body(VALID_BODY).spec
    assert spec is not None
    assert data["system"] == build_system_prompt(spec)
    assert data["maxTurns"] == spec.max_turns


def test_user_content_cannot_close_the_script_or_inject_markup() -> None:
    body = VALID_BODY.replace(
        "topic: al ristorante",
        "topic: </script><img src=x onerror=alert(1)>",
    )
    out = render_dialogue_exercise(body, "ex-1", ui_language="it", config=ENABLED)

    assert "</script><img" not in out
    assert "<img" not in out


def test_model_output_is_rendered_as_text_only() -> None:
    out = render_dialogue_exercise(VALID_BODY, "ex-1", ui_language="it", config=ENABLED)

    assert "textContent" in out
    assert "innerHTML" not in out


def test_invalid_body_shows_errors_and_no_panel() -> None:
    out = render_dialogue_exercise("type: dialogue\nlevel: Z9\n", "ex-1", ui_language="it", config=ENABLED)

    assert "edutex-dialogue-error" in out
    assert "livello non valido: Z9" in out
    assert "<script" not in out


def test_exercise_id_is_attribute_escaped() -> None:
    out = render_dialogue_exercise(VALID_BODY, 'a"b', ui_language="en", config=DISABLED)

    assert 'data-dialogue-id="a&quot;b"' in out


def test_rendering_is_deterministic() -> None:
    first = render_dialogue_exercise(VALID_BODY, "ex-1", ui_language="it", config=ENABLED)
    second = render_dialogue_exercise(VALID_BODY, "ex-1", ui_language="it", config=ENABLED)

    assert first == second