"""Loopback-only visual editor for EduTeX course manifests."""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import stat
import tempfile
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import yaml

from edutex.course.service import CourseValidation, load_course_manifest

MAX_REQUEST_BYTES = 1_000_000


class StudioError(ValueError):
    """Base error for local authoring operations."""


class StudioConflictError(StudioError):
    """The manifest changed after the editor loaded it."""


class StudioValidationError(StudioError):
    """A proposed manifest failed EduTeX course validation."""

    def __init__(self, report: CourseValidation) -> None:
        self.report = report
        super().__init__("; ".join(report.errors) or "Course manifest is invalid.")


def _resolve_paths(project_root: Path, manifest_path: Path | str = "course.yaml") -> tuple[Path, Path]:
    root = Path(project_root).expanduser().resolve()
    candidate = Path(manifest_path).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise StudioError("The course manifest must be inside the project directory.") from exc
    if not candidate.is_file():
        raise StudioError(f"Course manifest not found: {candidate}")
    return root, candidate


def _etag(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _course_mapping(document: dict[str, Any]) -> dict[str, Any]:
    nested = document.get("course")
    if isinstance(nested, dict):
        return nested
    return document


def load_course_document(
    project_root: Path, manifest_path: Path | str = "course.yaml"
) -> tuple[dict[str, Any], str, CourseValidation]:
    """Return the raw YAML mapping, its content hash, and validation report."""
    root, path = _resolve_paths(project_root, manifest_path)
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise StudioError(f"Could not read course manifest: {exc}") from exc
    if not isinstance(document, dict) or not isinstance(_course_mapping(document), dict):
        raise StudioError("Course manifest must contain a YAML mapping.")
    report = load_course_manifest(path, root)
    return document, _etag(path), report


def save_course_document(
    project_root: Path,
    document: dict[str, Any],
    expected_etag: str,
    manifest_path: Path | str = "course.yaml",
) -> tuple[str, CourseValidation]:
    """Validate and atomically save an edited raw YAML document."""
    root, path = _resolve_paths(project_root, manifest_path)
    if not isinstance(document, dict) or not isinstance(_course_mapping(document), dict):
        raise StudioError("Edited course manifest must be a YAML mapping.")
    if not secrets.compare_digest(_etag(path), str(expected_etag)):
        raise StudioConflictError("The manifest changed on disk. Reload before saving.")

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{path.name}.",
            suffix=".tmp.yaml",
            dir=path.parent,
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            yaml.safe_dump(document, handle, sort_keys=False, allow_unicode=True)
            handle.flush()
            os.fsync(handle.fileno())

        report = load_course_manifest(temp_path, root)
        if not report.valid:
            raise StudioValidationError(report)
        os.chmod(temp_path, stat.S_IMODE(path.stat().st_mode))
        os.replace(temp_path, path)
        temp_path = None
        return _etag(path), load_course_manifest(path, root)
    except StudioError:
        raise
    except (OSError, UnicodeError, yaml.YAMLError, TypeError, ValueError) as exc:
        raise StudioError(f"Could not save course manifest: {exc}") from exc
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass




class StudioLessonValidationError(StudioError):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("Lesson validation failed; no changes were saved.")


_SUPPORTED_EXERCISES = {"choice", "true_false", "cloze", "matching", "short_answer", "translation", "builder"}
_EXERCISE_ALIASES = {"true-false": "true_false", "truefalse": "true_false", "fill": "cloze", "fill-in": "cloze", "sentence-builder": "builder"}
_LIST_KEYS = {"options", "answers", "words", "meanings", "tokens"}
_FIELD_KEYS = {
    "choice": {"title", "type", "multiple", "question", "options", "answer"},
    "true_false": {"title", "type", "statement", "answer"},
    "cloze": {"title", "type", "sentence", "answers"},
    "matching": {"title", "type", "words", "meanings"},
    "short_answer": {"title", "type", "prompt", "question", "response_hint", "answer", "expected"},
    "translation": {"title", "type", "source", "prompt", "answer", "expected"},
    "builder": {"title", "type", "tokens", "answer"},
}


def split_lesson_frontmatter(source: str) -> tuple[str, str]:
    match = re.match(r"\A---[ \t]*\r?\n.*?\r?\n---[ \t]*(?:\r?\n|\Z)", source, re.DOTALL)
    if not match:
        raise StudioError("Lesson must begin with YAML frontmatter delimited by ---.")
    return match.group(0), source[match.end():]


def _line_ending(value: str) -> str:
    match = re.search(r"(?:\r\n|\n|\r)+\Z", value)
    if not match:
        return ""
    ending = match.group(0)
    return "\r\n" if "\r\n" in ending else "\r" if "\r" in ending else "\n"


def _plain_preview(raw: str) -> str:
    # Produce a short, plain-text hint without exposing Markdown syntax.
    visible: list[str] = []
    for original in raw.splitlines():
        line = original.strip()
        if not line or re.match(r"^:::\s*(?:[A-Za-z0-9_.-]+.*)?$", line):
            continue
        if re.match(r"^(?:```|~~~)", line):
            continue
        if re.match(r"^\|?\s*:?-{3,}", line):
            continue
        if "|" in line:
            line = " / ".join(cell.strip() for cell in line.strip("|").split("|"))
        line = re.sub(r"^#{1,6}\s+", "", line)
        line = re.sub(r"^(?:[-*+]\s+|\d+[.)]\s+|>\s*)", "", line)
        line = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1 [immagine]", line)
        line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
        line = re.sub(r"<[^>]*>", "", line)
        line = re.sub(r"[*_~`]+", "", line)
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            visible.append(line)
        if len(visible) == 3:
            break
    preview = " · ".join(visible)
    if len(preview) > 280:
        preview = preview[:277].rsplit(" ", 1)[0] + "..."
    return preview


def _readonly_block(raw: str, prefix: str, label: str = "Contenuto avanzato") -> dict[str, Any]:
    return {
        "kind": "preserved",
        "editable": False,
        "raw": raw,
        "prefix": prefix,
        "display": label,
        "preview": _plain_preview(raw),
    }


def _shortcode_end(lines: list[str], start: int) -> int | None:
    opener = re.compile(r"^\s*:::\s+[A-Za-z0-9_.-]+(?:\s+.*)?(?:\r?\n)?$")
    closer = re.compile(r"^\s*:::\s*(?:\r?\n)?$")
    if not opener.match(lines[start]):
        return None
    depth = 1
    for index in range(start + 1, len(lines)):
        if closer.match(lines[index]):
            depth -= 1
            if depth == 0:
                return index + 1
        elif opener.match(lines[index]):
            depth += 1
    return None


def _decode_scalar(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    try:
        decoded = yaml.safe_load(value)
        if isinstance(decoded, (str, int, float, bool)):
            return str(decoded)
    except yaml.YAMLError:
        pass
    return value


def _parse_exercise(raw: str, prefix: str) -> dict[str, Any] | None:
    lines = raw.splitlines()
    if len(lines) < 3:
        return None
    opening = re.match(r"^\s*:::\s+exercise\s*$", lines[0], re.IGNORECASE)
    if not opening or not re.match(r"^\s*:::\s*$", lines[-1]):
        return None
    interior = lines[1:-1]
    solution: list[str] = []
    body: list[str] = []
    in_solution = False
    depth = 0
    for line in interior:
        if re.match(r"^\s*:::\s+solution\s*$", line, re.IGNORECASE) and not in_solution:
            in_solution = True
            depth = 1
            continue
        if in_solution and re.match(r"^\s*:::\s*$", line):
            depth -= 1
            if depth == 0:
                in_solution = False
                continue
        (solution if in_solution else body).append(line)
    values: dict[str, Any] = {}
    current: str | None = None
    preamble: list[str] = []
    for line in body:
        match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_-]*):(?:\s*(.*))?$", line)
        if match:
            key = match.group(1).lower().replace("-", "_")
            value = _decode_scalar(match.group(2) or "")
            if key in _LIST_KEYS:
                values.setdefault(key, [])
                if value:
                    values[key].extend(item.strip() for item in value.split("|") if item.strip())
            elif key in {"statement", "answer"} and values.get("type") in {"true_false", "true-false", "truefalse"}:
                values.setdefault(key, []).append(value)
            else:
                values[key] = value
            current = key
            continue
        list_match = re.match(r"^\s*(?:[-*]|\d+[.)])\s+(.*)$", line)
        if current in _LIST_KEYS and list_match:
            values.setdefault(current, []).append(_decode_scalar(list_match.group(1)))
        elif current and line[:1].isspace():
            if isinstance(values.get(current), str):
                values[current] += "\n" + line.strip()
            elif current in _LIST_KEYS:
                values.setdefault(current, []).append(line.strip())
            else:
                preamble.append(line)
        elif line.strip():
            preamble.append(line)
    raw_type = str(values.get("type", "")).strip().lower()
    exercise_type = _EXERCISE_ALIASES.get(raw_type, raw_type)
    if exercise_type not in _SUPPORTED_EXERCISES:
        return None
    allowed = _FIELD_KEYS[exercise_type]
    if any(key not in allowed for key in values):
        return None
    data: dict[str, Any] = {"exercise_type": exercise_type}
    for key, value in values.items():
        if key == "type":
            continue
        data[key] = value
    if exercise_type == "true_false":
        statements = values.get("statement", [])
        answers = values.get("answer", [])
        if isinstance(statements, str):
            statements = [statements]
        if isinstance(answers, str):
            answers = [answers]
        data["pairs"] = [
            {"statement": statement, "answer": answer}
            for statement, answer in zip(statements, answers)
        ]
        data.pop("statement", None)
        data.pop("answer", None)
    if exercise_type == "choice" and "multiple" in data:
        data["multiple"] = str(data["multiple"]).lower() == "true"
    data["solution"] = "\n".join(solution).strip()
    data["preamble"] = "\n".join(preamble).strip()
    return {"kind": "exercise", "editable": True, "raw": raw, "prefix": prefix, "dirty": False, "data": data}


def _classify_shortcode(raw: str, prefix: str) -> dict[str, Any]:
    first = raw.splitlines()[0] if raw.splitlines() else ""
    match = re.match(r"^\s*:::\s+([A-Za-z0-9_.-]+)", first)
    if not match:
        return _readonly_block(prefix + raw, prefix, f"Shortcode non supportato: {name}")
    name = match.group(1).lower()
    body = "\n".join(raw.splitlines()[1:-1]).strip()
    if name == "exercise":
        parsed = _parse_exercise(raw, prefix)
        if parsed:
            parsed["raw"] = prefix + raw
            return parsed
        raw_type = re.search(r"(?im)^\s*type:\s*([^\r\n]+)", raw)
        type_name = raw_type.group(1).strip() if raw_type else "tipo non riconosciuto"
        return _readonly_block(prefix + raw, prefix, f"Esercizio non supportato: {type_name}")
    if name in {"note", "rule"}:
        return {"kind": name, "editable": True, "raw": prefix + raw, "prefix": prefix, "dirty": False, "data": {"content": body}}
    if name == "example" or name.startswith("example."):
        subtype = name.split(".", 1)[1] if "." in name else "simple"
        if subtype not in {"simple", "comparative", "contextual"}:
            return _readonly_block(prefix + raw, prefix, f"Variante di esempio non supportata: {name}")
        return {"kind": "example", "editable": True, "raw": prefix + raw, "prefix": prefix, "dirty": False, "data": {"content": body, "subtype": subtype}}
    return _readonly_block(prefix + raw, prefix, f"Shortcode non supportato: {name}")


def parse_lesson_blocks(body: str) -> tuple[list[dict[str, Any]], str]:
    lines = body.splitlines(keepends=True)
    blocks: list[dict[str, Any]] = []
    pending = ""
    index = 0
    while index < len(lines):
        if not lines[index].strip():
            pending += lines[index]
            index += 1
            continue
        prefix = pending
        pending = ""
        start = index
        line = lines[index]
        if re.match(r"^\s*:::\s+", line):
            end = _shortcode_end(lines, index)
            if end is None:
                blocks.append(_readonly_block(prefix + "".join(lines[index:]), prefix, "Blocco non chiuso; mantenuto invariato"))
                return blocks, ""
            raw = "".join(lines[index:end])
            blocks.append(_classify_shortcode(raw, prefix))
            index = end
            continue
        if re.match(r"^\s*(```|~~~)", line):
            fence = re.match(r"^\s*(```|~~~)", line).group(1)
            index += 1
            while index < len(lines) and not re.match(r"^\s*" + re.escape(fence) + r"\s*$", lines[index].rstrip("\r\n")):
                index += 1
            if index < len(lines):
                index += 1
            blocks.append(_readonly_block(prefix + "".join(lines[start:index]), prefix, "Blocco di codice"))
            continue
        heading = re.match(r"^(#{1,6})\s+(.*?)(?:\r?\n)?$", line)
        if heading:
            blocks.append({"kind": "heading", "editable": True, "raw": prefix + line, "prefix": prefix, "dirty": False, "data": {"level": len(heading.group(1)), "text": heading.group(2)}})
            index += 1
            continue
        list_match = re.match(r"^(\s*)([-*+] |\d+[.)] )(.*?)(?:\r?\n)?$", line)
        if list_match and not list_match.group(1):
            ordered = bool(re.match(r"\d", list_match.group(2)))
            items: list[str] = []
            marker = list_match.group(2)
            while index < len(lines):
                item_match = re.match(r"^(\s*)([-*+] |\d+[.)] )(.*?)(?:\r?\n)?$", lines[index])
                if not item_match or item_match.group(1) or bool(re.match(r"\d", item_match.group(2))) != ordered:
                    break
                items.append(item_match.group(3))
                index += 1
            raw = prefix + "".join(lines[start:index])
            blocks.append({"kind": "list", "editable": True, "raw": raw, "prefix": prefix, "dirty": False, "data": {"ordered": ordered, "marker": marker, "items": items}})
            continue
        if line.lstrip().startswith((">", "|", "<")):
            index += 1
            while index < len(lines) and lines[index].strip():
                index += 1
            blocks.append(_readonly_block(prefix + "".join(lines[start:index]), prefix, "Markdown avanzato (tabella, citazione o HTML)"))
            continue
        index += 1
        while index < len(lines) and lines[index].strip() and not re.match(r"^\s*:::\s+|^#{1,6}\s+|^(?:[-*+] |\d+[.)] )", lines[index]):
            index += 1
        raw_content = "".join(lines[start:index])
        content = raw_content.strip("\r\n")
        if re.search(r"(?:[`*_~<>]|\[[^\]]+\]\()", content):
            blocks.append(_readonly_block(prefix + raw_content, prefix, "Testo con formattazione inline avanzata"))
        else:
            blocks.append({"kind": "text", "editable": True, "raw": prefix + raw_content, "prefix": prefix, "dirty": False, "ending": _line_ending(raw_content), "data": {"text": content}})
    return blocks, pending


def _safe_manifest_source(project_root: Path, manifest_path: Path, source: str) -> Path:
    root, manifest = _resolve_paths(project_root, manifest_path)
    document, _, report = load_course_document(root, manifest)
    if not report.valid:
        raise StudioError("The course manifest must be valid before editing its lessons.")
    course = _course_mapping(document)
    linked: set[str] = set()
    for module in course.get("modules", []):
        if not isinstance(module, dict):
            continue
        for lesson in module.get("lessons", []):
            if isinstance(lesson, dict):
                value = lesson.get("source", lesson.get("path"))
                if isinstance(value, str):
                    linked.add(value.replace("\\", "/"))
    normalized = str(source).replace("\\", "/")
    if normalized not in linked:
        raise StudioError("The selected lesson is not linked from this course manifest.")
    candidate = Path(normalized)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise StudioError("Lesson source must be a relative path inside the project.")
    path = (root / candidate).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise StudioError("Lesson source must stay inside the project.") from exc
    if not path.is_file():
        raise StudioError(f"Lesson source not found: {normalized}")
    return path


def load_lesson_document(project_root: Path, manifest_path: Path | str, source: str) -> dict[str, Any]:
    path = _safe_manifest_source(project_root, Path(manifest_path), source)
    try:
        text = path.read_text(encoding="utf-8")
        frontmatter, body = split_lesson_frontmatter(text)
    except (OSError, UnicodeError) as exc:
        raise StudioError(f"Could not read lesson: {exc}") from exc
    blocks, tail = parse_lesson_blocks(body)
    return {"source": source.replace("\\", "/"), "etag": _etag(path), "blocks": blocks, "tail": tail}


def _scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return str(value).replace("\r", " ").replace("\n", " ").strip()


def _list_lines(key: str, value: Any) -> list[str]:
    items = value if isinstance(value, list) else []
    result = [key + ":"]
    result.extend("- " + _scalar(item) for item in items)
    return result


def _serialize_exercise(data: dict[str, Any]) -> str:
    kind = str(data.get("exercise_type", ""))
    if kind not in _SUPPORTED_EXERCISES:
        raise StudioError("Unsupported exercise type.")
    lines = ["::: exercise"]
    title = _scalar(data.get("title"))
    if title:
        lines.append("title: " + title)
    lines.append("type: " + kind)
    preamble = str(data.get("preamble", "")).strip()
    if preamble:
        lines.extend(preamble.splitlines())
    if kind == "choice":
        if "multiple" in data:
            lines.append("multiple: " + ("true" if data.get("multiple") else "false"))
        for key in ("question",):
            if _scalar(data.get(key)):
                lines.append(key + ": " + _scalar(data.get(key)))
        lines.extend(_list_lines("options", data.get("options", [])))
        if _scalar(data.get("answer")):
            lines.append("answer: " + _scalar(data.get("answer")))
    elif kind == "true_false":
        pairs = data.get("pairs", [])
        for pair in pairs if isinstance(pairs, list) else []:
            if not isinstance(pair, dict):
                continue
            lines.append("statement: " + _scalar(pair.get("statement")))
            lines.append("answer: " + _scalar(pair.get("answer")))
    elif kind == "cloze":
        lines.append("sentence: " + _scalar(data.get("sentence")))
        lines.extend(_list_lines("answers", data.get("answers", [])))
    elif kind == "matching":
        lines.extend(_list_lines("words", data.get("words", [])))
        lines.extend(_list_lines("meanings", data.get("meanings", [])))
    elif kind == "short_answer":
        prompt = _scalar(data.get("prompt", data.get("question")))
        if prompt:
            lines.append("prompt: " + prompt)
        for key in ("response_hint",):
            if _scalar(data.get(key)):
                lines.append(key + ": " + _scalar(data.get(key)))
        answer = _scalar(data.get("answer", data.get("expected")))
        if answer:
            lines.append("answer: " + answer)
    elif kind == "translation":
        source = _scalar(data.get("source", data.get("prompt")))
        if source:
            lines.append("source: " + source)
        answer = _scalar(data.get("answer", data.get("expected")))
        if answer:
            lines.append("answer: " + answer)
    elif kind == "builder":
        lines.extend(_list_lines("tokens", data.get("tokens", [])))
        if _scalar(data.get("answer")):
            lines.append("answer: " + _scalar(data.get("answer")))
    solution = str(data.get("solution", "")).strip()
    if solution:
        lines.extend(["", "::: solution", *solution.splitlines(), ":::"])
    lines.append(":::")
    return "\n".join(lines)


def _serialize_block(block: dict[str, Any]) -> str:
    kind = block.get("kind")
    data = block.get("data")
    if not isinstance(data, dict):
        raise StudioError("Invalid lesson block data.")
    prefix = block.get("prefix", "")
    if not isinstance(prefix, str) or prefix.strip():
        raise StudioError("Lesson block separator must contain whitespace only.")
    ending = block.get("ending", "\n")
    if ending not in {"", "\n", "\r\n", "\r"}:
        raise StudioError("Invalid lesson block line ending.")
    if kind == "heading":
        level = int(data.get("level", 2))
        if level < 1 or level > 6:
            raise StudioError("Heading level must be between 1 and 6.")
        content = "#" * level + " " + _scalar(data.get("text"))
    elif kind == "text":
        content = str(data.get("text", "")).replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")
    elif kind == "list":
        items = data.get("items", [])
        if not isinstance(items, list):
            raise StudioError("List items must be a list.")
        ordered = bool(data.get("ordered"))
        content = "\n".join((f"{index}. " if ordered else "- ") + _scalar(item) for index, item in enumerate(items, 1))
    elif kind in {"note", "rule", "example"}:
        name = kind
        if kind == "example":
            subtype = str(data.get("subtype", "simple"))
            if subtype not in {"simple", "comparative", "contextual"}:
                raise StudioError("Unsupported example subtype.")
            name += "." + subtype
        content = "::: " + name + "\n" + str(data.get("content", "")).strip() + "\n:::"
        ending = "\n"
    elif kind == "exercise":
        content = _serialize_exercise(data)
        ending = "\n"
    else:
        raise StudioError("Unsupported editable lesson block.")
    return prefix + content + ending


def compose_lesson_body(blocks: list[dict[str, Any]], tail: str, original_blocks: list[dict[str, Any]]) -> str:
    if not isinstance(blocks, list) or len(blocks) > 500:
        raise StudioError("Lesson must contain no more than 500 content blocks.")
    def counts(values: list[str]) -> dict[str, int]:
        result: dict[str, int] = {}
        for value in values:
            result[value] = result.get(value, 0) + 1
        return result
    original_locked = counts([str(item.get("raw", "")) for item in original_blocks if not item.get("editable")])
    sent_locked = counts([str(item.get("raw", "")) for item in blocks if isinstance(item, dict) and not item.get("editable")])
    if original_locked != sent_locked:
        raise StudioError("Read-only content was changed or removed; reload the lesson before saving.")
    original_editable = counts([str(item.get("raw", "")) for item in original_blocks if item.get("editable")])
    used_unchanged: dict[str, int] = {}
    output: list[str] = []
    for block in blocks:
        if not isinstance(block, dict):
            raise StudioError("Invalid lesson block.")
        if not block.get("editable"):
            output.append(str(block.get("raw", "")))
            continue
        raw = str(block.get("raw", ""))
        if block.get("dirty") is not True and raw:
            used_unchanged[raw] = used_unchanged.get(raw, 0) + 1
            if used_unchanged[raw] > original_editable.get(raw, 0):
                raise StudioError("An unchanged block does not belong to the loaded lesson.")
            output.append(raw)
        else:
            output.append(_serialize_block(block))
    if not isinstance(tail, str) or tail.strip():
        raise StudioError("The final lesson separator must contain whitespace only.")
    if tail != "" and tail not in {"\n", "\n\n", "\r\n", "\r\n\r\n", "\r", "\r\r"}:
        raise StudioError("The final lesson separator was changed; reload before saving.")
    return "".join(output) + tail


def _issue_key(issue: Any) -> str:
    if hasattr(issue, "to_dict"):
        issue = issue.to_dict()
    if isinstance(issue, dict):
        issue = {key: issue[key] for key in ("code", "message", "severity", "field") if key in issue}
    try:
        return json.dumps(issue, ensure_ascii=False, sort_keys=True, default=str)
    except (TypeError, ValueError):
        return str(issue)


def _new_authoring_errors(original: Path, candidate: Path) -> list[str]:
    from edutex.core.cli import validate_authoring
    before = validate_authoring(original)
    after = validate_authoring(candidate)
    old: dict[str, int] = {}
    for issue in before.errors:
        key = _issue_key(issue)
        old[key] = old.get(key, 0) + 1
    added: list[str] = []
    for issue in after.errors:
        key = _issue_key(issue)
        count = old.get(key, 0)
        if count:
            old[key] = count - 1
        else:
            added.append(key)
    return added


def save_lesson_blocks(project_root: Path, manifest_path: Path | str, source: str, etag: str, blocks: list[dict[str, Any]], tail: str) -> tuple[str, list[str]]:
    path = _safe_manifest_source(project_root, Path(manifest_path), source)
    if not secrets.compare_digest(_etag(path), str(etag)):
        raise StudioConflictError("The lesson changed on disk. Reload before saving.")
    try:
        original = path.read_text(encoding="utf-8")
        frontmatter, body = split_lesson_frontmatter(original)
        original_blocks, original_tail = parse_lesson_blocks(body)
        if tail != original_tail:
            raise StudioError("The final lesson separator was changed; reload before saving.")
        new_body = compose_lesson_body(blocks, tail, original_blocks)
        content = frontmatter + new_body
    except (OSError, UnicodeError) as exc:
        raise StudioError(f"Could not prepare lesson save: {exc}") from exc
    if len(content.encode("utf-8")) > MAX_REQUEST_BYTES:
        raise StudioError("Lesson is too large to save through the local Studio.")
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", prefix=f".{path.name}.", suffix=".tmp.md", dir=path.parent, delete=False) as handle:
            temp_path = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        added_errors = _new_authoring_errors(path, temp_path)
        if added_errors:
            raise StudioLessonValidationError(added_errors)
        os.chmod(temp_path, stat.S_IMODE(path.stat().st_mode))
        os.replace(temp_path, path)
        temp_path = None
        return _etag(path), []
    except StudioError:
        raise
    except (OSError, UnicodeError, TypeError, ValueError) as exc:
        raise StudioError(f"Could not save lesson: {exc}") from exc
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.send_header("Referrer-Policy", "no-referrer")
    handler.end_headers()
    handler.wfile.write(body)


def run_author_studio(
    project_root: Path,
    manifest_path: Path | str = "course.yaml",
    *,
    open_browser: bool = True,
) -> None:
    """Serve the course editor on loopback until interrupted by the user."""
    root, manifest = _resolve_paths(project_root, manifest_path)
    token = secrets.token_urlsafe(32)
    studio_html = files("edutex.course").joinpath("studio.html").read_text(encoding="utf-8")

    class StudioHandler(BaseHTTPRequestHandler):
        server_version = "EduTeXStudio/1.0"

        def log_message(self, _format: str, *_args: object) -> None:
            return

        def _host_ok(self) -> bool:
            expected = f"127.0.0.1:{self.server.server_port}"
            return self.headers.get("Host", "") == expected

        def _authorized(self) -> bool:
            return (
                self._host_ok()
                and secrets.compare_digest(
                    self.headers.get("X-EduTeX-Token", ""), token
                )
            )

        def _send_page(self, supplied_token: str) -> None:
            page = studio_html.replace("__EDUTEX_STUDIO_TOKEN__", json.dumps(supplied_token))
            body = page.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; connect-src 'self'; img-src 'self' data:; "
                "style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; "
                "object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
            )
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            parsed = urlsplit(self.path)
            if parsed.path == "/":
                supplied = parse_qs(parsed.query).get("token", [""])[0]
                if not self._host_ok() or not secrets.compare_digest(supplied, token):
                    self.send_error(403, "Invalid local studio token")
                    return
                self._send_page(supplied)
                return
            if parsed.path == "/api/lesson":
                if not self._authorized():
                    self.send_error(403, "Invalid local studio token")
                    return
                source = parse_qs(parsed.query).get("source", [""])[0]
                try:
                    _json_response(self, 200, load_lesson_document(root, manifest, source))
                except (StudioError, TypeError, ValueError) as exc:
                    _json_response(self, 422, {"error": str(exc)})
                return
            if parsed.path != "/api/course" or not self._authorized():
                self.send_error(404 if parsed.path not in {"/api/course", "/api/lesson"} else 403)
                return
            try:
                document, etag, report = load_course_document(root, manifest)
                _json_response(
                    self,
                    200,
                    {
                        "document": document,
                        "course": _course_mapping(document),
                        "etag": etag,
                        "valid": report.valid,
                        "errors": report.errors,
                        "warnings": report.warnings,
                    },
                )
            except (StudioError, TypeError, ValueError) as exc:
                _json_response(self, 422, {"error": str(exc)})

        def do_POST(self) -> None:
            api_path = urlsplit(self.path).path
            if api_path not in {"/api/course", "/api/lesson"}:
                self.send_error(404)
                return
            if not self._authorized():
                self.send_error(403, "Invalid local studio token")
                return
            origin = self.headers.get("Origin")
            expected_origin = f"http://127.0.0.1:{self.server.server_port}"
            if origin and origin != expected_origin:
                self.send_error(403, "Cross-origin requests are not allowed")
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self.send_error(400, "Invalid Content-Length")
                return
            if length < 1 or length > MAX_REQUEST_BYTES:
                self.send_error(413, "Request body is empty or too large")
                return
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(payload, dict):
                    raise StudioError("Request body must be a JSON object.")
                if urlsplit(self.path).path == "/api/lesson":
                    new_etag, warnings = save_lesson_blocks(
                        root,
                        manifest,
                        str(payload.get("source", "")),
                        str(payload.get("etag", "")),
                        payload.get("blocks"),
                        payload.get("tail", ""),
                    )
                    _json_response(self, 200, {"saved": True, "etag": new_etag, "warnings": warnings})
                    return
                new_etag, report = save_course_document(
                    root,
                    payload.get("document"),
                    str(payload.get("etag", "")),
                    manifest,
                )
                _json_response(
                    self,
                    200,
                    {"saved": True, "etag": new_etag, "warnings": report.warnings},
                )
            except StudioConflictError as exc:
                _json_response(self, 409, {"error": str(exc), "reload": True})
            except StudioLessonValidationError as exc:
                _json_response(self, 422, {"error": str(exc), "errors": exc.errors})
            except StudioValidationError as exc:
                _json_response(
                    self,
                    422,
                    {
                        "error": "Course validation failed; no changes were saved.",
                        "errors": exc.report.errors,
                        "diagnostics": [item.to_dict() for item in exc.report.diagnostics],
                    },
                )
            except (StudioError, UnicodeError, json.JSONDecodeError) as exc:
                _json_response(self, 400, {"error": str(exc)})

    server = ThreadingHTTPServer(("127.0.0.1", 0), StudioHandler)
    server.daemon_threads = True
    url = f"http://127.0.0.1:{server.server_port}/?token={token}"
    print(f"EduTeX course studio: {url}")
    print("The editor is available only on this computer. Press Ctrl+C to stop it.")
    if open_browser:
        webbrowser.open_new_tab(url)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        print("\nEduTeX course studio stopped.")
    finally:
        server.server_close()
