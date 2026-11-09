"""HTML rendering for the text-only dialogue exercise.

The exercise data and the fixed system prompt are embedded as JSON. The
browser calls only the configured local endpoint and shows the model output
as plain text. Without an enabled configuration the renderer emits a static
printable block with a self-check list.
"""

from __future__ import annotations

import html
import json
from typing import Any

from edutex.build.dialogue import DialogueSpec, build_system_prompt, parse_dialogue_body

_LABELS: dict[str, dict[str, str]] = {
    "it": {
        "title": "Dialogo guidato",
        "level": "Livello",
        "topic": "Tema",
        "role": "Ruolo",
        "goal": "Obiettivo",
        "vocabulary": "Lessico",
        "structures": "Strutture",
        "criteria": "Criteri",
        "start": "Avvia",
        "send": "Invia",
        "finish": "Termina e valuta",
        "download": "Scarica trascrizione",
        "input_label": "Il tuo messaggio",
        "disclaimer": "Il verdetto è indicativo e non sostituisce la valutazione dell'insegnante.",
        "verdict_label": "Verdetto indicativo",
        "verdict_missing": "Verdetto non disponibile: serve la valutazione dell'insegnante.",
        "fallback_title": "Traccia per l'esercizio",
        "fallback_note": "Svolgi il dialogo con un compagno o da solo, poi controlla i criteri.",
        "self_check": "Autovalutazione",
        "error_title": "Esercizio dialogue non valido",
        "waiting": "In attesa della risposta...",
        "unavailable": "Il modello non risponde: resta disponibile la traccia stampabile.",
        "you": "Tu",
        "teacher": "Insegnante",
        "start_prompt": "Inizia la conversazione con la prima domanda, nella lingua dell'esercizio.",
        "verdict_request": "Valuta ora la conversazione secondo il formato del verdetto.",
    },
    "en": {
        "title": "Guided dialogue",
        "level": "Level",
        "topic": "Topic",
        "role": "Role",
        "goal": "Goal",
        "vocabulary": "Vocabulary",
        "structures": "Structures",
        "criteria": "Criteria",
        "start": "Start",
        "send": "Send",
        "finish": "Finish and assess",
        "download": "Download transcript",
        "input_label": "Your message",
        "disclaimer": "The verdict is indicative and does not replace the teacher's assessment.",
        "verdict_label": "Indicative verdict",
        "verdict_missing": "No verdict available: the teacher's assessment is required.",
        "fallback_title": "Exercise outline",
        "fallback_note": "Do the dialogue with a partner or alone, then check the criteria.",
        "self_check": "Self-assessment",
        "error_title": "Invalid dialogue exercise",
        "waiting": "Waiting for the reply...",
        "unavailable": "The model is not responding: the printable outline remains available.",
        "you": "You",
        "teacher": "Teacher",
        "start_prompt": "Start the conversation with the first question, in the language of the exercise.",
        "verdict_request": "Now assess the conversation according to the verdict format.",
    },
}

_STYLE = """
.edutex-dialogue{border:1px solid #c9d3df;border-radius:8px;padding:1rem 1.25rem;margin:1.5rem 0;}
.edutex-dialogue dl{display:grid;grid-template-columns:max-content 1fr;gap:.25rem 1rem;}
.edutex-dialogue dt{font-weight:600;}
.edutex-dialogue dd{margin:0;}
.edutex-dialogue-chat{max-height:24rem;overflow-y:auto;margin:.75rem 0;}
.edutex-dialogue-line p{margin:.15rem 0 .6rem;white-space:pre-wrap;}
.edutex-dialogue textarea{width:100%;box-sizing:border-box;}
.edutex-dialogue-actions{display:flex;flex-wrap:wrap;gap:.5rem;margin-top:.5rem;}
.edutex-dialogue button:focus-visible,.edutex-dialogue textarea:focus-visible,.edutex-dialogue input:focus-visible{outline:3px solid #1a5fb4;outline-offset:2px;}
.edutex-dialogue button:disabled,.edutex-dialogue textarea:disabled{opacity:.6;}
.edutex-dialogue-error{border-color:#b42318;}
@media (prefers-reduced-motion: reduce){.edutex-dialogue *{transition:none!important;animation:none!important;}}
"""

_CLIENT_SCRIPT = r"""
(function () {
  var root = document.currentScript.closest(".edutex-dialogue");
  if (!root) { return; }
  var data = JSON.parse(root.querySelector("[data-dialogue-config]").textContent);
  var L = data.labels;
  var chat = root.querySelector("[data-dialogue-chat]");
  var statusEl = root.querySelector("[data-dialogue-status]");
  var verdictEl = root.querySelector("[data-dialogue-verdict]");
  var form = root.querySelector("[data-dialogue-form]");
  var input = root.querySelector("[data-dialogue-input]");
  var startBtn = root.querySelector("[data-dialogue-start]");
  var sendBtn = root.querySelector("[data-dialogue-send]");
  var finishBtn = root.querySelector("[data-dialogue-finish]");
  var downloadBtn = root.querySelector("[data-dialogue-download]");
  var fallback = root.querySelector("[data-dialogue-fallback]");
  var apiMessages = [];
  var transcript = [];
  var studentTurns = 0;
  var started = false;
  var finished = false;
  var busy = false;

  function refresh() {
    var active = started && !finished && !busy;
    input.disabled = !active;
    sendBtn.disabled = !active;
    finishBtn.disabled = !active || studentTurns === 0;
    startBtn.disabled = started || busy;
    downloadBtn.disabled = transcript.length === 0;
  }

  function addLine(role, text) {
    var who = role === "user" ? L.you : L.teacher;
    transcript.push(who + ": " + text);
    var wrap = document.createElement("div");
    wrap.className = "edutex-dialogue-line edutex-dialogue-" + role;
    var label = document.createElement("strong");
    label.textContent = who;
    var body = document.createElement("p");
    body.textContent = text;
    wrap.appendChild(label);
    wrap.appendChild(body);
    chat.appendChild(wrap);
    chat.scrollTop = chat.scrollHeight;
  }

  function callModel() {
    var controller = new AbortController();
    var timer = setTimeout(function () { controller.abort(); }, data.timeoutMs);
    var payload = {
      model: data.model,
      stream: false,
      messages: [{ role: "system", content: data.system }].concat(apiMessages)
    };
    return fetch(data.endpoint + "/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal
    })
      .then(function (res) {
        if (!res.ok) { throw new Error("http " + res.status); }
        return res.json();
      })
      .then(function (json) {
        var content = json && json.message && typeof json.message.content === "string" ? json.message.content : "";
        if (!content) { throw new Error("empty reply"); }
        return content;
      })
      .finally(function () { clearTimeout(timer); });
  }

  function exchange() {
    busy = true;
    statusEl.textContent = L.waiting;
    refresh();
    return callModel()
      .then(function (reply) {
        statusEl.textContent = "";
        apiMessages.push({ role: "assistant", content: reply });
        return reply;
      })
      .catch(function () {
        statusEl.textContent = L.unavailable;
        if (fallback) { fallback.hidden = false; }
        return null;
      })
      .finally(function () {
        busy = false;
        refresh();
      });
  }

  function showVerdict(reply) {
    var lines = reply.split("\n").map(function (s) { return s.trim(); })
      .filter(function (s) { return s.length > 0; }).slice(-6);
    var idx = -1;
    var status = null;
    var criteria = null;
    var i;
    for (i = 0; i < lines.length; i++) {
      var m = lines[i].match(/^VERDETTO:\s*(SUPERATO|NON SUPERATO)$/);
      if (m) { idx = i; status = m[1]; break; }
    }
    verdictEl.textContent = "";
    verdictEl.hidden = false;
    if (idx < 0) {
      verdictEl.textContent = L.verdict_missing;
      return;
    }
    for (i = idx + 1; i < lines.length; i++) {
      var c = lines[i].match(/^CRITERI:\s*(\d+\/\d+)$/);
      if (c) { criteria = c[1]; break; }
    }
    var head = document.createElement("p");
    var strong = document.createElement("strong");
    strong.textContent = L.verdict_label + ": " + status + (criteria ? " (" + criteria + ")" : "");
    head.appendChild(strong);
    var note = document.createElement("p");
    note.textContent = L.disclaimer;
    verdictEl.appendChild(head);
    verdictEl.appendChild(note);
  }

  function start() {
    if (started || busy) { return; }
    started = true;
    apiMessages.push({ role: "user", content: L.start_prompt });
    refresh();
    exchange().then(function (reply) {
      if (reply === null) {
        started = false;
        apiMessages.length = 0;
        refresh();
        return;
      }
      addLine("teacher", reply);
      refresh();
    });
  }

  function requestVerdict() {
    apiMessages.push({ role: "user", content: L.verdict_request });
    exchange().then(function (reply) {
      if (reply === null) {
        apiMessages.pop();
        refresh();
        return;
      }
      finished = true;
      addLine("teacher", reply);
      showVerdict(reply);
      refresh();
    });
  }

  function submitStudent(text) {
    studentTurns += 1;
    addLine("user", text);
    apiMessages.push({ role: "user", content: text });
    exchange().then(function (reply) {
      if (reply === null) { return; }
      addLine("teacher", reply);
      if (studentTurns >= data.maxTurns) { requestVerdict(); }
    });
  }

  function downloadTranscript() {
    var blob = new Blob([transcript.join("\n\n") + "\n"], { type: "text/plain;charset=utf-8" });
    var url = URL.createObjectURL(blob);
    var link = document.createElement("a");
    link.href = url;
    link.download = "trascrizione-" + String(data.id).replace(/[^A-Za-z0-9_-]/g, "_") + ".txt";
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 0);
  }

  startBtn.addEventListener("click", start);
  form.addEventListener("submit", function (event) {
    event.preventDefault();
    var text = input.value.trim();
    if (!text || !started || finished || busy) { return; }
    input.value = "";
    submitStudent(text);
  });
  finishBtn.addEventListener("click", function () {
    if (!started || finished || busy || studentTurns === 0) { return; }
    requestVerdict();
  });
  downloadBtn.addEventListener("click", downloadTranscript);
  refresh();
})();
"""


def _labels_for(ui_language: str | None) -> dict[str, str]:
    code = str(ui_language or "en").strip().lower()[:2]
    return _LABELS.get(code, _LABELS["en"])


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _script_json(data: dict[str, Any]) -> str:
    text = json.dumps(data, ensure_ascii=False, sort_keys=True)
    for char, escaped in (
        ("<", "\\u003c"),
        (">", "\\u003e"),
        ("&", "\\u0026"),
        ("\u2028", "\\u2028"),
        ("\u2029", "\\u2029"),
    ):
        text = text.replace(char, escaped)
    return text


def _header(spec: DialogueSpec, labels: dict[str, str]) -> str:
    return f"<h3>{_esc(spec.title or labels['title'])}</h3>\n"


def _summary_html(spec: DialogueSpec, labels: dict[str, str]) -> str:
    rows = [
        (labels["level"], spec.level),
        (labels["topic"], spec.topic),
        (labels["role"], spec.role),
        (labels["goal"], spec.goal),
    ]
    if spec.vocabulary:
        rows.append((labels["vocabulary"], ", ".join(spec.vocabulary)))
    if spec.structures:
        rows.append((labels["structures"], ", ".join(spec.structures)))
    items = "".join(f"<dt>{_esc(key)}</dt><dd>{_esc(value)}</dd>" for key, value in rows)
    return f"<dl>{items}</dl>\n"


def _fallback_html(spec: DialogueSpec, labels: dict[str, str], hidden: bool) -> str:
    attribute = " hidden" if hidden else ""
    boxes = "".join(
        f'<li><label><input type="checkbox"> {_esc(criterion)}</label></li>'
        for criterion in spec.criteria
    )
    return (
        f'<div class="edutex-dialogue-fallback" data-dialogue-fallback{attribute}>\n'
        f"<h4>{_esc(labels['fallback_title'])}</h4>\n"
        f"<p>{_esc(labels['fallback_note'])}</p>\n"
        f"<p><strong>{_esc(labels['criteria'])}</strong></p>\n"
        f"<ul>{boxes}</ul>\n"
        f"<p><strong>{_esc(labels['self_check'])}</strong></p>\n"
        "</div>\n"
    )


def _wrap(eid: str, inner: str) -> str:
    return (
        f"<style>{_STYLE}</style>\n"
        f'<section class="edutex-dialogue" data-dialogue-id="{eid}">\n'
        f"{inner}"
        "</section>"
    )


def _render_errors(errors: tuple[str, ...], eid: str, labels: dict[str, str]) -> str:
    items = "".join(f"<li>{_esc(error)}</li>" for error in errors)
    return (
        f"<style>{_STYLE}</style>\n"
        f'<section class="edutex-dialogue edutex-dialogue-error" role="alert" data-dialogue-id="{eid}">\n'
        f"<h3>{_esc(labels['error_title'])}</h3>\n"
        f"<ul>{items}</ul>\n"
        "</section>"
    )


def _render_static(spec: DialogueSpec, eid: str, labels: dict[str, str]) -> str:
    return _wrap(
        eid,
        _header(spec, labels) + _summary_html(spec, labels) + _fallback_html(spec, labels, hidden=False),
    )


def _render_interactive(
    spec: DialogueSpec,
    exercise_id: str,
    eid: str,
    labels: dict[str, str],
    config: Any,
) -> str:
    data: dict[str, Any] = {
        "id": exercise_id,
        "endpoint": str(config.endpoint).rstrip("/"),
        "model": str(config.model),
        "timeoutMs": int(config.timeout_seconds) * 1000,
        "system": build_system_prompt(spec),
        "maxTurns": spec.max_turns,
        "labels": labels,
    }
    config_block = (
        f'<script type="application/json" data-dialogue-config>{_script_json(data)}</script>\n'
    )
    form = (
        "<form data-dialogue-form>\n"
        f'<label for="{eid}-input">{_esc(labels["input_label"])}</label>\n'
        f'<textarea id="{eid}-input" rows="3" data-dialogue-input disabled></textarea>\n'
        '<div class="edutex-dialogue-actions">\n'
        f'<button type="button" data-dialogue-start>{_esc(labels["start"])}</button>\n'
        f'<button type="submit" data-dialogue-send disabled>{_esc(labels["send"])}</button>\n'
        f'<button type="button" data-dialogue-finish disabled>{_esc(labels["finish"])}</button>\n'
        f'<button type="button" data-dialogue-download disabled>{_esc(labels["download"])}</button>\n'
        "</div>\n"
        "</form>\n"
    )
    inner = (
        _header(spec, labels)
        + _summary_html(spec, labels)
        + _fallback_html(spec, labels, hidden=True)
        + '<div class="edutex-dialogue-chat" data-dialogue-chat></div>\n'
        + '<p class="edutex-dialogue-status" data-dialogue-status role="status"></p>\n'
        + '<div class="edutex-dialogue-verdict" data-dialogue-verdict hidden></div>\n'
        + form
        + f'<p class="edutex-dialogue-disclaimer">{_esc(labels["disclaimer"])}</p>\n'
        + config_block
        + f"<script>{_CLIENT_SCRIPT}</script>\n"
    )
    return _wrap(eid, inner)


def render_dialogue_exercise(
    body: str,
    exercise_id: str,
    *,
    ui_language: str | None = "en",
    config: Any = None,
) -> str:
    """Render a dialogue exercise as HTML.

    Returns an error block when the body is invalid, a static printable block
    when the dialogue is disabled or absent, and an interactive panel otherwise.
    """
    labels = _labels_for(ui_language)
    parsed = parse_dialogue_body(body)
    eid = _esc(exercise_id)
    if parsed.spec is None:
        return _render_errors(parsed.errors, eid, labels)
    if not bool(getattr(config, "enabled", False)):
        return _render_static(parsed.spec, eid, labels)
    return _render_interactive(parsed.spec, exercise_id, eid, labels, config)