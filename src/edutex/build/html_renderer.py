"""EduTeX HTML renderer.

Produces a self-contained, accessible HTML document from DocumentStructure.
Rendering is pure string transformation and does not perform file I/O.
"""

from __future__ import annotations

import html
import json
import re

from edutex.knowledge.models import TextBlock
from edutex.layout.models import DocumentStructure
from edutex.theme.models import StyledNode, ThemeModel


_EDUTEX_UI_LABELS = {
    "en": {
        "rule": "Rule", "note": "Note", "example": "Example", "exercise": "Exercise",
        "solution": "Solution", "solutions": "Solutions", "subject": "Subject", "form": "Form",
        "meaning": "Meaning", "conjugation": "Conjugation", "infinitive": "Infinitive",
        "translation": "Translation", "gender_plural": "Gender / plural", "grammar": "Grammar",
        "third_person": "3rd person", "word": "Word", "example_field": "Example",
        "auxiliary": "Auxiliary", "participle": "Participle",
        "chemical_formula": "Chemical formula", "mathematical_formula": "Mathematical formula",
        "show_solution": "Show / hide solution", "answer": "Answer", "options": "Options",
        "translation_prompt": "Text to translate", "write_translation": "Write your translation",
        "matching": "Matching", "matching_word": "Word", "matching_meaning": "Meaning",
        "choose_meaning": "Choose a meaning", "no_matching_data": "No matching pairs configured.",
        "check_matching": "Check answers", "matching_correct": "Correct",
        "matching_wrong": "Not correct", "matching_missing": "Choose a meaning",
        "matching_duplicate": "Already used",
        "matching_result": "Matching result", "reset_matching": "Reset exercise",
        "builder": "Sentence builder", "builder_tokens": "Available words",
        "builder_answer": "Your sentence", "builder_placeholder": "Click words to build the sentence",
        "check_builder": "Check sentence", "builder_correct": "Correct",
        "builder_wrong": "Not correct", "builder_empty": "Build a sentence first",
        "reset_builder": "Reset sentence", "remove_builder_token": "Remove word",
        "true_false": "True or false", "true": "True", "false": "False",
        "check_true_false": "Check answers", "reset_true_false": "Reset exercise",
        "tf_correct": "Correct", "tf_wrong": "Not correct",
        "tf_missing": "Choose true or false", "tf_invalid": "Invalid true/false exercise.", "tf_result": "True/false result",
        "cloze": "Fill in the blanks", "cloze_tokens": "Available words",
        "cloze_sentence": "Sentence", "cloze_placeholder": "Click a word",
        "check_cloze": "Check answers", "reset_cloze": "Reset exercise",
        "cloze_correct": "Correct", "cloze_wrong": "Not correct",
        "cloze_missing": "Fill this blank", "cloze_result": "Cloze result",
        "short_answer": "Short answer", "short_prompt": "Answer",
        "short_placeholder": "Write your answer", "check_short": "Check answer",
        "reset_short": "Reset answer", "short_correct": "Correct",
        "short_wrong": "Not correct", "short_empty": "Write an answer first",
        "check_choice": "Check answer", "reset_choice": "Reset exercise",
        "choice_correct": "Correct", "choice_wrong": "Not correct",
        "choice_missing": "Select an answer", "choice_result": "Choice result",
        "special_chars": "Special characters",
        "skip": "Skip to content", "document_content": "Document content","contents": "Contents",
    },
    "it": {
        "rule": "Regola", "note": "Nota", "example": "Esempio", "exercise": "Esercizio",
        "solution": "Soluzione", "solutions": "Soluzioni", "subject": "Persona", "form": "Forma",
        "meaning": "Significato", "conjugation": "Coniugazione", "infinitive": "Infinito",
        "translation": "Traduzione", "gender_plural": "Genere / plurale", "grammar": "Grammatica",
        "third_person": "3ª persona", "word": "Parola", "example_field": "Esempio",
        "auxiliary": "Ausiliare", "participle": "Participio",
        "chemical_formula": "Formula chimica", "mathematical_formula": "Formula matematica",
        "show_solution": "Mostra / nascondi soluzione", "answer": "Risposta", "options": "Opzioni",
        "translation_prompt": "Testo da tradurre", "write_translation": "Scrivi la traduzione",
        "matching": "Abbinamento", "matching_word": "Parola", "matching_meaning": "Significato",
        "choose_meaning": "Scegli un significato", "no_matching_data": "Nessuna coppia configurata.",
        "check_matching": "Verifica risposte", "matching_correct": "Corretta",
        "matching_wrong": "Non corretta", "matching_missing": "Scegli un significato",
        "matching_duplicate": "Già utilizzato",
        "matching_result": "Risultato abbinamento", "reset_matching": "Azzera esercizio",
        "builder": "Costruzione frase", "builder_tokens": "Parole disponibili",
        "builder_answer": "La tua frase", "builder_placeholder": "Clicca sulle parole per costruire la frase",
        "check_builder": "Verifica frase", "builder_correct": "Corretta",
        "builder_wrong": "Non corretta", "builder_empty": "Costruisci prima una frase",
        "reset_builder": "Azzera frase", "remove_builder_token": "Rimuovi parola",
        "true_false": "Vero o falso", "true": "Vero", "false": "Falso",
        "check_true_false": "Verifica risposte", "reset_true_false": "Azzera esercizio",
        "tf_correct": "Corretta", "tf_wrong": "Non corretta",
        "tf_missing": "Scegli vero o falso", "tf_invalid": "Esercizio Vero/Falso non valido.", "tf_result": "Risultato vero o falso",
        "cloze": "Completa la frase", "cloze_tokens": "Parole disponibili",
        "cloze_sentence": "Frase", "cloze_placeholder": "Clicca una parola",
        "check_cloze": "Verifica risposte", "reset_cloze": "Azzera esercizio",
        "cloze_correct": "Corretta", "cloze_wrong": "Non corretta",
        "cloze_missing": "Completa questo spazio", "cloze_result": "Risultato completamento",
        "short_answer": "Risposta breve", "short_prompt": "Risposta",
        "short_placeholder": "Scrivi la tua risposta", "check_short": "Verifica risposta",
        "reset_short": "Azzera risposta", "short_correct": "Corretta",
        "short_wrong": "Non corretta", "short_empty": "Scrivi prima una risposta",
        "check_choice": "Verifica risposta", "reset_choice": "Azzera esercizio",
        "choice_correct": "Corretta", "choice_wrong": "Non corretta",
        "choice_missing": "Seleziona una risposta", "choice_result": "Risultato scelta",
        "special_chars": "Caratteri speciali",
        "skip": "Vai al contenuto", "document_content": "Contenuto del documento","contents": "Indice",
    },
}

# Japanese interface labels. Untranslated exercise-specific labels intentionally
# fall back to English until the complete Japanese UI catalogue is added.
_EDUTEX_UI_LABELS["ja"] = {
    **_EDUTEX_UI_LABELS["en"],
    "rule": "規則",
    "example": "例",
    "exercise": "練習",
    "solution": "解答",
    "solutions": "解答",
    "contents": "目次",
    "skip": "コンテンツへ移動",
    "document_content": "文書の内容",
}


def _ui_language(value: object) -> str:
    code = str(value or "en").lower().replace("_", "-").split("-", 1)[0]
    # German is the learning language; the instructional interface is Italian.
    if code == "ja":
        return "ja"
    return "it" if code in {"it", "de"} else "en"


class HtmlRenderer:
    """Render a DocumentStructure as a complete standalone HTML document."""

    def render(self, doc: DocumentStructure, meta: object, theme: ThemeModel) -> str:
        self._heading_entries: list[tuple[int, str, str]] = []
        self._used_ids: set[str] = set()
        self._labels = _EDUTEX_UI_LABELS[_ui_language(getattr(meta, "language", "en"))]
        body_parts: list[str] = []
        all_items: list[tuple[int, object]] = []

        for element in doc.elements:
            all_items.append((element.position_index, element))
        for position, block in doc.prose_blocks:
            all_items.append((position, block))
        all_items.sort(key=lambda item: item[0])

        for _, item in all_items:
            if isinstance(item, TextBlock):
                rendered = self._render_prose(item)
            else:
                rendered = self._render_element(item)
            if rendered.strip():
                body_parts.append(rendered)

        if doc.appendix_nodes and doc.layout_model.appendix.enabled:
            appendix_title = self._labels["solutions"] if doc.layout_model.appendix.title == "Solutions" else doc.layout_model.appendix.title
            solutions_section_id = self._unique_id("solutions", appendix_title)
            solutions_heading_id = self._unique_id("heading", appendix_title)
            self._heading_entries.append((2, solutions_heading_id, appendix_title))
            appendix = [
                f'<section id="{solutions_section_id}" class="solutions" aria-labelledby="{solutions_heading_id}">',
                f'<h2 id="{solutions_heading_id}">{html.escape(appendix_title)}</h2>',
            ]
            references = getattr(doc, "solution_references", [])
            appendix.extend(
                self._render_solution(
                    node,
                    references[index] if index < len(references) else None,
                )
                for index, node in enumerate(doc.appendix_nodes)
            )
            appendix.append("</section>")
            body_parts.append("\n".join(appendix))

        title = html.escape(str(getattr(meta, "title", "EduTeX")))
        author = html.escape(str(getattr(meta, "author", "")))
        language = html.escape(str(getattr(meta, "language", "en")))
        toc_html = self._render_toc()
        return self._document(title, author, language, theme, toc_html, "\n".join(body_parts))

    def _document(
        self,
        title: str,
        author: str,
        language: str,
        theme: ThemeModel,
        toc_html: str,
        body: str,
    ) -> str:
        colors = self._theme_colors(theme)
        palette = self._theme_palette(theme)
        author_html = f'<p class="author">{author}</p>' if author else ""
        return f"""<!doctype html>
<html lang="{language}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="generator" content="EduTeX">
  <title>{title}</title>
  <style>
    :root {{
      color-scheme: light;
      --page-bg: {colors['page_bg']};
      --canvas-bg: {colors['canvas_bg']};
      --surface: #ffffff;
      --surface-subtle: #f8fafc;
      --ink: {colors['ink']};
      --muted: {colors['muted']};
      --control-bg: #ffffff;
      --control-bg-hover: #eef2ff;
      --control-bg-strong: #e0e7ff;
      --control-bg-strong-hover: #c7d2fe;
      --control-border: rgba(67, 56, 202, .35);
      --control-border-soft: rgba(67, 56, 202, .22);
      --control-border-strong: #a5b4fc;
      --input-bg: rgba(255, 255, 255, .85);
      --code-bg: rgba(23, 32, 51, .08);
      --neutral-line: rgba(83, 97, 118, .25);
      --shadow: rgba(23, 32, 51, .08);
      --on-accent: #ffffff;
      --success-border: #15803d;
      --success-bg: #f0fdf4;
      --success-bg-strong: #dcfce7;
      --success-ink: #166534;
      --danger-border: #b91c1c;
      --danger-bg: #fef2f2;
      --danger-bg-strong: #fee2e2;
      --danger-ink: #991b1b;
      --warning-border: #b45309;
      --warning-bg: #fffbeb;
      --warning-bg-strong: #fef3c7;
      --print-bg: #ffffff;
      --rule-color: {colors['rule_color']};
      --rule-bg: {colors['rule_bg']};
      --note-color: {colors['note_color']};
      --note-bg: {colors['note_bg']};
      --example-color: {colors['example_color']};
      --example-bg: {colors['example_bg']};
      --exercise-color: {colors['exercise_color']};
      --exercise-bg: {colors['exercise_bg']};
      --vocab-color: {colors['vocab_color']};
      --vocab-bg: {colors['vocab_bg']};
      --solution-color: {colors['solution_color']};
      --solution-bg: {colors['solution_bg']};
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        color-scheme: dark;
        --page-bg: #0f172a;
        --canvas-bg: #020617;
        --surface: #111827;
        --surface-subtle: #1e293b;
        --ink: #e5e7eb;
        --muted: #cbd5e1;
        --control-bg: #0f172a;
        --control-bg-hover: #1e293b;
        --control-bg-strong: #312e81;
        --control-bg-strong-hover: #4338ca;
        --control-border: rgba(165, 180, 252, .60);
        --control-border-soft: rgba(165, 180, 252, .38);
        --control-border-strong: #a5b4fc;
        --input-bg: rgba(15, 23, 42, .88);
        --code-bg: rgba(255, 255, 255, .10);
        --neutral-line: rgba(203, 213, 225, .35);
        --shadow: rgba(0, 0, 0, .35);
        --on-accent: #0b1020;
        --success-border: #86efac;
        --success-bg: #052e16;
        --success-bg-strong: #14532d;
        --success-ink: #bbf7d0;
        --danger-border: #fca5a5;
        --danger-bg: #450a0a;
        --danger-bg-strong: #7f1d1d;
        --danger-ink: #fecaca;
        --warning-border: #fbbf24;
        --warning-bg: #422006;
        --warning-bg-strong: #713f12;
        --rule-color: #93c5fd;
        --rule-bg: #172554;
        --note-color: #fbbf24;
        --note-bg: #422006;
        --example-color: #5eead4;
        --example-bg: #042f2e;
        --exercise-color: #a5b4fc;
        --exercise-bg: #1e1b4b;
        --vocab-color: #cbd5e1;
        --vocab-bg: #1e293b;
        --solution-color: #86efac;
        --solution-bg: #052e16;
      }}
    }}    * {{ box-sizing: border-box; }}
    :focus-visible {{ outline: 3px solid var(--rule-color); outline-offset: 3px; }}
    .skip-link {{
      position: absolute;
      left: 1rem;
      top: -4rem;
      z-index: 10;
      padding: .55rem .8rem;
      background: var(--ink);
      color: var(--on-accent);
      text-decoration: none;
      font-weight: 700;
    }}
    .skip-link:focus {{ top: 1rem; }}
    body {{
      margin: 0;
      background: var(--canvas-bg);
      color: var(--ink);
      font-family: Inter, "Segoe UI", Arial, sans-serif;
      font-size: 1rem;
      line-height: 1.65;
    }}
    main {{
      max-width: 900px;
      margin: 0 auto;
      padding: 3rem 1.25rem 5rem;
    }}
    .masthead {{
      background: var(--page-bg);
      border-top: 8px solid var(--rule-color);
      padding: 2.25rem clamp(1.25rem, 4vw, 3.5rem);
      margin-bottom: 2rem;
      box-shadow: 0 8px 28px var(--shadow);
    }}
    h1, h2, h3, h4 {{ line-height: 1.2; margin-top: 0; }}
    h1 {{ font-size: clamp(2rem, 5vw, 3.25rem); letter-spacing: -.035em; margin-bottom: .45rem; }}
    h2 {{ font-size: 1.7rem; margin: 2.2rem 0 .8rem; }}
    h3 {{ font-size: 1.2rem; margin-bottom: .55rem; }}
    .author {{ color: var(--muted); margin: 0; }}
    .toc {{
      background: var(--surface);
      border-left: 5px solid var(--muted);
      padding: 1rem 1.25rem;
      margin: 0 0 2rem;
      box-shadow: 0 3px 14px var(--shadow);
    }}
    .toc-title {{ margin: 0 0 .4rem; font-size: 1rem; }}
    .toc ol {{ margin: 0; padding-left: 1.25rem; }}
    .toc li {{ margin: .15rem 0; }}
    .toc ol ol {{ margin-top: .15rem; }}
    .toc a {{ color: var(--rule-color); font-weight: 600; }}
    .sr-only {{
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }}
    .prose {{ margin: 1.15rem 0; }}
    .prose p {{ margin: .65rem 0; }}
    .node {{
      margin: 1.2rem 0;
      padding: 1.1rem 1.25rem;
      border-left: 5px solid var(--muted);
      background: var(--surface);
      box-shadow: 0 3px 14px var(--shadow);
    }}
    .node.rule {{ border-color: var(--rule-color); background: var(--rule-bg); }}
    .node.note {{ border-color: var(--note-color); background: var(--note-bg); }}
    .node.example {{ border-color: var(--example-color); background: var(--example-bg); }}
    .node.exercise {{ border-color: var(--exercise-color); background: var(--exercise-bg); }}
    .node.vocab, .node.verb, .node.conjugation {{ border-color: var(--vocab-color); background: var(--vocab-bg); }}
    .node.formula {{ border-color: var(--muted); background: var(--code-bg); text-align: center; font-family: "JetBrains Mono", Consolas, monospace; }}
    .node.solution {{ border-color: var(--solution-color); background: var(--solution-bg); }}
    .node-title {{ display: block; font-weight: 700; margin-bottom: .45rem; }}
    .exercise-title {{ letter-spacing: .005em; }}
    .note .node-title, .example .node-title {{ font-style: italic; }}
    .body-line {{ min-height: 1.65em; }}
    .kv-grid {{ display: grid; grid-template-columns: minmax(7rem, auto) 1fr; gap: .3rem 1rem; margin: 0; }}
    .kv-grid dt {{ font-weight: 700; }}
    .kv-grid dd {{ margin: 0; }}
    .conjugation-table {{ border-collapse: collapse; width: 100%; max-width: 30rem; margin-top: .5rem; }}
    .conjugation-table th, .conjugation-table td {{ border-bottom: 1px solid var(--neutral-line); padding: .35rem .5rem; text-align: left; }}
    .conjugation-table th {{ color: var(--muted); font-weight: 600; }}
    .blank {{ display: inline-block; min-width: 7rem; border-bottom: 2px solid currentColor; height: 1.1em; vertical-align: baseline; }}
    .solution-inline {{ margin-top: 1rem; padding-top: .7rem; border-top: 1px dashed currentColor; }}
    .solution-inline a {{ color: var(--solution-color); font-weight: 700; }}
    .solution-toggle {{
      margin-top: 1rem;
      border-top: 1px dashed currentColor;
      padding-top: .7rem;
    }}
    .solution-toggle summary {{
      cursor: pointer;
      color: var(--solution-color);
      font-weight: 700;
    }}
    .solution-toggle summary:focus-visible {{
      outline: 3px solid var(--solution-color);
      outline-offset: 3px;
    }}
    .solution-toggle .solution-toggle-body {{
      margin-top: .65rem;
      padding: .75rem 1rem;
      background: var(--canvas-bg);
      border-left: 3px solid var(--solution-color);
    }}
    .blank-input {{
      display: inline-block;
      width: 8rem;
      max-width: 100%;
      margin: 0 .2rem;
      padding: .18rem .35rem;
      border: 0;
      border-bottom: 2px solid var(--exercise-color);
      border-radius: 0;
      background: var(--input-bg);
      color: var(--ink);
      font: inherit;
      vertical-align: baseline;
    }}
    .blank-input:focus-visible {{
      outline: 3px solid var(--exercise-color);
      outline-offset: 2px;
      background: var(--control-bg);
    }}
    .translation-source {{
      margin: .7rem 0;
      padding: .8rem 1rem;
      border-left: 3px solid var(--exercise-color);
      background: var(--input-bg);
    }}
    .translation-label {{
      display: block;
      margin-bottom: .4rem;
      font-weight: 700;
      color: var(--muted);
    }}
    .translation-answer {{
      display: block;
      width: 100%;
      min-height: 5rem;
      margin-top: .8rem;
      padding: .65rem .75rem;
      border: 1px solid var(--control-border);
      border-bottom: 3px solid var(--exercise-color);
      background: var(--input-bg);
      color: var(--ink);
      font: inherit;
      line-height: 1.5;
      resize: vertical;
    }}
    .translation-answer:focus-visible {{
      outline: 3px solid var(--exercise-color);
      outline-offset: 2px;
      background: var(--control-bg);
    }}
    .choice-list {{
      display: grid;
      gap: .55rem;
      margin: .8rem 0 0;
      padding: 0;
      border: 0;
    }}
    .choice-option {{
      display: flex;
      align-items: flex-start;
      gap: .55rem;
      padding: .55rem .7rem;
      border: 1px solid var(--control-border-soft);
      background: var(--input-bg);
      cursor: pointer;
    }}
    .choice-option:hover {{
      background: var(--control-bg);
    }}
    .choice-option input {{
      margin-top: .35rem;
      accent-color: var(--exercise-color);
    }}
    .choice-actions {{
      margin-top: .8rem;
    }}
    .choice-check, .choice-reset {{
      padding: .5rem .8rem;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }}
    .choice-check {{
      border: 0;
      border-bottom: 3px solid var(--exercise-color);
      background: var(--exercise-color);
      color: var(--on-accent);
    }}
    .choice-reset {{
      margin-left: .5rem;
      border: 1px solid var(--exercise-color);
      border-bottom: 3px solid var(--exercise-color);
      background: var(--control-bg);
      color: var(--exercise-color);
    }}
    .choice-check:hover, .choice-reset:hover {{
      filter: brightness(.95);
    }}
    .choice-result {{
      min-height: 1.5em;
      margin-top: .6rem;
      font-weight: 700;
    }}
    .choice-option.is-correct {{
      border-color: var(--success-border);
      background: var(--success-bg);
    }}
    .choice-option.is-wrong {{
      border-color: var(--danger-border);
      background: var(--danger-bg);
    }}
    .matching-list {{
      display: grid;
      gap: .6rem;
      margin: .8rem 0 0;
    }}
    .matching-row {{
      display: grid;
      grid-template-columns: minmax(8rem, .8fr) minmax(12rem, 1.2fr);
      align-items: center;
      gap: .8rem;
      padding: .65rem .75rem;
      border: 1px solid var(--control-border-soft);
      background: var(--input-bg);
    }}
    .matching-word {{
      font-weight: 700;
    }}
    .matching-select {{
      width: 100%;
      min-width: 0;
      padding: .45rem .55rem;
      border: 1px solid var(--control-border);
      border-bottom: 3px solid var(--exercise-color);
      background: var(--control-bg);
      color: var(--ink);
      font: inherit;
    }}
    .matching-select:focus-visible {{
      outline: 3px solid var(--exercise-color);
      outline-offset: 2px;
    }}
    .matching-check {{
      margin-top: .8rem;
      padding: .5rem .8rem;
      border: 0;
      border-bottom: 3px solid var(--exercise-color);
      background: var(--exercise-color);
      color: var(--on-accent);
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }}
    .matching-check:hover {{
      filter: brightness(.94);
    }}
    .matching-reset {{
      margin-top: .8rem;
      margin-left: .5rem;
      padding: .5rem .8rem;
      border: 1px solid var(--exercise-color);
      border-bottom: 3px solid var(--exercise-color);
      background: var(--control-bg);
      color: var(--exercise-color);
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }}
    .matching-reset:hover {{
      background: var(--control-bg-hover);
    }}
    .matching-result {{
      min-height: 1.5em;
      margin-top: .6rem;
      font-weight: 700;
    }}
    .matching-feedback {{
      display: block;
      margin-top: .25rem;
      font-size: .92em;
      font-weight: 600;
    }}
    .matching-row.is-correct {{
      border-color: var(--success-border);
      background: var(--success-bg);
    }}
    .matching-row.is-wrong {{
      border-color: var(--danger-border);
      background: var(--danger-bg);
    }}
    .matching-row.is-missing {{
      border-color: var(--warning-border);
      background: var(--warning-bg);
    }}
    .builder-answer {{
      min-height: 3rem;
      margin-top: .7rem;
      padding: .7rem .8rem;
      border: 1px solid var(--control-border);
      border-bottom: 3px solid var(--exercise-color);
      background: var(--input-bg);
    }}
    .builder-answer-label, .builder-tokens-label {{
      display: block;
      margin-top: .75rem;
      color: var(--muted);
      font-weight: 700;
    }}
    .builder-placeholder {{
      color: var(--muted);
      font-style: italic;
    }}
    .builder-answer-token {{
      display: inline-block;
      margin: .12rem .18rem .12rem 0;
      padding: .12rem .35rem;
      border: 1px solid var(--control-border-strong);
      background: var(--control-bg-strong);
      border-radius: .2rem;
      color: var(--ink);
      font: inherit;
      cursor: pointer;
    }}
    .builder-answer-token:hover {{
      background: var(--control-bg-strong-hover);
    }}
    .builder-tokens {{
      display: flex;
      flex-wrap: wrap;
      gap: .45rem;
      margin-top: .5rem;
    }}
    .builder-token {{
      padding: .4rem .65rem;
      border: 1px solid var(--control-border);
      background: var(--control-bg);
      color: var(--ink);
      font: inherit;
      cursor: pointer;
    }}
    .builder-token:hover:not(:disabled) {{
      background: var(--control-bg-hover);
    }}
    .builder-token:disabled {{
      opacity: .45;
      cursor: not-allowed;
    }}
    .builder-check, .builder-reset {{
      margin-top: .8rem;
      padding: .5rem .8rem;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }}
    .builder-check {{
      border: 0;
      border-bottom: 3px solid var(--exercise-color);
      background: var(--exercise-color);
      color: var(--on-accent);
    }}
    .builder-reset {{
      margin-left: .5rem;
      border: 1px solid var(--exercise-color);
      border-bottom: 3px solid var(--exercise-color);
      background: var(--control-bg);
      color: var(--exercise-color);
    }}
    .builder-check:hover, .builder-reset:hover {{
      filter: brightness(.95);
    }}
    .builder-result {{
      min-height: 1.5em;
      margin-top: .6rem;
      font-weight: 700;
    }}
    .builder.is-correct .builder-answer {{
      border-color: var(--success-border);
      background: var(--success-bg);
    }}
    .builder.is-wrong .builder-answer {{
      border-color: var(--danger-border);
      background: var(--danger-bg);
    }}
    .short-answer-special {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: .35rem;
      margin: .7rem 0 .9rem;
    }}
    .short-answer-special-label {{
      margin-right: .25rem;
      color: var(--muted);
      font-size: .92em;
      font-weight: 700;
    }}
    .special-char-button {{
      min-width: 2.2rem;
      padding: .28rem .45rem;
      border: 1px solid var(--control-border);
      border-bottom: 3px solid var(--exercise-color);
      background: var(--control-bg);
      color: var(--ink);
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }}
    .special-char-button:hover {{
      background: var(--control-bg-hover);
    }}
    .short-answer-prompt {{
      margin: .7rem 0;
      font-weight: 600;
    }}
    .short-answer-input {{
      display: block;
      width: 100%;
      max-width: 34rem;
      margin-top: .5rem;
      padding: .65rem .75rem;
      border: 1px solid var(--control-border);
      border-bottom: 3px solid var(--exercise-color);
      background: var(--input-bg);
      color: var(--ink);
      font: inherit;
    }}
    .short-answer-input:focus-visible {{
      outline: 3px solid var(--exercise-color);
      outline-offset: 2px;
      background: var(--control-bg);
    }}
    .short-answer-actions {{
      margin-top: .8rem;
    }}
    .short-answer-check, .short-answer-reset {{
      padding: .5rem .8rem;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }}
    .short-answer-check {{
      border: 0;
      border-bottom: 3px solid var(--exercise-color);
      background: var(--exercise-color);
      color: var(--on-accent);
    }}
    .short-answer-reset {{
      margin-left: .5rem;
      border: 1px solid var(--exercise-color);
      border-bottom: 3px solid var(--exercise-color);
      background: var(--control-bg);
      color: var(--exercise-color);
    }}
    .short-answer-result {{
      min-height: 1.5em;
      margin-top: .6rem;
      font-weight: 700;
    }}
    .short-answer.is-correct .short-answer-input {{
      border-color: var(--success-border);
      background: var(--success-bg);
    }}
    .short-answer.is-wrong .short-answer-input {{
      border-color: var(--danger-border);
      background: var(--danger-bg);
    }}
    .cloze-sentence-label, .cloze-tokens-label {{
      display: block;
      margin-top: .75rem;
      color: var(--muted);
      font-weight: 700;
    }}
    .cloze-sentence {{
      margin-top: .5rem;
      padding: .8rem;
      border: 1px solid var(--control-border-soft);
      background: var(--input-bg);
      line-height: 2.2;
    }}
    .cloze-blank {{
      min-width: 7rem;
      margin: 0 .18rem;
      padding: .12rem .4rem;
      border: 0;
      border-bottom: 3px solid var(--exercise-color);
      background: var(--control-bg);
      color: var(--muted);
      font: inherit;
      font-style: italic;
      cursor: pointer;
      vertical-align: baseline;
    }}
    .cloze-blank.is-filled {{
      color: var(--ink);
      font-style: normal;
      font-weight: 700;
    }}
    .cloze-blank:hover {{
      background: var(--control-bg-hover);
    }}
    .cloze-blank.is-correct {{
      border-bottom-color: var(--success-border);
      background: var(--success-bg-strong);
      color: var(--success-ink);
    }}
    .cloze-blank.is-wrong {{
      border-bottom-color: var(--danger-border);
      background: var(--danger-bg-strong);
      color: var(--danger-ink);
    }}
    .cloze-blank.is-missing {{
      border-bottom-color: var(--warning-border);
      background: var(--warning-bg-strong);
    }}
    .cloze-tokens {{
      display: flex;
      flex-wrap: wrap;
      gap: .45rem;
      margin-top: .5rem;
    }}
    .cloze-token {{
      padding: .4rem .65rem;
      border: 1px solid var(--control-border);
      background: var(--control-bg);
      color: var(--ink);
      font: inherit;
      cursor: pointer;
    }}
    .cloze-token:hover:not(:disabled) {{
      background: var(--control-bg-hover);
    }}
    .cloze-token:disabled {{
      opacity: .45;
      cursor: not-allowed;
    }}
    .cloze-actions {{
      margin-top: .8rem;
    }}
    .cloze-check, .cloze-reset {{
      padding: .5rem .8rem;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }}
    .cloze-check {{
      border: 0;
      border-bottom: 3px solid var(--exercise-color);
      background: var(--exercise-color);
      color: var(--on-accent);
    }}
    .cloze-reset {{
      margin-left: .5rem;
      border: 1px solid var(--exercise-color);
      border-bottom: 3px solid var(--exercise-color);
      background: var(--control-bg);
      color: var(--exercise-color);
    }}
    .cloze-result {{
      min-height: 1.5em;
      margin-top: .6rem;
      font-weight: 700;
    }}
    .true-false-list {{
      display: grid;
      gap: .7rem;
      margin: .8rem 0 0;
    }}
    .true-false-row {{
      display: grid;
      grid-template-columns: 1fr auto;
      gap: .8rem;
      align-items: center;
      padding: .75rem;
      border: 1px solid var(--control-border-soft);
      background: var(--input-bg);
    }}
    .true-false-statement {{
      font-weight: 600;
    }}
    .true-false-controls {{
      display: flex;
      flex-wrap: wrap;
      gap: .4rem;
    }}
    .true-false-option {{
      display: inline-flex;
      align-items: center;
      gap: .35rem;
      padding: .35rem .6rem;
      border: 1px solid var(--control-border);
      background: var(--control-bg);
      color: var(--ink);
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }}
    .true-false-option input {{
      margin: 0;
      accent-color: var(--exercise-color);
    }}
    .true-false-option.is-selected {{
      background: var(--exercise-color);
      color: var(--on-accent);
    }}
    .true-false-option:focus-within {{
      outline: 3px solid var(--exercise-color);
      outline-offset: 2px;
    }}
    .true-false-option:hover {{
      background: var(--control-bg-hover);
      color: var(--ink);
    }}
    .true-false-option.is-selected:hover {{
      background: var(--exercise-color);
      color: var(--on-accent);
    }}
    .true-false-feedback {{
      grid-column: 1 / -1;
      min-height: 1.35em;
      font-size: .92em;
      font-weight: 700;
    }}
    .true-false-row.is-correct {{
      border-color: var(--success-border);
      background: var(--success-bg);
    }}
    .true-false-row.is-wrong {{
      border-color: var(--danger-border);
      background: var(--danger-bg);
    }}
    .true-false-row.is-missing {{
      border-color: var(--warning-border);
      background: var(--warning-bg);
    }}
    .true-false-actions {{
      margin-top: .8rem;
    }}
    .true-false-check, .true-false-reset {{
      padding: .5rem .8rem;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }}
    .true-false-check {{
      border: 0;
      border-bottom: 3px solid var(--exercise-color);
      background: var(--exercise-color);
      color: var(--on-accent);
    }}
    .true-false-reset {{
      margin-left: .5rem;
      border: 1px solid var(--exercise-color);
      border-bottom: 3px solid var(--exercise-color);
      background: var(--control-bg);
      color: var(--exercise-color);
    }}
    .true-false-result {{
      min-height: 1.5em;
      margin-top: .6rem;
      font-weight: 700;
    }}
    .solutions {{ break-before: page; page-break-before: always; margin-top: 3rem; padding-top: 1rem; border-top: 3px solid var(--solution-color); }}
    .page-break-before {{ break-before: page; page-break-before: always; }}
    code {{ font-family: "JetBrains Mono", Consolas, monospace; font-size: .92em; background: var(--code-bg); padding: .1em .3em; border-radius: .2em; }}
    @media print {{
      body {{ background: var(--canvas-bg); }}
      main {{ max-width: none; padding: 0; }}
      .masthead, .node {{ box-shadow: none; }}
      .node, .solutions {{ break-inside: avoid; page-break-inside: avoid; }}
      .skip-link, .toc {{ display: none; }}
      a {{ color: inherit; text-decoration: none; }}
    }}
    /* EduTeX responsive exercise contract */
    @media (max-width: 640px) {{
      .matching-row {{
        grid-template-columns: 1fr;
        gap: .45rem;
      }}
      .true-false-row {{
        grid-template-columns: 1fr;
        gap: .55rem;
      }}
      .true-false-controls {{
        width: 100%;
      }}
      .true-false-choice {{
        flex: 1 1 8rem;
      }}
      .matching-check,
      .matching-reset,
      .builder-check,
      .builder-reset,
      .short-answer-check,
      .short-answer-reset,
      .cloze-check,
      .cloze-reset,
      .true-false-check,
      .true-false-reset {{
        margin-left: 0;
        width: 100%;
      }}
    }}    @media (max-width: 520px) {{ main {{ padding: 1rem .75rem 3rem; }} .masthead {{ padding: 1.5rem 1rem; }} .node {{ padding: .9rem .85rem; }} .kv-grid {{ grid-template-columns: 1fr; gap: .05rem; }} }}
  </style>
</head>
<body>
  <a class="skip-link" href="#content">{html.escape(self._labels["skip"])}</a>
  <main>
    <header class="masthead">
      <h1>{title}</h1>
      {author_html}
    </header>
    {toc_html}
    <article id="content" tabindex="-1" aria-label="{html.escape(self._labels["document_content"])}">
{body}
    </article>
  </main>
  <script>
    (() => {{
      const shuffle = (items) => {{
        const shuffled = items.slice();
        for (let index = shuffled.length - 1; index > 0; index -= 1) {{
          const randomIndex = Math.floor(Math.random() * (index + 1));
          [shuffled[index], shuffled[randomIndex]] =
            [shuffled[randomIndex], shuffled[index]];
        }}
        return shuffled;
      }};

      const randomizeMatchingGroup = (group) => {{
        const selects = Array.from(group.querySelectorAll("select.matching-select"));
        if (!selects.length) return;
        const sourceOptions = Array.from(selects[0].options)
          .filter((option) => option.value);
        const shuffledOptions = shuffle(sourceOptions);
        selects.forEach((select) => {{
          const placeholder = Array.from(select.options)
            .find((option) => !option.value);
          select.replaceChildren();
          if (placeholder) select.appendChild(placeholder.cloneNode(true));
          shuffledOptions.forEach((option) => {{
            select.appendChild(option.cloneNode(true));
          }});
        }});
      }};

      const updateMatchingGroup = (group) => {{
        const selects = Array.from(group.querySelectorAll("select.matching-select"));
        const selectedValues = new Set(
          selects.map((select) => select.value).filter(Boolean)
        );
        selects.forEach((select) => {{
          Array.from(select.options).forEach((option) => {{
            if (!option.value) return;
            option.disabled = selectedValues.has(option.value)
              && option.value !== select.value;
          }});
        }});
      }};

      const resetMatchingGroup = (group) => {{
        group.querySelectorAll("select.matching-select").forEach((select) => {{
          select.value = "";
        }});
        group.querySelectorAll(".matching-row").forEach((row) => {{
          row.classList.remove("is-correct", "is-wrong", "is-missing");
          const feedback = row.querySelector(".matching-feedback");
          if (feedback) feedback.textContent = "";
        }});
        const result = group.querySelector(".matching-result");
        if (result) result.textContent = "";
        updateMatchingGroup(group);
      }};

      const checkMatchingGroup = (group) => {{
        const rows = Array.from(group.querySelectorAll(".matching-row"));
        let correct = 0;
        const selectedValues = new Set();
        rows.forEach((row) => {{
          const select = row.querySelector("select.matching-select");
          const feedback = row.querySelector(".matching-feedback");
          row.classList.remove("is-correct", "is-wrong", "is-missing");
          if (!select.value) {{
            row.classList.add("is-missing");
            feedback.textContent = "{self._labels["matching_missing"]}";
          }} else if (selectedValues.has(select.value)) {{
            row.classList.add("is-wrong");
            feedback.textContent = "{self._labels["matching_duplicate"]}";
          }} else if (select.value === select.dataset.answer) {{
            selectedValues.add(select.value);
            row.classList.add("is-correct");
            feedback.textContent = "{self._labels["matching_correct"]}";
            correct += 1;
          }} else {{
            selectedValues.add(select.value);
            row.classList.add("is-wrong");
            feedback.textContent = "{self._labels["matching_wrong"]}";
          }}
        }});
        const result = group.querySelector(".matching-result");
        result.textContent = `${{correct}} / ${{rows.length}}`;
      }};

      const handleMatchingChange = (group, changedSelect) => {{
        const duplicate = changedSelect.value && Array.from(
          group.querySelectorAll("select.matching-select")
        ).some((select) => select !== changedSelect
          && select.value === changedSelect.value);

        if (duplicate) {{
          changedSelect.value = "";
          const row = changedSelect.closest(".matching-row");
          const feedback = row && row.querySelector(".matching-feedback");
          if (feedback) feedback.textContent = "{self._labels["matching_duplicate"]}";
        }}

        updateMatchingGroup(group);
      }};

      const initializeSpecialCharacters = (exercise) => {{
        const input = exercise.querySelector("input.short-answer-input");
        exercise.querySelectorAll("button.special-char-button").forEach((button) => {{
          button.addEventListener("click", () => {{
            const character = button.dataset.character;
            const start = input.selectionStart ?? input.value.length;
            const end = input.selectionEnd ?? input.value.length;
            input.value = input.value.slice(0, start)
              + character
              + input.value.slice(end);
            const cursor = start + character.length;
            input.focus();
            input.setSelectionRange(cursor, cursor);
            input.dispatchEvent(new Event("input", {{ bubbles: true }}));
          }});
        }});
      }};

      const normalizeShortAnswer = (value) => value
        .trim()
        .replace(/\\s+/g, " ")
        .replace(/[.!?…]+$/, "")
        .trim()
        .toLocaleLowerCase();

      const normalizeChoiceValue = (value) => String(value || "")
        .trim()
        .replace(/\\s+/g, " ")
        .toLocaleLowerCase();

      function sameValues(left, right) {{
        const normalize = (values) => values
          .map(normalizeChoiceValue)
          .filter(Boolean)
          .sort();
        const normalizedLeft = normalize(left);
        const normalizedRight = normalize(right);
        return normalizedLeft.length === normalizedRight.length
          && normalizedLeft.every((value, index) => value === normalizedRight[index]);
      }}

      const initializeChoice = (exercise) => {{
        const inputs = Array.from(exercise.querySelectorAll("input[name]"));
        const result = exercise.querySelector(".choice-result");
        const checkButton = exercise.querySelector("button.choice-check");
        const resetButton = exercise.querySelector("button.choice-reset");
        let expected = [];
        try {{
          expected = JSON.parse(exercise.dataset.answer || "[]");
        }} catch (error) {{
          expected = [];
        }}

        const clearState = () => {{
          exercise.classList.remove("is-correct", "is-wrong");
          inputs.forEach((input) => {{
            input.closest(".choice-option")?.classList.remove("is-correct", "is-wrong");
          }});
          result.textContent = "";
        }};

        inputs.forEach((input) => input.addEventListener("change", clearState));
        checkButton.addEventListener("click", () => {{
          const selected = inputs.filter((input) => input.checked).map((input) => input.value);
          inputs.forEach((input) => {{
            input.closest(".choice-option")?.classList.remove("is-correct", "is-wrong");
          }});
          if (!selected.length) {{
            exercise.classList.remove("is-correct", "is-wrong");
            result.textContent = "{self._labels["choice_missing"]}";
            return;
          }}
          const correct = sameValues(selected, expected);
          exercise.classList.toggle("is-correct", correct);
          exercise.classList.toggle("is-wrong", !correct);
          selected.forEach((value) => {{
            const input = inputs.find((candidate) => candidate.value === value);
            input?.closest(".choice-option")?.classList.add(correct ? "is-correct" : "is-wrong");
          }});
          result.textContent = correct
            ? "{self._labels["choice_correct"]}"
            : "{self._labels["choice_wrong"]}";
        }});

        resetButton.addEventListener("click", () => {{
          inputs.forEach((input) => {{ input.checked = false; }});
          clearState();
          inputs[0]?.focus();
        }});
      }};

      const initializeShortAnswer = (exercise) => {{
        const input = exercise.querySelector("input.short-answer-input");
        const result = exercise.querySelector(".short-answer-result");
        const checkButton = exercise.querySelector("button.short-answer-check");
        const resetButton = exercise.querySelector("button.short-answer-reset");

        checkButton.addEventListener("click", () => {{
          exercise.classList.remove("is-correct", "is-wrong");
          const value = input.value.trim();
          if (!value) {{
            result.textContent = "{self._labels["short_empty"]}";
          }} else if (
            normalizeShortAnswer(value)
            === normalizeShortAnswer(input.dataset.answer)
          ) {{
            exercise.classList.add("is-correct");
            result.textContent = "{self._labels["short_correct"]}";
          }} else {{
            exercise.classList.add("is-wrong");
            result.textContent = "{self._labels["short_wrong"]}";
          }}
        }});

        input.addEventListener("input", () => {{
          exercise.classList.remove("is-correct", "is-wrong");
          result.textContent = "";
        }});

        resetButton.addEventListener("click", () => {{
          input.value = "";
          exercise.classList.remove("is-correct", "is-wrong");
          result.textContent = "";
          input.focus();
        }});
      }};

      const normalizeClozeText = (value) => value
        .trim()
        .replace(/\\s+/g, " ")
        .toLocaleLowerCase();

      const initializeCloze = (exercise) => {{
        const blanks = Array.from(exercise.querySelectorAll("button.cloze-blank"));
        const tokens = Array.from(exercise.querySelectorAll("button.cloze-token"));
        const result = exercise.querySelector(".cloze-result");

        const clearBlankFeedback = () => {{
          blanks.forEach((blank) => {{
            blank.classList.remove("is-correct", "is-wrong", "is-missing");
          }});
        }};

        tokens.forEach((token) => {{
          token.addEventListener("click", () => {{
            const blank = blanks.find((candidate) => !candidate.dataset.tokenIndex);
            if (!blank) return;
            blank.dataset.tokenIndex = token.dataset.tokenIndex;
            blank.dataset.selected = token.dataset.token;
            blank.textContent = token.dataset.token;
            blank.classList.add("is-filled");
            blank.setAttribute("aria-label", `${{token.dataset.token}} — {self._labels["cloze_placeholder"]}`);
            token.disabled = true;
            clearBlankFeedback();
            result.textContent = "";
          }});
        }});

        blanks.forEach((blank) => {{
          blank.addEventListener("click", () => {{
            if (!blank.dataset.tokenIndex) return;
            const token = tokens.find(
              (candidate) => candidate.dataset.tokenIndex === blank.dataset.tokenIndex
            );
            if (token) token.disabled = false;
            delete blank.dataset.tokenIndex;
            delete blank.dataset.selected;
            blank.textContent = blank.dataset.placeholder;
            blank.classList.remove("is-filled", "is-correct", "is-wrong", "is-missing");
            blank.setAttribute("aria-label", blank.dataset.placeholder);
            result.textContent = "";
          }});
        }});

        const checkButton = exercise.querySelector("button.cloze-check");
        checkButton.addEventListener("click", () => {{
          let correct = 0;
          blanks.forEach((blank) => {{
            blank.classList.remove("is-correct", "is-wrong", "is-missing");
            if (!blank.dataset.selected) {{
              blank.classList.add("is-missing");
            }} else if (
              normalizeClozeText(blank.dataset.selected)
              === normalizeClozeText(blank.dataset.answer)
            ) {{
              blank.classList.add("is-correct");
              correct += 1;
            }} else {{
              blank.classList.add("is-wrong");
            }}
          }});
          result.textContent = `${{correct}} / ${{blanks.length}}`;
        }});

        const resetButton = exercise.querySelector("button.cloze-reset");
        resetButton.addEventListener("click", () => {{
          blanks.forEach((blank) => {{
            delete blank.dataset.tokenIndex;
            delete blank.dataset.selected;
            blank.textContent = blank.dataset.placeholder;
            blank.classList.remove("is-filled", "is-correct", "is-wrong", "is-missing");
            blank.setAttribute("aria-label", blank.dataset.placeholder);
          }});
          tokens.forEach((token) => {{ token.disabled = false; }});
          result.textContent = "";
        }});
      }};

      const initializeTrueFalse = (exercise) => {{
        const rows = Array.from(exercise.querySelectorAll(".true-false-row"));
        const result = exercise.querySelector(".true-false-result");

        rows.forEach((row) => {{
          row.querySelectorAll("input.true-false-choice").forEach((input) => {{
            input.addEventListener("change", () => {{
              row.dataset.selected = input.value;
              row.querySelectorAll("label.true-false-option").forEach((option) => {{
                option.classList.toggle("is-selected", option.contains(input));
              }});
              row.classList.remove("is-correct", "is-wrong", "is-missing");
              const feedback = row.querySelector(".true-false-feedback");
              if (feedback) feedback.textContent = "";
              result.textContent = "";
            }});
          }});
        }});

        const checkButton = exercise.querySelector("button.true-false-check");
        checkButton.addEventListener("click", () => {{
          let correct = 0;
          rows.forEach((row) => {{
            const feedback = row.querySelector(".true-false-feedback");
            row.classList.remove("is-correct", "is-wrong", "is-missing");
            if (!row.dataset.selected) {{
              row.classList.add("is-missing");
              feedback.textContent = "{self._labels["tf_missing"]}";
            }} else if (row.dataset.selected === row.dataset.answer) {{
              row.classList.add("is-correct");
              feedback.textContent = "{self._labels["tf_correct"]}";
              correct += 1;
            }} else {{
              row.classList.add("is-wrong");
              feedback.textContent = "{self._labels["tf_wrong"]}";
            }}
          }});
          result.textContent = `${{correct}} / ${{rows.length}}`;
        }});

        const resetButton = exercise.querySelector("button.true-false-reset");
        resetButton.addEventListener("click", () => {{
          rows.forEach((row) => {{
            delete row.dataset.selected;
            row.classList.remove("is-correct", "is-wrong", "is-missing");
            row.querySelectorAll("input.true-false-choice").forEach((input) => {{
              input.checked = false;
            }});
            row.querySelectorAll("label.true-false-option").forEach((option) => {{
              option.classList.remove("is-selected");
            }});
            const feedback = row.querySelector(".true-false-feedback");
            if (feedback) feedback.textContent = "";
          }});
          result.textContent = "";
        }});
      }};

      const normalizeBuilderText = (value) => value
        .trim()
        .replace(/\\s+/g, " ")
        .toLocaleLowerCase();

      const randomizeBuilderTokens = (builder) => {{
        const container = builder.querySelector(".builder-tokens");
        if (!container) return;
        const tokens = shuffle(Array.from(container.querySelectorAll("button.builder-token")));
        tokens.forEach((token) => container.appendChild(token));
      }};

      const initializeBuilder = (builder) => {{
        randomizeBuilderTokens(builder);
        const values = [];
        const selectedTokens = [];
        const answer = builder.querySelector(".builder-answer");
        const result = builder.querySelector(".builder-result");
        const tokens = Array.from(builder.querySelectorAll("button.builder-token"));

        const renderAnswer = () => {{
          answer.replaceChildren();
          if (!values.length) {{
            const placeholder = document.createElement("span");
            placeholder.className = "builder-placeholder";
            placeholder.textContent = builder.dataset.placeholder;
            answer.appendChild(placeholder);
            return;
          }}
          values.forEach((value, index) => {{
            const item = document.createElement("button");
            item.type = "button";
            item.className = "builder-answer-token";
            item.textContent = value;
            item.title = "{self._labels["remove_builder_token"]}";
            item.setAttribute(
              "aria-label",
              `${{value}} — {self._labels["remove_builder_token"]}`
            );
            item.addEventListener("click", () => {{
              const originalToken = selectedTokens[index];
              values.splice(index, 1);
              selectedTokens.splice(index, 1);
              if (originalToken) originalToken.disabled = false;
              builder.classList.remove("is-correct", "is-wrong");
              result.textContent = "";
              renderAnswer();
            }});
            answer.appendChild(item);
          }});
        }};

        tokens.forEach((token) => {{
          token.addEventListener("click", () => {{
            values.push(token.dataset.token);
            selectedTokens.push(token);
            token.disabled = true;
            renderAnswer();
            builder.classList.remove("is-correct", "is-wrong");
            result.textContent = "";
          }});
        }});

        const checkButton = builder.querySelector("button.builder-check");
        checkButton.addEventListener("click", () => {{
          builder.classList.remove("is-correct", "is-wrong");
          if (!values.length) {{
            result.textContent = "{self._labels["builder_empty"]}";
          }} else if (
            normalizeBuilderText(values.join(" "))
            === normalizeBuilderText(builder.dataset.answer)
          ) {{
            builder.classList.add("is-correct");
            result.textContent = "{self._labels["builder_correct"]}";
          }} else {{
            builder.classList.add("is-wrong");
            result.textContent = "{self._labels["builder_wrong"]}";
          }}
        }});

        const resetButton = builder.querySelector("button.builder-reset");
        resetButton.addEventListener("click", () => {{
          values.length = 0;
          selectedTokens.length = 0;
          tokens.forEach((token) => {{ token.disabled = false; }});
          builder.classList.remove("is-correct", "is-wrong");
          result.textContent = "";
          renderAnswer();
        }});

        renderAnswer();
      }};

      document.querySelectorAll(".matching-list").forEach((group) => {{
        group.addEventListener("change", (event) => {{
          if (event.target.matches("select.matching-select")) {{
            handleMatchingChange(group, event.target);
          }}
        }});
        const checkButton = group.parentElement.querySelector("button.matching-check");
        if (checkButton) {{
          checkButton.addEventListener("click", () => checkMatchingGroup(group));
        }}
        const resetButton = group.parentElement.querySelector("button.matching-reset");
        if (resetButton) {{
          resetButton.addEventListener("click", () => resetMatchingGroup(group));
        }}
        randomizeMatchingGroup(group);
        updateMatchingGroup(group);
      }});

      document.querySelectorAll(".short-answer").forEach(initializeSpecialCharacters);
      document.querySelectorAll(".choice-exercise").forEach(initializeChoice);
      document.querySelectorAll(".short-answer").forEach(initializeShortAnswer);
      document.querySelectorAll(".cloze-exercise").forEach(initializeCloze);
      document.querySelectorAll(".true-false-exercise").forEach(initializeTrueFalse);
      document.querySelectorAll(".sentence-builder").forEach(initializeBuilder);
    }})();
  </script>
</body>
</html>
"""

    def _render_prose(self, block: TextBlock) -> str:
        lines: list[str] = []
        for raw_line in block.content.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            match = re.match(r"^(#{1,4})\s+(.*)$", line)
            if match:
                level = min(len(match.group(1)) + 1, 4)
                heading_text = match.group(2).strip()
                heading_id = self._unique_id("section", heading_text)
                self._heading_entries.append((level, heading_id, heading_text))
                lines.append(
                    f'<h{level} id="{heading_id}">{self._inline(heading_text)}</h{level}>'
                )
            else:
                lines.append(f'<p class="prose">{self._inline(line)}</p>')
        return "\n".join(lines)

    def _render_element(self, element: object) -> str:
        node = element.styled_node
        classes = ["node", node.node_type]
        if element.placement.page_break_before:
            classes.append("page-break-before")
        title, body = self._extract_title(node.body)
        label = self._labels.get(node.node_type, node.style.label.strip())

        # Exercises receive a stable visible number from LayoutService.
        # The exercise_id is generated as exercise-1, exercise-2, ...
        if node.node_type == "exercise":
            exercise_id = str(getattr(element, "exercise_id", ""))
            match = re.search(r"(?:^|-)\d+$", exercise_id)
            if match:
                number = match.group(0).lstrip("-")
                label = f"{label} {number}"

        heading = " --- ".join(part for part in (label, title) if part)
        heading_html = ""
        section_id = self._unique_id("node", heading or node.node_type)
        heading_id = self._unique_id("heading", heading or node.node_type)
        labelled_by = heading_id if heading else ""
        if heading:
            self._heading_entries.append((2, heading_id, heading))
            heading_class = "node-title"
            if node.node_type == "exercise":
                heading_class += " exercise-title"
            heading_html = (
                f'<h2 id="{heading_id}" class="{heading_class}">'
                f'{html.escape(heading)}</h2>'
            )

        if node.node_type == "vocab":
            content = self._render_vocab(node)
        elif node.node_type == "verb":
            content = self._render_verb(node)
        elif node.node_type == "conjugation":
            content = self._render_conjugation(node)
        elif node.node_type == "formula":
            content = self._render_formula(node, body)
        elif node.node_type == "example":
            content = self._render_example(node, body)
        else:
            if node.node_type == "exercise":
                exercise_solution_node = next(
                    (
                        child
                        for child in node.children
                        if child.node_type == "solution"
                    ),
                    None,
                )
                exercise_solution_body = (
                    self._extract_title(exercise_solution_node.body)[1]
                    if exercise_solution_node is not None
                    else ""
                )
                if self._is_short_answer_exercise(body):
                    content = self._render_short_answer(
                        body, section_id, exercise_solution_body
                    )
                elif self._is_cloze_exercise(body):
                    content = self._render_cloze_exercise(body, section_id)
                elif self._is_true_false_exercise(body):
                    content = self._render_true_false_exercise(body, section_id)
                elif self._is_sentence_builder_exercise(body):
                    content = self._render_sentence_builder(
                        body, section_id, exercise_solution_body
                    )
                elif self._is_matching_exercise(body):
                    content = self._render_matching_exercise(body, section_id)
                elif self._is_translation_exercise(body):
                    content = self._render_translation_exercise(body, section_id)
                elif self._is_choice_exercise(body):
                    content = self._render_choice_exercise(body, section_id)
                else:
                    content = self._render_exercise_body(body, section_id)
                solution_id = getattr(element, "solution_id", "")
                solution_index = getattr(element, "solution_index", 0)
                if solution_id and solution_index:
                    solution_node = exercise_solution_node
                    if solution_node is not None:
                        solution_body = self._extract_title(solution_node.body)[1]
                        content += (
                            '<details class="solution-toggle">'
                            f'<summary>{html.escape(self._labels["show_solution"])}</summary>'
                            f'<div class="solution-toggle-body">'
                            f'{self._render_body(solution_body)}'
                            f'</div></details>'
                        )
                    content += (
                        '<div class="solution-inline"><a '
                        f'href="#{html.escape(solution_id)}">'
                        f'{html.escape(self._labels["solution"])} '
                        f'{solution_index} — appendice</a></div>'
                    )
            else:
                content = self._render_body(body)

        aria = f' aria-labelledby="{labelled_by}"' if labelled_by else f' aria-label="{html.escape(node.node_type)}"'
        return f'<section id="{section_id}" class="{" ".join(classes)}"{aria}>{heading_html}{content}</section>'

    def _is_short_answer_exercise(self, body: str) -> bool:
        """Return True when an exercise body declares type: short_answer."""
        return any(
            line.strip().lower() in {
                "type: short_answer", "type: short-answer", "type: shortanswer"
            }
            for line in body.splitlines()
        )

    def _render_short_answer(
        self,
        body: str,
        exercise_id: str,
        solution_body: str = "",
    ) -> str:
        """Render a short-answer field with client-side checking."""
        prompt = ""
        expected = ""

        for raw_line in body.splitlines():
            line = raw_line.strip()
            lower = line.lower()
            if lower in {
                "type: short_answer", "type: short-answer", "type: shortanswer"
            }:
                continue
            if lower.startswith("prompt:") or lower.startswith("question:"):
                prompt = line.split(":", 1)[1].strip()
                continue
            if lower.startswith("answer:") or lower.startswith("expected:"):
                expected = line.split(":", 1)[1].strip()

        if not expected and solution_body:
            solution_lines = [line.strip() for line in solution_body.splitlines() if line.strip()]
            expected = solution_lines[0] if solution_lines else ""

        input_id = f"{exercise_id}-short-answer"
        return (
            f'<div class="short-answer" id="{html.escape(exercise_id)}" '
            f'aria-label="{html.escape(self._labels["short_answer"])}">'
            f'<div class="short-answer-special" role="group" '
            f'aria-label="{html.escape(self._labels["special_chars"])}">'
            f'<span class="short-answer-special-label">'
            f'{html.escape(self._labels["special_chars"])}:</span>'
            + "".join(
                f'<button type="button" class="special-char-button" '
                f'data-character="{html.escape(character, quote=True)}" '
                f'aria-label="{html.escape(character)}">{html.escape(character)}</button>'
                for character in ("ä", "ö", "ü", "Ä", "Ö", "Ü", "ß")
            )
            + '</div>'
            f'<div class="short-answer-prompt">{self._inline(prompt)}</div>'
            f'<label class="translation-label" for="{html.escape(input_id)}">'
            f'{html.escape(self._labels["short_prompt"])}:</label>'
            f'<input type="text" class="short-answer-input" '
            f'id="{html.escape(input_id)}" name="{html.escape(input_id)}" '
            f'data-answer="{html.escape(expected, quote=True)}" '
            f'placeholder="{html.escape(self._labels["short_placeholder"], quote=True)}">'
            f'<div class="short-answer-actions">'
            f'<button type="button" class="short-answer-check">'
            f'{html.escape(self._labels["check_short"])}'
            f'</button>'
            f'<button type="button" class="short-answer-reset">'
            f'{html.escape(self._labels["reset_short"])}'
            f'</button>'
            f'<div class="short-answer-result" role="status" aria-live="polite"></div>'
            f'</div></div>'
        )

    def _is_cloze_exercise(self, body: str) -> bool:
        """Return True when an exercise body declares type: cloze."""
        return any(
            line.strip().lower() in {"type: cloze", "type: fill", "type: fill-in"}
            for line in body.splitlines()
        )

    def _render_cloze_exercise(self, body: str, exercise_id: str) -> str:
        """Render a click-to-fill sentence with removable word buttons.

        Supported body syntax::

            type: cloze
            sentence: Ich ______ Luca.
            answers:
            - heiße
        """
        sentence = ""
        answers: list[str] = []
        reading_answers = False

        for raw_line in body.splitlines():
            line = raw_line.strip()
            lower = line.lower()
            if lower in {"type: cloze", "type: fill", "type: fill-in"}:
                continue
            if lower.startswith("sentence:"):
                sentence = line.split(":", 1)[1].strip()
                reading_answers = False
                continue
            if lower == "answers:" or lower.startswith("answers:"):
                reading_answers = True
                inline_value = line.split(":", 1)[1].strip()
                if inline_value:
                    answers.extend(
                        item.strip() for item in inline_value.split("|") if item.strip()
                    )
                continue
            if reading_answers and line:
                answer = re.sub(r"^(?:[-*]\s+|\d+[.)]\s+)", "", line).strip()
                if answer:
                    answers.append(answer)

        parts = re.split(r"_{2,}", sentence)
        blank_count = len(parts) - 1
        if not sentence or blank_count <= 0 or len(answers) < blank_count:
            return (
                f'<div class="body-line"><em>{html.escape(self._labels["cloze_missing"])}</em></div>'
            )

        sentence_markup: list[str] = []
        for index, part in enumerate(parts):
            sentence_markup.append(self._inline(part))
            if index < blank_count:
                placeholder = self._labels["cloze_placeholder"]
                sentence_markup.append(
                    f'<button type="button" class="cloze-blank" '
                    f'data-index="{index}" '
                    f'data-answer="{html.escape(answers[index], quote=True)}" '
                    f'data-placeholder="{html.escape(placeholder, quote=True)}" '
                    f'aria-label="{html.escape(placeholder)}">'
                    f'{html.escape(placeholder)}</button>'
                )

        token_markup = []
        for index, answer in enumerate(answers):
            token_markup.append(
                f'<button type="button" class="cloze-token" '
                f'data-token-index="{index}" data-token="{html.escape(answer, quote=True)}">'
                f'{self._inline(answer)}</button>'
            )

        return (
            f'<div class="cloze-exercise" id="{html.escape(exercise_id)}" '
            f'aria-label="{html.escape(self._labels["cloze"])}">'
            f'<span class="cloze-sentence-label">'
            f'{html.escape(self._labels["cloze_sentence"])}</span>'
            f'<div class="cloze-sentence">' + "".join(sentence_markup) + '</div>'
            f'<span class="cloze-tokens-label">'
            f'{html.escape(self._labels["cloze_tokens"])}</span>'
            f'<div class="cloze-tokens" role="group" '
            f'aria-label="{html.escape(self._labels["cloze_tokens"])}">'
            + chr(10).join(token_markup)
            + '</div>'
            f'<div class="cloze-actions">'
            f'<button type="button" class="cloze-check">'
            f'{html.escape(self._labels["check_cloze"])}'
            f'</button>'
            f'<button type="button" class="cloze-reset">'
            f'{html.escape(self._labels["reset_cloze"])}'
            f'</button>'
            f'<div class="cloze-result" role="status" aria-live="polite"></div>'
            f'</div></div>'
        )

    def _is_true_false_exercise(self, body: str) -> bool:
        """Return True when an exercise body declares type: true_false."""
        return any(
            line.strip().lower() in {"type: true_false", "type: true-false", "type: truefalse"}
            for line in body.splitlines()
        )

    def _render_true_false_exercise(self, body: str, exercise_id: str) -> str:
        """Render ordered statement/answer true-false pairs."""
        pairs: list[tuple[str, str]] = []
        current_statement: str | None = None
        invalid = False

        for raw_line in body.splitlines():
            line = raw_line.strip()
            lower = line.lower()
            if lower in {"type: true_false", "type: true-false", "type: truefalse"}:
                continue
            if lower.startswith("statement:"):
                if current_statement is not None:
                    invalid = True
                current_statement = line.split(":", 1)[1].strip()
                if not current_statement:
                    invalid = True
                continue
            if lower.startswith("answer:"):
                if current_statement is None:
                    invalid = True
                    continue
                answer = line.split(":", 1)[1].strip().lower()
                if answer not in {"true", "false", "vero", "falso"}:
                    invalid = True
                else:
                    normalized = "true" if answer in {"true", "vero"} else "false"
                    pairs.append((current_statement, normalized))
                current_statement = None

        if current_statement is not None:
            invalid = True
        if invalid or not pairs:
            return (
                f'<div class="body-line" role="alert">'
                f'<em>{html.escape(self._labels["tf_invalid"])}</em></div>'
            )

        rows: list[str] = []
        for index, (statement, answer) in enumerate(pairs, start=1):
            row_id = f"{exercise_id}-true-false-{index}"
            statement_id = f"{row_id}-statement"
            true_id = f"{row_id}-true"
            false_id = f"{row_id}-false"
            rows.append(
                f'<div class="true-false-row" id="{html.escape(row_id)}" '
                f'data-answer="{html.escape(answer, quote=True)}" '
                f'aria-labelledby="{html.escape(statement_id)}">'
                f'<span class="true-false-statement" id="{html.escape(statement_id)}">'
                f'{self._inline(statement)}</span>'
                f'<div class="true-false-controls" role="group" '
                f'aria-labelledby="{html.escape(statement_id)}">'
                f'<label class="true-false-option" for="{html.escape(true_id)}">'
                f'<input type="radio" class="true-false-choice" '
                f'id="{html.escape(true_id)}" name="{html.escape(row_id)}" '
                f'value="true">'
                f'<span>{html.escape(self._labels["true"])}</span></label>'
                f'<label class="true-false-option" for="{html.escape(false_id)}">'
                f'<input type="radio" class="true-false-choice" '
                f'id="{html.escape(false_id)}" name="{html.escape(row_id)}" '
                f'value="false">'
                f'<span>{html.escape(self._labels["false"])}</span></label>'
                f'</div>'
                f'<span class="true-false-feedback" aria-live="polite"></span>'
                f'</div>'
            )

        return (
            f'<div class="true-false-exercise" id="{html.escape(exercise_id)}" '
            f'aria-label="{html.escape(self._labels["true_false"])}">'
            f'<div class="true-false-list" role="list">' + chr(10).join(rows) + '</div>'
            f'<div class="true-false-actions">'
            f'<button type="button" class="true-false-check">'
            f'{html.escape(self._labels["check_true_false"])}'
            f'</button>'
            f'<button type="button" class="true-false-reset">'
            f'{html.escape(self._labels["reset_true_false"])}'
            f'</button>'
            f'<div class="true-false-result" role="status" aria-live="polite"></div>'
            f'</div></div>'
        )

    def _is_sentence_builder_exercise(self, body: str) -> bool:
        """Return True when an exercise body declares type: builder."""
        return any(
            line.strip().lower() in {"type: builder", "type: sentence-builder"}
            for line in body.splitlines()
        )

    def _render_sentence_builder(
        self,
        body: str,
        exercise_id: str,
        solution_body: str = "",
    ) -> str:
        """Render clickable tokens for building and checking a sentence.

        Supported body syntax::

            type: builder
            tokens:
            - Ich
            - heiße
            - Luca.

        ``answer:`` may be used in the exercise body. Otherwise the first
        non-empty line of the nested solution is used as the expected answer.
        """
        tokens: list[str] = []
        answer_lines: list[str] = []
        current: list[str] | None = None
        reading_answer = False

        for raw_line in body.splitlines():
            line = raw_line.strip()
            lower = line.lower()
            if lower in {"type: builder", "type: sentence-builder"}:
                continue
            if lower == "tokens:" or lower.startswith("tokens:"):
                current = tokens
                reading_answer = False
                inline_value = line.split(":", 1)[1].strip()
                if inline_value:
                    tokens.extend(
                        item.strip() for item in inline_value.split("|") if item.strip()
                    )
                continue
            if lower.startswith("answer:"):
                current = answer_lines
                reading_answer = True
                value = line.split(":", 1)[1].strip()
                if value:
                    answer_lines.append(value)
                continue
            if reading_answer:
                if line:
                    answer_lines.append(raw_line.strip())
                continue
            if current is None or not line:
                continue
            item = re.sub(r"^(?:[-*]\s+|\d+[.)]\s+)", "", line).strip()
            if item:
                current.append(item)

        expected = " ".join(answer_lines).strip()
        if not expected and solution_body:
            solution_lines = [line.strip() for line in solution_body.splitlines() if line.strip()]
            expected = solution_lines[0] if solution_lines else ""

        rendered_tokens: list[str] = []
        for index, token in enumerate(tokens):
            rendered_tokens.append(
                f'<button type="button" class="builder-token" '
                f'data-token-index="{index}" data-token="{html.escape(token, quote=True)}">'
                f'{self._inline(token)}</button>'
            )

        answer_label = html.escape(self._labels["builder_answer"])
        tokens_label = html.escape(self._labels["builder_tokens"])
        placeholder = html.escape(self._labels["builder_placeholder"], quote=True)
        return (
            f'<div class="sentence-builder" id="{html.escape(exercise_id)}" '
            f'data-answer="{html.escape(expected, quote=True)}" '
            f'data-placeholder="{placeholder}" '
            f'aria-label="{html.escape(self._labels["builder"])}">'
            f'<span class="builder-answer-label">{answer_label}</span>'
            f'<div class="builder-answer" role="status" aria-live="polite"></div>'
            f'<span class="builder-tokens-label">{tokens_label}</span>'
            f'<div class="builder-tokens" role="group" '
            f'aria-label="{tokens_label}">' + chr(10).join(rendered_tokens) + '</div>'
            f'<button type="button" class="builder-check">'
            f'{html.escape(self._labels["check_builder"])}'
            f'</button>'
            f'<button type="button" class="builder-reset">'
            f'{html.escape(self._labels["reset_builder"])}'
            f'</button>'
            f'<div class="builder-result" role="status" aria-live="polite"></div>'
            f'</div>'
        )

    def _is_matching_exercise(self, body: str) -> bool:
        """Return True when an exercise body declares type: matching."""
        return any(
            line.strip().lower() == "type: matching"
            for line in body.splitlines()
        )

    def _render_matching_exercise(self, body: str, exercise_id: str) -> str:
        """Render parallel ``words:`` and ``meanings:`` lists as selectors.

        Supported body syntax::

            type: matching
            words:
            - Hallo
            - Tschuess
            meanings:
            - ciao
            - arrivederci
        """
        words: list[str] = []
        meanings: list[str] = []
        current: list[str] | None = None

        for raw_line in body.splitlines():
            line = raw_line.strip()
            lower = line.lower()

            if lower == "type: matching":
                continue
            if lower == "words:" or lower.startswith("words:"):
                current = words
                inline_value = line.split(":", 1)[1].strip()
                if inline_value:
                    current.extend(
                        item.strip() for item in inline_value.split("|") if item.strip()
                    )
                continue
            if lower == "meanings:" or lower.startswith("meanings:"):
                current = meanings
                inline_value = line.split(":", 1)[1].strip()
                if inline_value:
                    current.extend(
                        item.strip() for item in inline_value.split("|") if item.strip()
                    )
                continue

            if current is None or not line:
                continue

            item = re.sub(r"^(?:[-*]\s+|\d+[.)]\s+)", "", line).strip()
            if item:
                current.append(item)

        pair_count = min(len(words), len(meanings))
        rendered: list[str] = []
        if pair_count == 0:
            rendered.append(
                f'<div class="body-line"><em>{html.escape(self._labels["no_matching_data"])}</em></div>'
            )
            return chr(10).join(rendered)

        options = "".join(
            f'<option value="{html.escape(meaning)}">{self._inline(meaning)}</option>'
            for meaning in meanings
        )
        rows: list[str] = []
        for index, word in enumerate(words[:pair_count], start=1):
            select_id = f"{exercise_id}-matching-{index}"
            rows.append(
                f'<label class="matching-row" for="{html.escape(select_id)}">'
                f'<span class="matching-word">{self._inline(word)}</span>'
                f'<select class="matching-select" id="{html.escape(select_id)}" '
                f'name="{html.escape(select_id)}" '
                f'data-answer="{html.escape(meanings[index - 1], quote=True)}" '
                f'aria-label="{html.escape(self._labels["matching_word"])} '
                f'{html.escape(word)} — {html.escape(self._labels["matching_meaning"])}">'
                f'<option value="" selected>{html.escape(self._labels["choose_meaning"])}</option>'
                f'{options}</select>'
                f'<span class="matching-feedback" aria-live="polite"></span></label>'
            )

        rendered.append(
            f'<div class="matching-list" role="list" '
            f'data-matching-group="{html.escape(exercise_id, quote=True)}" '
            f'aria-label="{html.escape(self._labels["matching"])}">'
            + chr(10).join(rows)
            + "</div>"
            f'<button type="button" class="matching-check">'
            f'{html.escape(self._labels["check_matching"])}'
            f'</button>'
            f'<button type="button" class="matching-reset">'
            f'{html.escape(self._labels["reset_matching"])}'
            f'</button>'
            f'<div class="matching-result" role="status" aria-label="'
            f'{html.escape(self._labels["matching_result"])}"></div>'
        )
        return chr(10).join(rendered)

    def _is_translation_exercise(self, body: str) -> bool:
        """Return True when an exercise body declares type: translation."""
        return any(
            line.strip().lower() == "type: translation"
            for line in body.splitlines()
        )

    def _render_translation_exercise(self, body: str, exercise_id: str) -> str:
        """Render a translation prompt and an accessible multiline answer box.

        Supported body syntax:

            type: translation
            source: Mi chiamo Luca.

        ``prompt:`` is accepted as an alias for ``source:``.
        """
        prompt_lines: list[str] = []
        source_lines: list[str] = []
        in_source = False

        for raw_line in body.splitlines():
            line = raw_line.strip()
            lower = line.lower()

            if lower == "type: translation":
                continue
            if lower.startswith("source:") or lower.startswith("prompt:"):
                source_lines.append(line.split(":", 1)[1].strip())
                in_source = True
                continue
            if in_source and line:
                source_lines.append(raw_line)
                continue
            if line:
                prompt_lines.append(raw_line)

        rendered: list[str] = []
        for line in prompt_lines:
            rendered.append(f'<div class="body-line">{self._inline(line)}</div>')

        source = chr(10).join(source_lines).strip()
        if source:
            rendered.append(
                f'<div class="translation-source">'
                f'<span class="translation-label">'
                f'{html.escape(self._labels["translation_prompt"])}:'
                f'</span>{self._inline(source)}</div>'
            )

        answer_id = f"{exercise_id}-translation"
        rendered.append(
            f'<label class="translation-label" for="{html.escape(answer_id)}">'
            f'{html.escape(self._labels["write_translation"])}:</label>'
            f'<textarea class="translation-answer" '
            f'id="{html.escape(answer_id)}" '
            f'name="{html.escape(answer_id)}" '
            f'aria-label="{html.escape(self._labels["write_translation"])}"></textarea>'
        )
        return chr(10).join(rendered)

    def _is_choice_exercise(self, body: str) -> bool:
        """Return True when an exercise body declares type: choice."""
        return any(
            line.strip().lower() == "type: choice"
            for line in body.splitlines()
        )

    def _render_choice_exercise(self, body: str, exercise_id: str) -> str:
        """Render a checked single- or multiple-choice exercise."""
        question_lines: list[str] = []
        option_lines: list[str] = []
        answers: list[str] = []
        in_options = False
        multiple = False

        for raw_line in body.splitlines():
            line = raw_line.strip()
            lower = line.lower()
            if not line:
                continue
            if lower == "type: choice":
                continue
            if lower == "multiple: true":
                multiple = True
                continue
            if lower == "multiple: false":
                multiple = False
                continue
            if lower == "options:" or lower.startswith("options:"):
                in_options = True
                inline_options = line.split(":", 1)[1].strip()
                if inline_options:
                    option_lines.extend(
                        item.strip() for item in inline_options.split("|") if item.strip()
                    )
                continue
            if lower.startswith("answer:"):
                answers.extend(
                    item.strip()
                    for item in line.split(":", 1)[1].strip().split("|")
                    if item.strip()
                )
                in_options = False
                continue
            if lower.startswith("question:"):
                question = line.split(":", 1)[1].strip()
                if question:
                    question_lines.append(question)
                in_options = False
                continue
            if in_options:
                option = re.sub(
                    r"^(?:[-*]\s+|\[[ xX]\]\s+|\d+[.)]\s+)",
                    "",
                    line,
                ).strip()
                if option:
                    option_lines.append(option)
            else:
                question_lines.append(raw_line.strip())

        rendered = [
            f'<div class="choice-question">{self._inline(line)}</div>'
            for line in question_lines
        ]
        if not option_lines:
            rendered.append(
                '<div class="body-line"><em>Nessuna opzione configurata.</em></div>'
            )
            return "\n".join(rendered)

        expected = answers if multiple else answers[:1]
        answer_json = json.dumps(expected, ensure_ascii=False, separators=(",", ":"))
        input_type = "checkbox" if multiple else "radio"
        name = f"{exercise_id}-choice"
        option_markup: list[str] = []
        for index, option in enumerate(option_lines, start=1):
            input_id = f"{name}-{index}"
            option_markup.append(
                f'<label class="choice-option" for="{html.escape(input_id)}">'
                f'<input type="{input_type}" id="{html.escape(input_id)}" '
                f'name="{html.escape(name)}" value="{html.escape(option, quote=True)}">'
                f'<span>{self._inline(option)}</span></label>'
            )

        legend = self._labels["options"]
        rendered.append(
            f'<div class="choice-exercise" data-choice-exercise '
            f'data-answer="{html.escape(answer_json, quote=True)}" '
            f'data-multiple="{"true" if multiple else "false"}">'
            f'<fieldset class="choice-list">'
            f'<legend class="sr-only">{html.escape(legend)}</legend>'
            + "\n".join(option_markup)
            + '</fieldset>'
            f'<div class="choice-actions">'
            f'<button type="button" class="choice-check">'
            f'{html.escape(self._labels["check_choice"])}</button>'
            f'<button type="button" class="choice-reset">'
            f'{html.escape(self._labels["reset_choice"])}</button>'
            f'<div class="choice-result" role="status" aria-live="polite" '
            f'aria-label="{html.escape(self._labels["choice_result"])}"></div>'
            f'</div></div>'
        )
        return "\n".join(rendered)

    def _render_exercise_body(self, body: str, exercise_id: str) -> str:
        """Render exercise text and turn underscore blanks into text inputs."""
        blank_number = 0
        rendered_lines: list[str] = []

        for line in body.splitlines() or [""]:
            parts = re.split(r"_{2,}", line)
            rendered = [self._inline(parts[0])]

            for part in parts[1:]:
                blank_number += 1
                input_id = f"{exercise_id}-blank-{blank_number}"
                rendered.append(
                    f'<input type="text" class="blank" '
                    f'id="{html.escape(input_id)}" '
                    f'name="{html.escape(input_id)}" '
                    f'aria-label="{html.escape(self._labels["answer"])} '
                    f'{blank_number}">'
                )
                rendered.append(self._inline(part))

            rendered_lines.append(
                f'<div class="body-line">{"".join(rendered)}</div>'
            )

        return chr(10).join(rendered_lines)

    def _render_body(self, body: str) -> str:
        lines = body.splitlines() or [""]
        return "\n".join(f'<div class="body-line">{self._inline(line)}</div>' for line in lines)

    def _render_example(self, node: StyledNode, body: str) -> str:
        """Render simple, comparative, and contextual example shortcodes."""
        lines = [line.strip() for line in body.splitlines() if line.strip()]

        if node.subtype == "comparative":
            rendered: list[str] = []
            for line in lines:
                if line.startswith("+"):
                    rendered.append(
                        f'<div class="body-line example-correct">'
                        f'{self._inline(line[1:].strip())}</div>'
                    )
                elif line.startswith("-"):
                    rendered.append(
                        f'<div class="body-line example-incorrect">'
                        f'{self._inline(line[1:].strip())}</div>'
                    )
                else:
                    rendered.append(
                        f'<div class="body-line">{self._inline(line)}</div>'
                    )
            return "\n".join(rendered)

        if node.subtype == "contextual" and len(lines) >= 2:
            return (
                f'<div class="body-line">{self._inline(lines[0])}</div>\n'
                f'<div class="body-line example-translation">'
                f'<em>{self._inline(" ".join(lines[1:]))}</em></div>'
            )

        return self._render_body(body)

    def _render_formula(self, node: StyledNode, body: str) -> str:
        """Render mathematical and chemical formulas with semantic HTML."""
        escaped = html.escape(body, quote=False)
        if node.subtype == "chem":
            escaped = self._render_chemistry(escaped)
            return (
                f'<div class="body-line formula-display formula-chem" '
                f'role="img" aria-label="{html.escape(self._labels["chemical_formula"])}">'
                f'{escaped}</div>'
            )
        return (
            f'<div class="body-line formula-display" role="math" '
            f'aria-label="{html.escape(self._labels["mathematical_formula"])}">'
            f'<i>{escaped}</i></div>'
        )

    @staticmethod
    def _render_chemistry(escaped: str) -> str:
        """Render common chemical subscripts without interpreting HTML input."""
        escaped = escaped.replace("-&gt;", "&#8594;").replace("->", "&#8594;")
        escaped = re.sub(r"_\{([^{}]+)\}", r"<sub>\1</sub>", escaped)
        return re.sub(r"_([0-9]+)", r"<sub>\1</sub>", escaped)

    def _render_vocab(self, node: StyledNode) -> str:
        data = self._vocab_data(node)

        rows = [
            (self._labels["word"], data.get("word", "")),
            (self._labels["translation"], data.get("translation", "")),
        ]

        if data.get("gender") or data.get("plural"):
            rows.append(
                (
                    self._labels["gender_plural"],
                    f"{data.get('gender', '')}, pl. {data.get('plural', '')}",
                )
            )

        if data.get("example"):
            rows.append(
                (self._labels["example_field"], data["example"])
            )

        return self._kv_table(rows)

    def _vocab_data(self, node: StyledNode) -> dict[str, str]:
        """Read vocabulary data from fields, key/value lines, or pipe rows."""
        keys = ("word", "translation", "gender", "plural", "example")

        # Syntax:
        # ::: vocab Hallo | ciao | ? | ? | Hallo, Luca!
        if node.fields:
            values = list(node.fields) + [""] * len(keys)
            return dict(zip(keys, values[:len(keys)]))

        # Syntax:
        # word: Hallo
        # translation: ciao
        data = self._parse_kv(node.body)
        if data:
            return data

        # Syntax:
        # ::: vocab
        # Hallo | ciao | ? | ? | Hallo, Luca!
        # :::
        for raw_line in node.body.splitlines():
            line = raw_line.strip()

            if "|" not in line:
                continue

            values = [part.strip() for part in line.split("|")]
            values += [""] * len(keys)

            return dict(zip(keys, values[:len(keys)]))

        return {}

    def _render_verb(self, node: StyledNode) -> str:
        data = self._verb_data(node)

        rows = [
            (self._labels["infinitive"], data.get("infinitive", "")),
            (self._labels["meaning"], data.get("meaning", data.get("translation", ""))),
        ]
        grammar = " · ".join(
            value
            for value in (
                data.get("auxiliary", ""),
                data.get("participle", data.get("past-participle", "")),
            )
            if value
        )
        if grammar:
            rows.append((self._labels["grammar"], grammar))
        third_person = data.get("third_person", data.get("3sg", ""))
        if third_person:
            rows.append((self._labels["third_person"], third_person))

        return self._kv_table(rows)

    def _verb_data(self, node: StyledNode) -> dict[str, str]:
        """Read verb data from pipe fields, key/value lines, or pipe rows."""
        keys = (
            "infinitive",
            "meaning",
            "auxiliary",
            "participle",
            "third_person",
        )

        # Inline fields:
        # ::: verb heißen | chiamarsi | haben | geheißen | heißt
        if node.fields:
            values = list(node.fields) + [""] * len(keys)
            return dict(zip(keys, values[:len(keys)]))

        # Key/value body:
        # infinitive: heißen
        # meaning: chiamarsi
        data = self._parse_kv(node.body)
        if data:
            return data

        # Pipe-separated body:
        # heißen | chiamarsi | haben | geheißen | heißt
        for raw_line in node.body.splitlines():
            line = raw_line.strip()
            if "|" not in line:
                continue
            values = [part.strip() for part in line.split("|")]
            values += [""] * len(keys)
            return dict(zip(keys, values[:len(keys)]))

        return {}

    def _render_conjugation(self, node: StyledNode) -> str:
        rows: list[list[str]] = []
        for line in node.body.splitlines():
            parts = [part.strip() for part in line.split("|")]
            if len(parts) >= 2:
                rows.append(parts[:3])
        if not rows:
            data = self._parse_kv(node.body)
            for pronoun in ("io", "tu", "lui/lei", "noi", "voi", "loro"):
                rows.append([pronoun, data.get(pronoun, "---"), ""])
        heading = ""
        if node.fields:
            values = [value for value in node.fields[:2] if value]
            if values:
                heading = f'<p><strong>{html.escape(" --- ".join(values))}</strong></p>'
        table = [
            '<table class="conjugation-table"><caption class="sr-only">'
            + html.escape(self._labels["conjugation"])
            + '</caption><thead><tr><th scope="col">'
            + html.escape(self._labels["subject"])
            + '</th><th scope="col">'
            + html.escape(self._labels["form"])
            + '</th><th scope="col">'
            + html.escape(self._labels["meaning"])
            + '</th></tr></thead><tbody>'
        ]
        table.extend(
            '<tr><td>' + html.escape(row[0]) + '</td><td>' + self._inline(row[1])
            + '</td><td>' + (self._inline(row[2]) if len(row) > 2 else '') + '</td></tr>'
            for row in rows
        )
        table.append('</tbody></table>')
        return heading + "\n".join(table)

    def _render_solution_inline(self, node: StyledNode) -> str:
        return f'<div class="solution-inline"><strong>{self._labels["solution"]}:</strong> {self._inline(node.body.strip())}</div>'

    def _render_solution(self, node: StyledNode, reference=None) -> str:
        if reference is None:
            return (
                f'<div class="node solution">'
                f'<span class="node-title">{self._labels["solution"]}</span>'
                f'{self._render_body(node.body)}</div>'
            )

        heading_id = f"solution-heading-{reference.index}"
        label = f'{self._labels["solution"]} {reference.index}'
        if reference.exercise_title:
            label += " --- " + reference.exercise_title

        solution_body = self._extract_title(node.body)[1]
        return (
            '<div class="node solution">'
            f'<div id="{html.escape(reference.solution_id)}" '
            f'aria-labelledby="{heading_id}">'
            f'<h3 id="{heading_id}" class="node-title">{html.escape(label)}</h3>'
            f'{self._render_body(solution_body)}</div></div>'
        )

    def _extract_title(self, body: str) -> tuple[str, str]:
        lines = body.strip().splitlines()
        if lines and lines[0].startswith("title:"):
            return lines[0][len("title:"):].strip(), "\n".join(lines[1:]).lstrip("\n")
        return "", body.strip()

    def _parse_kv(self, body: str) -> dict[str, str]:
        result: dict[str, str] = {}
        for line in body.splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                result[key.strip()] = value.strip()
        return result

    def _inline(self, text: str) -> str:
        marker = "__EDUTEX_BLANK__"
        text = re.sub(r"_{2,}", marker, text)
        text = html.escape(text, quote=False)
        text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)
        text = re.sub(r"(?<!\w)_([^\s_][^_]*)_(?!\w)", r"<em>\1</em>", text)
        return text.replace(marker, '<span class="blank" aria-label="blank space"></span>')

    def _render_toc(self) -> str:
        if not self._heading_entries:
            return ""

        # Preserve legitimate repeated titles, but remove an accidental duplicate
        # emitted consecutively for the same heading level.
        entries: list[tuple[int, str, str]] = []
        previous_key: tuple[int, str] | None = None
        for level, heading_id, label in self._heading_entries:
            normalized_label = " ".join(label.split()).casefold()
            key = (level, normalized_label)
            if key == previous_key:
                continue
            entries.append((level, heading_id, label))
            previous_key = key

        if not entries:
            return ""

        # Build a small heading tree so the generated navigation reflects the
        # heading hierarchy instead of rendering every entry in one flat list.
        roots: list[dict[str, object]] = []
        stack: list[tuple[int, dict[str, object]]] = []
        for raw_level, heading_id, label in entries:
            level = max(2, min(raw_level, 4))
            while stack and level <= stack[-1][0]:
                stack.pop()
            siblings = roots if not stack else stack[-1][1]["children"]
            node: dict[str, object] = {
                "level": level,
                "id": heading_id,
                "label": label,
                "children": [],
            }
            siblings.append(node)
            stack.append((level, node))

        def render_nodes(nodes: list[dict[str, object]]) -> str:
            parts = ["<ol>"]
            for node in nodes:
                level = int(node["level"])
                heading_id = str(node["id"])
                label = str(node["label"])
                parts.append(
                    f'<li class="toc-level-{level}">'
                    f'<a href="#{html.escape(heading_id, quote=True)}">'
                    f'{html.escape(label)}</a>'
                )
                children = node["children"]
                if children:
                    parts.append(render_nodes(children))
                parts.append("</li>")
            parts.append("</ol>")
            return "".join(parts)

        return (
            '<nav class="toc" aria-labelledby="toc-title">'
            f'<h2 id="toc-title" class="toc-title">{html.escape(self._labels["contents"])}</h2>'
            + render_nodes(roots)
            + "</nav>"
        )
    def _kv_table(self, rows: list[tuple[str, str]]) -> str:
        result = ['<dl class="kv-grid">']

        for key, value in rows:
            result.append(
                f'<dt>{html.escape(key)}</dt>'
                f'<dd>{self._inline(value)}</dd>'
            )

        result.append("</dl>")
        return "".join(result)

    def _unique_id(self, prefix: str, text: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "item"
        base = f"{prefix}-{slug}"
        candidate = base
        index = 2
        while candidate in self._used_ids:
            candidate = f"{base}-{index}"
            index += 1
        self._used_ids.add(candidate)
        return candidate

    def _theme_palette(self, theme: ThemeModel) -> dict[str, str]:
        """Return document-level colors with a light-theme fallback."""
        defaults = {
            "canvas": "#eef1f5",
            "page_bg": "#ffffff",
            "surface": "#ffffff",
            "ink": "#172033",
            "muted": "#536176",
            "link": "#2a4a7f",
            "code_bg": "rgba(23,32,51,.08)",
        }
        palette = getattr(theme, "palette", {}) or {}
        defaults.update({key: value for key, value in palette.items() if key in defaults})
        # Older dark themes used canvas/ink while newer themes may expose page_bg.
        if "canvas" in palette:
            defaults["canvas"] = palette["canvas"]
        if "ink" in palette:
            defaults["ink"] = palette["ink"]
        return defaults

    def _theme_colors(self, theme: ThemeModel) -> dict[str, str]:
        defaults = {
            "page_bg": "#ffffff", "canvas_bg": "#eef1f5",
            "ink": "#172033", "muted": "#536176",
            "rule_color": "#2a4a7f", "rule_bg": "#eef2f9",
            "note_color": "#b45309", "note_bg": "#fefce8",
            "example_color": "#0f766e", "example_bg": "#f0fdfa",
            "exercise_color": "#4338ca", "exercise_bg": "#eef2ff",
            "vocab_color": "#64748b", "vocab_bg": "#f8fafc",
            "solution_color": "#15803d", "solution_bg": "#f0fdf4",
        }
        palette = getattr(theme, "palette", None)
        if palette is None:
            palette = getattr(theme, "colors", None)
        if palette is not None:
            def palette_value(name: str) -> object:
                if isinstance(palette, dict):
                    return palette.get(name)
                return getattr(palette, name, None)

            for palette_key in ("page_bg", "canvas", "canvas_bg", "ink", "muted"):
                palette_value_for_key = palette_value(palette_key)
                if palette_value_for_key:
                    normalized_key = "canvas_bg" if palette_key == "canvas" else palette_key
                    defaults[normalized_key] = str(palette_value_for_key)
        mapping = {
            "rule": ("rule_color", "rule_bg"), "note": ("note_color", "note_bg"),
            "example": ("example_color", "example_bg"), "exercise": ("exercise_color", "exercise_bg"),
            "vocab": ("vocab_color", "vocab_bg"), "solution": ("solution_color", "solution_bg"),
        }
        for node_type, (border_key, background_key) in mapping.items():
            style = theme.styles.get(node_type)
            if style:
                if style.border_color:
                    defaults[border_key] = style.border_color
                if style.background_color:
                    defaults[background_key] = style.background_color
        return defaults
