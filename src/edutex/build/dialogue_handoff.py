"""Hand-off mode for the dialogue exercise.

The page does not call any API. It copies the exercise instructions to the
clipboard and opens the configured Langdock agent in a new tab.
"""

from __future__ import annotations

from typing import Any

from edutex.build.dialogue import DialogueSpec, build_system_prompt, parse_dialogue_body
from edutex.build.dialogue_render import (
    _esc,
    _fallback_html,
    _header,
    _labels_for,
    _render_errors,
    _script_json,
    _summary_html,
    _wrap,
)

EXERCISE_TAG = "ESERCIZIO DIALOGO"

_HANDOFF_LABELS: dict[str, dict[str, str]] = {
    "it": {
        "button": "Apri l'agente e copia l'esercizio",
        "open_link": "Apri l'agente",
        "copied": "Esercizio copiato. Si apre l'agente: incolla il testo nella chat e invia.",
        "manual": "Copia manualmente il testo qui sotto e incollalo nella chat dell'agente.",
        "blocked": "Il browser ha bloccato la nuova scheda: usa il link qui sotto.",
        "invalid_url": "Link dell'agente non valido: deve iniziare con https://",
    },
    "en": {
        "button": "Open the agent and copy the exercise",
        "open_link": "Open the agent",
        "copied": "Exercise copied. The agent is opening: paste the text in the chat and send it.",
        "manual": "Copy the text below manually and paste it into the agent chat.",
        "blocked": "The browser blocked the new tab: use the link below.",
        "invalid_url": "Invalid agent link: it must start with https://",
    },
}

_HANDOFF_SCRIPT = r"""
(function () {
  var root = document.currentScript.closest(".edutex-dialogue");
  if (!root) { return; }
  var cfg = JSON.parse(root.querySelector("[data-langdock-config]").textContent);
  var button = root.querySelector("[data-langdock-handoff]");
  var status = root.querySelector("[data-langdock-status]");
  var area = root.querySelector("[data-langdock-text]");

  button.addEventListener("click", function () {
    var win = window.open(cfg.url, "_blank");
    var blocked = !win;
    if (win) { win.opener = null; }

    function done(message) {
      status.textContent = message + (blocked ? " " + cfg.blocked : "");
    }

    function manualCopy() {
      area.hidden = false;
      area.focus();
      area.select();
      var ok = false;
      try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
      done(ok ? cfg.copied : cfg.manual);
    }

    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(cfg.text).then(function () {
        done(cfg.copied);
      }, manualCopy);
    } else {
      manualCopy();
    }
  });
})();
"""


def _labels(ui_language: str | None) -> dict[str, str]:
    code = str(ui_language or "en").strip().lower()[:2]
    return _HANDOFF_LABELS.get(code, _HANDOFF_LABELS["en"])


def _exercise_text(spec: DialogueSpec, start_prompt: str) -> str:
    title = spec.title or spec.topic
    return "\n".join(
        [
            f"[{EXERCISE_TAG}: {title}]",
            "",
            build_system_prompt(spec),
            "",
            start_prompt,
        ]
    )


def render_langdock_handoff(
    body: str,
    exercise_id: str,
    *,
    ui_language: str | None = "en",
    langdock_url: str,
) -> str:
    """Render the exercise with a button that copies its text and opens the agent."""
    from edutex.build.dialogue_render import _labels_for as _base_labels

    base = _base_labels(ui_language)
    hl = _labels(ui_language)
    eid = _esc(exercise_id)
    parsed = parse_dialogue_body(body)
    if parsed.spec is None:
        return _render_errors(parsed.errors, eid, base)

    url = langdock_url.strip()
    if not url.startswith("https://"):
        return _render_errors((hl["invalid_url"],), eid, base)

    spec = parsed.spec
    text = _exercise_text(spec, base["start_prompt"])
    data: dict[str, Any] = {
        "url": url,
        "text": text,
        "copied": hl["copied"],
        "manual": hl["manual"],
        "blocked": hl["blocked"],
    }
    inner = (
        _header(spec, base)
        + _summary_html(spec, base)
        + _fallback_html(spec, base, hidden=False)
        + '<div class="edutex-dialogue-actions">\n'
        + f'<button type="button" data-langdock-handoff>{_esc(hl["button"])}</button>\n'
        + f'<a href="{_esc(url)}" target="_blank" rel="noopener noreferrer">{_esc(hl["open_link"])}</a>\n'
        + "</div>\n"
        + '<p class="edutex-dialogue-status" data-langdock-status role="status"></p>\n'
        + f'<textarea data-langdock-text readonly rows="10" hidden>{_esc(text)}</textarea>\n'
        + f'<script type="application/json" data-langdock-config>{_script_json(data)}</script>\n'
        + f"<script>{_HANDOFF_SCRIPT}</script>\n"
    )
    return _wrap(eid, inner)