"""
EduTeX Shortcode Parser
=======================
Reads a Markdown source file and produces an AST (list of nodes).

Node types
----------
TextNode   – plain Markdown text (passthrough)
ShortcodeNode – a parsed ::: block

AST is returned as a list of dicts for easy serialisation and inspection.
"""

from __future__ import annotations
import re
import json
from dataclasses import dataclass, field, asdict
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

KNOWN_TYPES = {
    "rule", "note", "example", "exercise", "solution",
    "vocab", "verb", "conjugation", "formula",
}

KNOWN_SUBTYPES: dict[str, set[str]] = {
    "example":   {"simple", "comparative", "contextual"},
    "formula":   {"math", "chem"},
    "conjugation": set(),
    "exercise":  set(),
    "solution":  set(),
    "rule":      set(),
    "note":      set(),
    "vocab":     set(),
    "verb":      set(),
}

# Shortcodes that may appear only nested inside another
NESTED_ONLY = {"solution"}

# Shortcodes that may contain nested shortcodes
ALLOWS_NESTING = {"exercise"}


# ---------------------------------------------------------------------------
# AST node dataclasses
# ---------------------------------------------------------------------------

@dataclass
class TextNode:
    kind: str = "text"
    content: str = ""

    def to_dict(self) -> dict:
        return {"kind": self.kind, "content": self.content}


@dataclass
class ShortcodeNode:
    kind: str = "shortcode"
    type: str = ""
    subtype: Optional[str] = None
    fields: list[str] = field(default_factory=list)
    body: str = ""
    children: list = field(default_factory=list)   # nested ShortcodeNodes
    line: int = 0                                   # source line for error reporting

    def to_dict(self) -> dict:
        d: dict = {
            "kind":    self.kind,
            "type":    self.type,
            "subtype": self.subtype,
            "fields":  self.fields,
            "body":    self.body,
        }
        if self.children:
            d["children"] = [c.to_dict() for c in self.children]
        d["line"] = self.line
        return d


# ---------------------------------------------------------------------------
# Parse errors
# ---------------------------------------------------------------------------

class ParseError(Exception):
    def __init__(self, message: str, line: int):
        super().__init__(f"Line {line}: {message}")
        self.line = line


# ---------------------------------------------------------------------------
# Tokeniser
# ---------------------------------------------------------------------------

_OPEN_RE  = re.compile(r"^:::\s*(\S+)(?:\s+(.+))?$")
_CLOSE_RE = re.compile(r"^:::\s*$")


def _parse_open_line(raw: str) -> tuple[str, Optional[str], list[str]]:
    """
    Parse the opening ::: line.
    Returns (type, subtype_or_None, fields_list).
    """
    m = _OPEN_RE.match(raw.strip())
    if not m:
        raise ValueError(f"Cannot parse opening line: {raw!r}")

    type_part = m.group(1).lower()
    rest      = m.group(2) or ""

    # Split type.subtype
    if "." in type_part:
        sc_type, sc_subtype = type_part.split(".", 1)
    else:
        sc_type, sc_subtype = type_part, None

    # Parse pipe-separated fields from the rest of the line
    if rest.strip():
        fields = [f.strip() for f in rest.split("|")]
    else:
        fields = []

    return sc_type, sc_subtype, fields


# ---------------------------------------------------------------------------
# Core parser
# ---------------------------------------------------------------------------

def _parse_block(lines: list[str], start: int, depth: int = 0
                 ) -> tuple[ShortcodeNode, int]:
    """
    Parse one shortcode block starting at `start`.
    Returns (node, index_of_line_after_closing_:::).
    `depth` tracks nesting level (0 = top-level).
    """
    opening = lines[start].strip()
    opening_match = _OPEN_RE.match(opening)
    if opening_match and opening_match.group(1) != opening_match.group(1).lower():
        raise ParseError("Shortcode type and subtype names must be lowercase.", start + 1)
    sc_type, sc_subtype, fields = _parse_open_line(opening)

    # Validate type
    if sc_type not in KNOWN_TYPES:
        raise ParseError(f"Unknown shortcode type: {sc_type!r}", start + 1)

    # Validate subtype
    allowed_subs = KNOWN_SUBTYPES.get(sc_type, set())
    if sc_subtype and sc_subtype not in allowed_subs:
        raise ParseError(
            f"Unknown subtype {sc_subtype!r} for type {sc_type!r}. "
            f"Allowed: {sorted(allowed_subs) or 'none'}",
            start + 1,
        )

    # Validate nesting rules
    if sc_type in NESTED_ONLY and depth == 0:
        raise ParseError(
            f"Shortcode {sc_type!r} may only appear nested inside another shortcode.",
            start + 1,
        )

    node = ShortcodeNode(
        type=sc_type,
        subtype=sc_subtype,
        fields=fields,
        line=start + 1,
    )

    body_lines: list[str] = []
    i = start + 1

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if _CLOSE_RE.match(stripped):
            # Closing ::: for this block
            node.body = "\n".join(body_lines).strip()
            return node, i + 1

        if _OPEN_RE.match(stripped):
            # Nested shortcode opening
            if sc_type not in ALLOWS_NESTING:
                raise ParseError(
                    f"Shortcode {sc_type!r} does not support nested shortcodes.",
                    i + 1,
                )
            child, i = _parse_block(lines, i, depth=depth + 1)
            if sc_type != "exercise" or child.type != "solution":
                raise ParseError(
                    "Only a solution shortcode may be nested inside an exercise.",
                    child.line,
                )
            node.children.append(child)
            continue

        body_lines.append(line)
        i += 1

    raise ParseError(
        f"Unclosed shortcode {sc_type!r} opened at line {start + 1}.",
        start + 1,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse(source: str) -> list[dict]:
    """
    Parse an EduTeX Markdown source string.

    Returns a list of AST node dicts:
      - {"kind": "text",      "content": "..."}
      - {"kind": "shortcode", "type": "...", "subtype": ..., "fields": [...],
         "body": "...", "children": [...], "line": N}
    """
    lines = source.splitlines()
    ast: list[dict] = []
    pending_text: list[str] = []
    i = 0

    def flush_text():
        nonlocal pending_text
        block = "\n".join(pending_text).strip()
        if block:
            ast.append(TextNode(content=block).to_dict())
        pending_text = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if _OPEN_RE.match(stripped):
            flush_text()
            node, i = _parse_block(lines, i, depth=0)
            ast.append(node.to_dict())
        else:
            pending_text.append(line)
            i += 1

    flush_text()
    return ast


def parse_file(path: str) -> list[dict]:
    """Convenience wrapper: read a file and parse it."""
    with open(path, encoding="utf-8") as f:
        return parse(f.read())


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python parser.py <file.md> [--pretty]")
        sys.exit(1)

    path   = sys.argv[1]
    pretty = "--pretty" in sys.argv

    try:
        ast = parse_file(path)
        indent = 2 if pretty else None
        print(json.dumps(ast, ensure_ascii=False, indent=indent))
    except ParseError as e:
        print(f"Parse error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)
