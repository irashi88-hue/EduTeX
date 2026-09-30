"""
EduTeX LaTeX Renderer
Component: Build System (MECH-BUILD-001)

Converts a DocumentStructure into a LaTeX source string.
Each content node type is rendered by a dedicated method.
Rendering is pure string transformation --- no I/O.

Responsibilities:
  - Render each DocumentElement into LaTeX markup.
  - Escape all user content for LaTeX safety.
  - Convert Markdown inline markup to LaTeX commands.
  - Render the appendix (solutions).
  - Produce the final LaTeX source string.
"""

from __future__ import annotations

import re

from edutex.knowledge.models import TextBlock
from edutex.layout.models import DocumentStructure
from edutex.theme.models import StyledNode, ThemeModel


# ---------------------------------------------------------------------------
# LaTeX escaping
# ---------------------------------------------------------------------------

_LATEX_SPECIAL = {
    "&":  r"\&",
    "%":  r"\%",
    "$":  r"\$",
    "#":  r"\#",
    "_":  r"\_",
    "{":  r"\{",
    "}":  r"\}",
    "~":  r"\textasciitilde{}",
    "^":  r"\textasciicircum{}",
    "\\": r"\textbackslash{}",
}

# Em-dash (U+2014) → LaTeX ---
_UNICODE_REPLACEMENTS = {
    "\u2014": "---",   # em-dash
    "\u2013": "--",    # en-dash
    "\u2018": "`",     # left single quote
    "\u2019": "'",     # right single quote
    "\u201C": "``",    # left double quote
    "\u201D": "''",    # right double quote
    "\u00A0": "~",     # non-breaking space
}


def latex_escape(text: str) -> str:
    """Escape a string for safe inclusion in LaTeX source."""
    # First replace unicode typographic chars
    for char, replacement in _UNICODE_REPLACEMENTS.items():
        text = text.replace(char, replacement)
    return "".join(_LATEX_SPECIAL.get(c, c) for c in text)


def _language_code(value: object) -> str:
    return str(value or "en").lower().replace("_", "-").split("-", 1)[0]


def _is_cjk_language(value: object) -> bool:
    return _language_code(value) in {"ja", "zh", "ko"}


def hex_to_latex_color(hex_color: str) -> str:
    """Convert a #RRGGBB hex color to a 6-char uppercase hex string for xcolor."""
    return hex_color.lstrip("#").upper()


# ---------------------------------------------------------------------------
# Markdown inline → LaTeX
# ---------------------------------------------------------------------------

def md_and_escape(text: str) -> str:
    """
    Convert Markdown inline markup to LaTeX, then escape LaTeX special chars.

    Order:
      0a. Replace fill-in-the-blank patterns (2+ underscores) with a placeholder.
      1.  Replace Unicode typographic characters.
      2.  Escape LaTeX special chars EXCEPT * and _ (needed as MD markers).
      3.  Apply Markdown inline conversions (**bold**, *italic*, `code`).
      4.  Escape any remaining _ not consumed by MD markers.
      0b. Restore placeholders as \\underline{\\hspace{1.5cm}}.
    """
    # Step 0a: protect fill-in-the-blank blanks (2+ underscores) from escaping
    text = re.sub(r'_{2,}', 'XBLANKX', text)

    # Step 1: unicode typographic replacements
    for char, replacement in _UNICODE_REPLACEMENTS.items():
        text = text.replace(char, replacement)

    # Step 2: escape LaTeX specials except MD marker chars (* _)
    SAFE = {k: v for k, v in _LATEX_SPECIAL.items() if k not in ('*', '_')}
    text = ''.join(SAFE.get(c, c) for c in text)

    # Step 3: Markdown inline conversions
    # Bold (**text**)
    text = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', text)
    # Italic (*text*) — single markers only
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\\textit{\1}', text)
    # Inline code (`text`)
    text = re.sub(r'`(.+?)`', r'\\texttt{\1}', text)
    # Italic _text_ — only when surrounded by word boundaries
    text = re.sub(r'(?<!\w)_([^\s_][^_]*)_(?!\w)', r'\\textit{\1}', text)

    # Step 4: escape remaining bare _ -> \_
    text = re.sub(r'(?<!\\)_', r'\\_', text)

    # Step 0b: restore fill-in-the-blank as LaTeX underline blank
    text = text.replace('XBLANKX', r'\underline{\hspace{1.5cm}}')

    return text


# ---------------------------------------------------------------------------
# Node renderers
# ---------------------------------------------------------------------------

class LatexRenderer:
    """
    Renders a DocumentStructure to a LaTeX source string.
    """

    def render(self, doc: DocumentStructure, meta: object, theme: ThemeModel) -> str:
        """
        Produce the complete LaTeX source for the document.

        Args:
            doc:   The DocumentStructure from Layout (LAYOUT-001).
            meta:  The KnowledgeModelMeta from Knowledge (KNOW-002).
            theme: The ThemeModel from Theme (THEME-002).

        Returns:
            A complete LaTeX source string.
        """
        self._table_labels = (
            ("Subject", "Form", "Meaning")
            if str(getattr(meta, "language", "en")).lower().split("-", 1)[0] == "en"
            else ("Persona", "Forma", "Significato")
        )
        body_parts: list[str] = []

        # Merge elements and prose blocks in position order
        all_items: list[tuple[int, object]] = []
        for el in doc.elements:
            all_items.append((el.position_index, el.styled_node))
        for pos, block in doc.prose_blocks:
            all_items.append((pos, block))
        all_items.sort(key=lambda x: x[0])

        for _, item in all_items:
            if isinstance(item, TextBlock):
                body_parts.append(self._render_prose(item))
            elif isinstance(item, StyledNode):
                body_parts.append(self._render_node(item))

        body = "\n\n".join(p for p in body_parts if p.strip())

        # Appendix
        appendix_parts: list[str] = []
        for node in doc.appendix_nodes:
            appendix_parts.append(self._render_solution_appendix(node))

        return self._render_document(
            meta=meta,
            theme=theme,
            layout=doc.layout_model,
            body=body,
            appendix_nodes_latex=appendix_parts,
            appendix_title=("Soluzioni" if doc.layout_model.appendix.title == "Solutions" and _language_code(getattr(meta, "language", "en")) in {"it", "de"} else ("解答" if doc.layout_model.appendix.title == "Solutions" and _language_code(getattr(meta, "language", "en")) == "ja" else doc.layout_model.appendix.title)),
        )

    # ------------------------------------------------------------------
    # Document wrapper
    # ------------------------------------------------------------------

    def _render_document(
        self, meta, theme, layout, body: str,
        appendix_nodes_latex: list[str], appendix_title: str
    ) -> str:
        rule_bc  = hex_to_latex_color(theme.styles["rule"].border_color)
        rule_bg  = hex_to_latex_color(theme.styles["rule"].background_color)
        note_bc  = hex_to_latex_color(theme.styles["note"].border_color)
        note_bg  = hex_to_latex_color(theme.styles["note"].background_color)
        ex_bc    = hex_to_latex_color(theme.styles["example"].border_color)
        ex_bg    = hex_to_latex_color(theme.styles["example"].background_color)
        exer_bc  = hex_to_latex_color(theme.styles["exercise"].border_color)
        exer_bg  = hex_to_latex_color(theme.styles["exercise"].background_color)
        vocab_bc = hex_to_latex_color(theme.styles.get("vocab", theme.styles["note"]).border_color)
        vocab_bg = hex_to_latex_color(theme.styles.get("vocab", theme.styles["note"]).background_color)

        palette = {"page_bg": "#ffffff", "ink": "#172033", "link": "#2a4a7f", **getattr(theme, "palette", {})}
        page_bg_hex = palette["page_bg"].lstrip("#").upper()
        ink_hex = palette["ink"].lstrip("#").upper()
        link_hex = palette["link"].lstrip("#").upper()

        appendix_tex = ""
        if appendix_nodes_latex and layout.appendix.enabled:
            appendix_tex = (
                "\\newpage\n"
                f"\\section*{{{latex_escape(appendix_title)}}}\n\n"
                + "\n\n".join(appendix_nodes_latex)
            )

        title_tex  = latex_escape(meta.title)
        author_tex = latex_escape(meta.author)

        language_code = str(getattr(meta, "language", "en") or "en").lower().replace("_", "-").split("-", 1)[0]
        requires_cjk = (
            language_code in {"ja", "zh", "ko"}
            or bool(re.search(
                r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uac00-\ud7af]",
                body,
            ))
            or any(
                bool(re.search(
                    r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uac00-\ud7af]",
                    part,
                ))
                for part in appendix_nodes_latex
            )
        )
        unicode_packages = (
            "\\usepackage{fontspec}\n\\usepackage{xeCJK}\n\\setCJKmainfont{Source Han Sans JP}"
            if requires_cjk
            else "\\usepackage[utf8]{inputenc}\n\\usepackage[T1]{fontenc}"
        )

        return f"""\\documentclass[12pt,a4paper]{{article}}

%% Packages
{unicode_packages}
\\usepackage[top={layout.page.margin_top_mm}mm,bottom={layout.page.margin_bottom_mm}mm,left={layout.page.margin_left_mm}mm,right={layout.page.margin_right_mm}mm]{{geometry}}
\\usepackage{{xcolor}}
\\usepackage{{mdframed}}
\\usepackage{{booktabs}}
\\usepackage{{array}}
\\usepackage{{parskip}}
\\usepackage{{amsmath}}
\\usepackage[version=4]{{mhchem}}
\\usepackage{{hyperref}}
\n%% Document palette
\\definecolor{{PageBackground}}{{HTML}}{{{page_bg_hex}}}
\\definecolor{{DocumentInk}}{{HTML}}{{{ink_hex}}}
\\definecolor{{DocumentLink}}{{HTML}}{{{link_hex}}}

%% Colours
\\definecolor{{rulecolor}}{{HTML}}{{{rule_bc}}}
\\definecolor{{rulebg}}{{HTML}}{{{rule_bg}}}
\\definecolor{{notecolor}}{{HTML}}{{{note_bc}}}
\\definecolor{{notebg}}{{HTML}}{{{note_bg}}}
\\definecolor{{examplecolor}}{{HTML}}{{{ex_bc}}}
\\definecolor{{examplebg}}{{HTML}}{{{ex_bg}}}
\\definecolor{{exercisecolor}}{{HTML}}{{{exer_bc}}}
\\definecolor{{exercisebg}}{{HTML}}{{{exer_bg}}}
\\definecolor{{vocabcolor}}{{HTML}}{{{vocab_bc}}}
\\definecolor{{vocabbg}}{{HTML}}{{{vocab_bg}}}

%% Environments (mdframed default framemethod, no TikZ required)
\\newmdenv[linecolor=rulecolor,linewidth=2pt,topline=false,bottomline=false,rightline=false,backgroundcolor=rulebg,innerleftmargin=10pt,innerrightmargin=10pt,innertopmargin=8pt,innerbottommargin=8pt,skipabove=6pt,skipbelow=6pt]{{rulebox}}
\\newmdenv[linecolor=notecolor,linewidth=2pt,topline=false,bottomline=false,rightline=false,backgroundcolor=notebg,innerleftmargin=10pt,innerrightmargin=10pt,innertopmargin=8pt,innerbottommargin=8pt,skipabove=6pt,skipbelow=6pt]{{notebox}}
\\newmdenv[linecolor=examplecolor,linewidth=2pt,topline=false,bottomline=false,rightline=false,backgroundcolor=examplebg,innerleftmargin=10pt,innerrightmargin=10pt,innertopmargin=8pt,innerbottommargin=8pt,skipabove=6pt,skipbelow=6pt]{{examplebox}}
\\newmdenv[linecolor=exercisecolor,linewidth=2pt,topline=false,bottomline=false,rightline=false,backgroundcolor=exercisebg,innerleftmargin=10pt,innerrightmargin=10pt,innertopmargin=8pt,innerbottommargin=8pt,skipabove=6pt,skipbelow=6pt]{{exercisebox}}
\\newmdenv[linecolor=vocabcolor,linewidth=1pt,topline=true,bottomline=true,rightline=true,backgroundcolor=vocabbg,innerleftmargin=10pt,innerrightmargin=10pt,innertopmargin=8pt,innerbottommargin=8pt,skipabove=6pt,skipbelow=6pt]{{vocabbox}}

%% Metadata
\\title{{{title_tex}}}
\\author{{{author_tex}}}
\\date{{}}
\n\\pagecolor{{PageBackground}}
\\color{{DocumentInk}}
\\hypersetup{{colorlinks=true,linkcolor=DocumentLink,urlcolor=DocumentLink}}

\\begin{{document}}
\\maketitle

{body}

{appendix_tex}
\\end{{document}}
"""

    # ------------------------------------------------------------------
    # Node renderers
    # ------------------------------------------------------------------

    def _render_node(self, node: StyledNode) -> str:
        dispatch = {
            "rule":        self._render_rule,
            "note":        self._render_note,
            "example":     self._render_example,
            "exercise":    self._render_exercise,
            "vocab":       self._render_vocab,
            "verb":        self._render_verb,
            "conjugation": self._render_conjugation,
            "formula":     self._render_formula,
        }
        renderer = dispatch.get(node.node_type, self._render_generic)
        return renderer(node)

    def _render_prose(self, block: TextBlock) -> str:
        """Render plain prose: convert MD headings to LaTeX sections, inline MD to commands."""
        lines = []
        for line in block.content.splitlines():
            # Convert Markdown headings
            m = re.match(r'^(#{1,4})\s+(.*)', line)
            if m:
                level = len(m.group(1))
                heading_text = md_and_escape(m.group(2))
                if level == 1:
                    lines.append(f"\\section*{{{heading_text}}}")
                elif level == 2:
                    lines.append(f"\\section*{{{heading_text}}}")
                elif level == 3:
                    lines.append(f"\\subsubsection*{{{heading_text}}}")
                else:
                    lines.append(f"\\paragraph{{{heading_text}}}")
            else:
                lines.append(md_and_escape(line))
        return "\n".join(lines).strip()

    def _render_rule(self, node: StyledNode) -> str:
        label = latex_escape(node.style.label)
        title, body = self._extract_title(node.body)
        if title:
            label = f"{label} --- {latex_escape(title)}"
        body_tex = self._render_body_lines(body)
        return (
            f"\\begin{{rulebox}}\n"
            f"\\textbf{{{label}}}\\\\\n"
            f"{body_tex}\n"
            f"\\end{{rulebox}}"
        )

    def _render_note(self, node: StyledNode) -> str:
        label = latex_escape(node.style.label)
        title, body = self._extract_title(node.body)
        if title:
            label = f"{label} --- {latex_escape(title)}"
        body_tex = self._render_body_lines(body)
        return (
            f"\\begin{{notebox}}\n"
            f"\\textit{{{label}}}\\\\\n"
            f"{body_tex}\n"
            f"\\end{{notebox}}"
        )

    def _render_example(self, node: StyledNode) -> str:
        label = latex_escape(node.style.label)
        title, body_raw = self._extract_title(node.body)
        if title:
            label = f"{label} --- {latex_escape(title)}"
        body = body_raw.strip()
        if node.subtype == "comparative":
            lines = []
            for line in body.splitlines():
                line = line.strip()
                if line.startswith("+"):
                    lines.append(f"\\textcolor{{green!60!black}}{{{md_and_escape(line[1:].strip())}}} $\\checkmark$")
                elif line.startswith("-"):
                    lines.append(f"\\textcolor{{red!70!black}}{{{md_and_escape(line[1:].strip())}}} $\\times$")
                else:
                    lines.append(md_and_escape(line))
            body_tex = "\\\\\n".join(lines)
        else:
            body_tex = self._render_body_lines(body)
        return (
            f"\\begin{{examplebox}}\n"
            f"\\textit{{{label}}}\\\\\n"
            f"{body_tex}\n"
            f"\\end{{examplebox}}"
        )

    def _render_exercise(self, node: StyledNode) -> str:
        label = latex_escape(node.style.label)
        title, body = self._extract_title(node.body)
        if title:
            label = f"{label} --- {latex_escape(title)}"
        body_tex = self._render_body_lines(body)
        # Solutions are collected by Layout and rendered only in the appendix.
        return (
            f"\\begin{{exercisebox}}\n"
            f"\\textbf{{{label}}}\\\\\n"
            f"{body_tex}\n"
            f"\\end{{exercisebox}}"
        )

    def _render_vocab(self, node: StyledNode) -> str:
        data = self._vocab_data(node)
        word = latex_escape(data.get("word", ""))
        translation = latex_escape(data.get("translation", ""))
        gender = latex_escape(data.get("gender", ""))
        plural = latex_escape(data.get("plural", ""))
        example = md_and_escape(data.get("example", ""))

        gender_plural = f"({gender}, pl. {plural})" if gender or plural else ""
        rows = f"\\textbf{{{word}}} & {translation} \\\\\n"
        if gender_plural:
            rows += f"\\textit{{{latex_escape(gender_plural)}}} & \\textit{{{example}}} \\\\\n"
        elif example:
            rows += f" & \\textit{{{example}}} \\\\\n"

        return (
            f"\\begin{{vocabbox}}\n"
            f"\\begin{{tabular}}{{@{{}}ll@{{}}}}\n"
            f"{rows}"
            f"\\end{{tabular}}\n"
            f"\\end{{vocabbox}}"
        )

    @staticmethod
    def _vocab_data(node: StyledNode) -> dict[str, str]:
        """Read vocabulary data from fields, key/value lines, or pipe rows."""
        keys = ("word", "translation", "gender", "plural", "example")
        if node.fields:
            values = list(node.fields) + [""] * len(keys)
            return dict(zip(keys, values))

        data = LatexRenderer._parse_kv_body(node.body)
        if data:
            return data

        for raw_line in node.body.splitlines():
            line = raw_line.strip()
            if "|" in line:
                values = [part.strip() for part in line.split("|")]
                values += [""] * len(keys)
                return dict(zip(keys, values))
        return {}

    def _render_verb(self, node: StyledNode) -> str:
        """Render a verb with its infinitive visibly emphasized."""
        data = self._verb_data(node)
        infinitive = latex_escape(data.get("infinitive", ""))
        translation = latex_escape(data.get("translation", data.get("meaning", "")))
        rows = [f"\\textbf{{{infinitive}}} & {translation} \\\\n"]
        grammar = " · ".join(
            value
            for value in (
                data.get("auxiliary", ""),
                data.get("past-participle", data.get("participle", "")),
            )
            if value
        )
        if grammar:
            rows.append(f"\\textit{{{latex_escape(grammar)}}} & \\\\n")
        third_person = data.get("3sg", data.get("third_person", ""))
        if third_person:
            rows.append(f"\\textit{{3sg}} & {latex_escape(third_person)} \\\\n")
        return (
            "\\begin{vocabbox}\n"
            "\\begin{tabular}{@{}ll@{}}\n"
            + "".join(rows)
            + "\\end{tabular}\n\\end{vocabbox}"
        )

    @staticmethod
    def _verb_data(node: StyledNode) -> dict[str, str]:
        keys = ("infinitive", "translation", "auxiliary", "past-participle", "3sg")
        if node.fields:
            values = list(node.fields) + [""] * len(keys)
            return dict(zip(keys, values[:len(keys)]))
        data = LatexRenderer._parse_kv_body(node.body)
        if data:
            return data
        for raw_line in node.body.splitlines():
            if "|" in raw_line:
                values = [value.strip() for value in raw_line.split("|")]
                values += [""] * len(keys)
                return dict(zip(keys, values[:len(keys)]))
        return {}

    def _render_conjugation(self, node: StyledNode) -> str:
        infinitive = latex_escape(node.fields[0].strip()) if node.fields else ""
        translation = latex_escape(node.fields[1].strip()) if len(node.fields) > 1 else ""
        rows = ""
        pipe_rows: list[list[str]] = []
        for raw_line in node.body.splitlines():
            parts = [part.strip() for part in raw_line.split("|")]
            if len(parts) >= 2:
                pipe_rows.append(parts)

        if pipe_rows:
            for parts in pipe_rows:
                pronoun = latex_escape(parts[0])
                form = latex_escape(parts[1])
                meaning = latex_escape(parts[2]) if len(parts) > 2 else ""
                rows += (
                    f"\\textit{{{pronoun}}} & {form} & {meaning} "
                    + r"\\" + "\n"
                )
        else:
            data = self._parse_kv_body(node.body)
            for pronoun in ["io", "tu", "lui/lei", "noi", "voi", "loro"]:
                form = latex_escape(data.get(pronoun, "---"))
                rows += (
                    f"\\textit{{{latex_escape(pronoun)}}} & {form} & "
                    + r"\\" + "\n"
                )

        header = ""
        if infinitive:
            header = (
                f"\\textbf{{{infinitive}}}"
                + (f" --- {translation}" if translation else "")
                + "\\par\n"
            )

        table_header = (
            f"\\textbf{{{self._table_labels[0]}}} & "
            f"\\textbf{{{self._table_labels[1]}}} & "
            f"\\textbf{{{self._table_labels[2]}}} "
            + r"\\" + "\n"
        )

        return (
            f"\\begin{{vocabbox}}\n"
            f"{header}"
            f"\\begin{{tabular}}{{@{{}}lll@{{}}}}\n"
            f"\\toprule\n"
            f"{table_header}"
            f"\\midrule\n"
            f"{rows}"
            f"\\bottomrule\n"
            f"\\end{{tabular}}\n"
            f"\\end{{vocabbox}}"
        )

    def _render_formula(self, node: StyledNode) -> str:
        body = node.body.strip()
        if node.subtype == "chem":
            return f"\\[\n\\ce{{{latex_escape(body)}}}\n\\]"
        else:
            return f"\\[\n{body}\n\\]"

    def _render_generic(self, node: StyledNode) -> str:
        body_tex = self._render_body_lines(node.body)
        return f"% [{node.node_type}]\n{body_tex}"

    def _render_solution_appendix(self, node: StyledNode) -> str:
        body_tex = self._render_body_lines(node.body)
        return f"\\textit{{Soluzione:}} {body_tex}\n"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_title(body: str) -> tuple[str, str]:
        """
        If the first line of a shortcode body is 'title: <text>',
        extract and return (title, remaining_body).
        Otherwise return ('', body).
        """
        lines = body.strip().splitlines()
        if lines and lines[0].startswith("title:"):
            title = lines[0][len("title:"):].strip()
            rest = "\n".join(lines[1:]).lstrip("\n")
            return title, rest
        return "", body.strip()

    @staticmethod
    def _render_body_lines(body: str) -> str:
        """Apply md_and_escape to each line of a body string."""
        return "\n".join(md_and_escape(line) for line in body.splitlines())

    @staticmethod
    def _parse_kv_body(body: str) -> dict[str, str]:
        """Parse a key: value body into a dict."""
        result = {}
        for line in body.splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                result[key.strip()] = value.strip()
        return result
