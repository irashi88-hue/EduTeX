"""Contract tests for the Langdock hand-off mode of the dialogue exercise."""

from __future__ import annotations

import json
import re
from types import SimpleNamespace

from edutex.build.dialogue import build_system_prompt, parse_dialogue_body
from edutex.build.dialogue_render import render_dialogue_exercise
from edutex.configuration.schema import DialogueConfig

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

URL = "https://app.langdock.com/assistants/test-agent/chat"
HANDOFF = SimpleNamespace(
    enabled=False, endpoint="http://localhost:11434", model="", timeout_seconds=60, langdock_url=URL
)
CONFIG_PATTERN = r'<script type="application/json" data-langdock-config>(.*?)</script>'


def _config(out: str) -> dict:
    match = re.search(CONFIG_PATTERN, out, re.S)
    assert match is not None
    return json.loads(match.group(1))


def test_handoff_renders_button_and_link() -> None:
    out = render_dialogue_exercise(VALID_BODY, "ex-1", ui_language="it", config=HANDOFF)

    assert "data-langdock-handoff" in out
    assert "madrelingua" in out
    assert f'href="{URL}"' in out


def test_handoff_uses_only_the_configured_url() -> None:
    out = render_dialogue_exercise(VALID_BODY, "ex-1", ui_language="it", config=HANDOFF)

    urls = set(re.findall(r"https?://[^\"'\s<]+", out))
    assert urls == {URL}


def test_copied_text_contains_the_exact_system_prompt() -> None:
    out = render_dialogue_exercise(VALID_BODY, "ex-1", ui_language="it", config=HANDOFF)

    data = _config(out)
    spec = parse_dialogue_body(VALID_BODY).spec
    assert spec is not None
    assert data["text"].startswith("[ESERCIZIO DIALOGO")
    assert build_system_prompt(spec) in data["text"]
    assert "VALUTA" in data["text"]


def test_non_https_url_is_rejected() -> None:
    cfg = SimpleNamespace(**{**HANDOFF.__dict__, "langdock_url": "javascript:alert(1)"})
    out = render_dialogue_exercise(VALID_BODY, "ex-1", ui_language="it", config=cfg)

    assert "edutex-dialogue-error" in out
    assert "data-langdock-handoff" not in out


def test_user_content_cannot_inject_markup_in_handoff() -> None:
    body = VALID_BODY.replace("topic: al ristorante", "topic: </script><img src=x onerror=alert(1)>")
    out = render_dialogue_exercise(body, "ex-1", ui_language="it", config=HANDOFF)

    assert "<img" not in out
    assert "</script><img" not in out


def test_handoff_does_not_use_inner_html() -> None:
    out = render_dialogue_exercise(VALID_BODY, "ex-1", ui_language="it", config=HANDOFF)

    assert "innerHTML" not in out


def test_empty_url_keeps_static_fallback() -> None:
    cfg = SimpleNamespace(**{**HANDOFF.__dict__, "langdock_url": ""})
    out = render_dialogue_exercise(VALID_BODY, "ex-1", ui_language="it", config=cfg)

    assert "data-langdock-handoff" not in out
    assert "<script" not in out


def test_schema_accepts_langdock_url() -> None:
    cfg = DialogueConfig(langdock_url=URL)

    assert cfg.langdock_url == URL