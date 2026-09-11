"""Run EduTeX's local quality baseline without network access."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence


CHECK_NAMES = (
    "Q001 Python syntax",
    "Q002 pytest suite",
    "Q003 CLI lint JSON",
    "Q004 build lint preflight",
    "Q005 CLI contract",
    "Q006 Course management contract",
    "Q007 PDF/LaTeX accessibility contract",
)


@dataclass(frozen=True)
class CheckResult:
    """Result of one quality check."""

    name: str
    passed: bool
    returncode: int = 0
    detail: str = ""


CompletedProcessRunner = Callable[
    [Sequence[str], Path], subprocess.CompletedProcess[str]
]


def project_root() -> Path:
    """Return the repository root based on this file's location."""
    return Path(__file__).resolve().parents[1]


def check_names() -> tuple[str, ...]:
    """Return the stable ordered names of all quality checks."""
    return CHECK_NAMES


def _python_env(root: Path) -> dict[str, str]:
    """Build an environment that imports the checkout under test."""
    environment = os.environ.copy()
    source_dir = str(root / "src")
    existing = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = (
        source_dir + os.pathsep + existing if existing else source_dir
    )
    return environment


def run_subprocess(
    command: Sequence[str],
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run one command with captured, decoded output."""
    return subprocess.run(
        list(command),
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _output(result: subprocess.CompletedProcess[str]) -> str:
    """Combine command output for diagnostics."""
    return "\n".join(
        part.strip()
        for part in (result.stdout or "", result.stderr or "")
        if part and part.strip()
    )


def run_command(
    name: str,
    command: Sequence[str],
    root: Path,
    *,
    validator: Callable[[subprocess.CompletedProcess[str]], str | None] | None = None,
    runner: CompletedProcessRunner | None = None,
) -> CheckResult:
    """Run and validate one external command.

    ``runner`` is injectable so the command behavior can be tested without
    launching subprocesses.
    """
    process_runner = runner or (lambda args, cwd: run_subprocess(args, cwd, env=_python_env(root)))
    result = process_runner(command, root)
    detail = _output(result)
    if result.returncode != 0:
        return CheckResult(name, False, result.returncode, detail)
    if validator is not None:
        validation_error = validator(result)
        if validation_error:
            return CheckResult(name, False, result.returncode, validation_error)
    return CheckResult(name, True, result.returncode, detail)


def _check_python_syntax(root: Path) -> CheckResult:
    """Compile project Python sources in memory, without creating pyc files."""
    files = sorted(
        path
        for directory in (root / "src", root / "tests", root / "tools")
        if directory.exists()
        for path in directory.rglob("*.py")
        if "__pycache__" not in path.parts
    )
    for path in files:
        try:
            source = path.read_bytes()
            compile(source, str(path), "exec")
        except (OSError, SyntaxError, UnicodeError) as exc:
            return CheckResult("Q001 Python syntax", False, 1, f"{path}: {exc}")
    return CheckResult("Q001 Python syntax", True, detail=f"{len(files)} files compiled")


def _check_pytest(root: Path) -> CheckResult:
    """Run the project's configured pytest suite."""
    return run_command(
        "Q002 pytest suite",
        (sys.executable, "-m", "pytest", "-q"),
        root,
    )


def _run_module(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run ``python -m edutex`` against the current checkout."""
    return run_subprocess(
        (sys.executable, "-m", "edutex", *arguments),
        root,
        env=_python_env(root),
    )


def _write_lesson(path: Path, body: str) -> None:
    """Write a minimal source file suitable for lint-only checks."""
    path.write_text(
        "---\n"
        "id: quality-check\n"
        "title: Quality check\n"
        "language: en\n"
        "level: A1\n"
        "version: 1.0.0\n"
        "author: EduTeX\n"
        "---\n\n"
        + body,
        encoding="utf-8",
    )


def _check_lint_json(root: Path) -> CheckResult:
    """Verify valid and invalid standalone lint invocations."""
    with tempfile.TemporaryDirectory(prefix="edutex-quality-lint-") as temporary:
        directory = Path(temporary)
        valid = directory / "valid.md"
        invalid = directory / "invalid.md"
        _write_lesson(valid, "::: formula.math\nE = mc^2\n:::\n")
        _write_lesson(invalid, "::: formula.math\n:::\n")

        valid_result = _run_module(root, "lint", str(valid))
        if valid_result.returncode != 0:
            return CheckResult("Q003 CLI lint JSON", False, valid_result.returncode, _output(valid_result))

        invalid_result = _run_module(root, "lint", str(invalid), "--format", "json")
        if invalid_result.returncode == 0:
            return CheckResult("Q003 CLI lint JSON", False, 1, "invalid source returned exit code 0")
        try:
            payload = json.loads(invalid_result.stdout)
        except json.JSONDecodeError as exc:
            return CheckResult("Q003 CLI lint JSON", False, 1, f"invalid JSON output: {exc}")
        if payload.get("valid") is not False:
            return CheckResult("Q003 CLI lint JSON", False, 1, "JSON report is not invalid")
        errors = payload.get("errors", [])
        if not errors or errors[0].get("code") != "SC101":
            return CheckResult("Q003 CLI lint JSON", False, 1, "expected first error code SC101")
    return CheckResult("Q003 CLI lint JSON", True, detail="text and JSON lint paths passed")


def _init_project(root: Path, directory: Path) -> subprocess.CompletedProcess[str]:
    """Create a temporary project using the public init command."""
    return _run_module(root, "init", str(directory), "--theme", "default", "--language", "en")


def _replace_model(project: Path, body: str) -> None:
    """Replace the template Knowledge Model while preserving its frontmatter."""
    model = project / "assets" / "knowledge_models" / "example.md"
    original = model.read_text(encoding="utf-8")
    frontmatter, _, _ = original.partition("---\n\n")
    model.write_text(frontmatter + "---\n\n" + body, encoding="utf-8")


def _check_build_preflight(root: Path) -> CheckResult:
    """Verify blocking errors, non-blocking warnings, and normal build."""
    with tempfile.TemporaryDirectory(prefix="edutex-quality-build-") as temporary:
        directory = Path(temporary)
        error_project = directory / "error-project"
        initialized = _init_project(root, error_project)
        if initialized.returncode != 0:
            return CheckResult("Q004 build lint preflight", False, initialized.returncode, _output(initialized))
        _replace_model(error_project, "::: formula.math\n:::\n")
        blocked = _run_module(root, "build", "--project", str(error_project), "--lint")
        blocked_output = _output(blocked)
        if blocked.returncode == 0 or "Build blocked: shortcode lint found errors." not in blocked_output:
            return CheckResult("Q004 build lint preflight", False, blocked.returncode or 1, blocked_output)
        if (error_project / "output" / "document.html").exists():
            return CheckResult("Q004 build lint preflight", False, 1, "blocked build produced output")

        warning_project = directory / "warning-project"
        initialized = _init_project(root, warning_project)
        if initialized.returncode != 0:
            return CheckResult("Q004 build lint preflight", False, initialized.returncode, _output(initialized))
        _replace_model(warning_project, "::: exercise\nWrite a sentence.\n:::\n")
        warning_build = _run_module(root, "build", "--project", str(warning_project), "--lint")
        if warning_build.returncode != 0 or not (warning_project / "output" / "document.html").exists():
            return CheckResult("Q004 build lint preflight", False, warning_build.returncode or 1, _output(warning_build))

        normal_project = directory / "normal-project"
        initialized = _init_project(root, normal_project)
        if initialized.returncode != 0:
            return CheckResult("Q004 build lint preflight", False, initialized.returncode, _output(initialized))
        normal_build = _run_module(root, "build", "--project", str(normal_project))
        if normal_build.returncode != 0 or not (normal_project / "output" / "document.html").exists():
            return CheckResult("Q004 build lint preflight", False, normal_build.returncode or 1, _output(normal_build))
    return CheckResult("Q004 build lint preflight", True, detail="blocking, warning, and normal build paths passed")


def _check_cli_contract(root: Path) -> CheckResult:
    """Verify public command names and the options introduced in 0.3.0."""
    checks = (
        (("--help",), ("init", "lint", "build", "validate")),
        (("init", "--help"), ("--theme", "--language")),
        (("lint", "--help"), ("--format",)),
        (("build", "--help"), ("--lint",)),
        (("validate", "--help"), ("--project", "--config")),
    )
    failures: list[str] = []
    for arguments, expected in checks:
        result = _run_module(root, *arguments)
        output = _output(result)
        if result.returncode != 0:
            failures.append(f"{' '.join(arguments)} exited {result.returncode}: {output}")
            continue
        missing = [marker for marker in expected if marker not in output]
        if missing:
            failures.append(f"{' '.join(arguments)} missing: {', '.join(missing)}")
    if failures:
        return CheckResult("Q005 CLI contract", False, 1, "\n".join(failures))
    return CheckResult("Q005 CLI contract", True, detail="public commands and options present")


def _write_course_project(root: Path, directory: Path) -> None:
    """Create a minimal valid course project for the quality contract."""
    lessons = directory / "lessons"
    lessons.mkdir(parents=True, exist_ok=True)
    assets = root / "assets"
    if assets.is_dir():
        shutil.copytree(assets, directory / "assets")
    (directory / "edutex.config.yaml").write_text(
        "edutex:\n"
        "  version: \"0.5.0\"\n"
        "knowledge:\n"
        "  model: \"assets/knowledge_models/example.md\"\n"
        "theme:\n"
        "  name: \"default\"\n"
        "layout:\n"
        "  name: \"default\"\n"
        "build:\n"
        "  output_format: \"html\"\n"
        "  output_dir: \"output\"\n"
        "  output_file: \"document\"\n"
        "extensions:\n"
        "  enabled: []\n"
        "logging:\n"
        "  level: \"INFO\"\n",
        encoding="utf-8",
    )
    (lessons / "hello.md").write_text(
        "---\n"
        "id: hello\n"
        "title: Hello\n"
        "language: en\n"
        "level: A1\n"
        "version: 1.0.0\n"
        "author: EduTeX\n"
        "---\n\n"
        "# Hello\n\nWelcome.\n",
        encoding="utf-8",
    )
    (directory / "course.yaml").write_text(
        "id: quality-course\n"
        "title: Quality Course\n"
        "language: en\n"
        "level: A1\n"
        "version: 1.0.0\n"
        "presentation:\n"
        "  theme: forest\n"
        "  show_contents: false\n"
        "modules:\n"
        "  - id: module-01\n"
        "    title: Getting started\n"
        "    lessons:\n"
        "      - id: lesson-01\n"
        "        title: Hello\n"
        "        source: lessons/hello.md\n"
        "        duration_minutes: 15\n",
        encoding="utf-8",
    )


def _check_course_management(root: Path) -> CheckResult:
    """Verify course validation and all available course output paths."""
    with tempfile.TemporaryDirectory(prefix="edutex-quality-course-") as temporary:
        directory = Path(temporary)
        _write_course_project(root, directory)

        validated = _run_module(root, "course", "validate", "--project", str(directory), "--format", "json")
        if validated.returncode != 0:
            return CheckResult("Q006 Course management contract", False, validated.returncode, _output(validated))
        try:
            payload = json.loads(validated.stdout)
        except json.JSONDecodeError as exc:
            return CheckResult("Q006 Course management contract", False, 1, f"invalid validation JSON: {exc}")
        course = payload.get("course") or {}
        if payload.get("valid") is not True or course.get("theme") != "forest" or course.get("lessons") != 1:
            return CheckResult("Q006 Course management contract", False, 1, "course validation contract mismatch")

        html = _run_module(root, "course", "build", "--project", str(directory), "--format", "html")
        if html.returncode != 0:
            return CheckResult("Q006 Course management contract", False, html.returncode, _output(html))
        index = directory / "output" / "course.html"
        lesson = directory / "output" / "lessons" / "lesson-01.html"
        if not index.is_file() or not lesson.is_file():
            return CheckResult("Q006 Course management contract", False, 1, "HTML course artifacts missing")
        html_source = index.read_text(encoding="utf-8")
        if 'edutex-course-theme" content="forest"' not in html_source:
            return CheckResult("Q006 Course management contract", False, 1, "forest theme marker missing")
        if '<nav class="contents"' in html_source:
            return CheckResult("Q006 Course management contract", False, 1, "disabled contents block rendered")

        latex = _run_module(root, "course", "build", "--project", str(directory), "--format", "latex")
        if latex.returncode != 0 or not (directory / "output" / "course.tex").is_file():
            return CheckResult("Q006 Course management contract", False, latex.returncode or 1, _output(latex))

        compiler_available = shutil.which("latexmk") or shutil.which("pdflatex")
        if compiler_available:
            pdf = _run_module(root, "course", "build", "--project", str(directory), "--format", "pdf")
            if pdf.returncode != 0 or not (directory / "output" / "course.pdf").is_file():
                return CheckResult("Q006 Course management contract", False, pdf.returncode or 1, _output(pdf))
            pdf_detail = "; PDF passed"
        else:
            pdf_detail = "; PDF skipped (latex compiler unavailable)"
    return CheckResult("Q006 Course management contract", True, detail="JSON, HTML, LaTeX passed" + pdf_detail)



def _available_course_pdf_compiler(language: str) -> str | None:
    """Return the first compiler supported by the course PDF runtime."""
    language_code = language.lower().split("-", 1)[0]
    if language_code in {"ja", "zh", "ko"}:
        if shutil.which("latexmk") and shutil.which("xelatex"):
            return "latexmk-xelatex"
        if shutil.which("xelatex"):
            return "xelatex"
        return None
    if shutil.which("latexmk"):
        return "latexmk-pdf"
    if shutil.which("pdflatex"):
        return "pdflatex"
    return None


def pdf_tool_status() -> dict[str, bool]:
    """Return availability of PDF compilation and inspection tools."""
    return {
        "latexmk": shutil.which("latexmk") is not None,
        "pdflatex": shutil.which("pdflatex") is not None,
        "xelatex": shutil.which("xelatex") is not None,
        "qpdf": shutil.which("qpdf") is not None,
        "pdftotext": shutil.which("pdftotext") is not None,
        "pdfinfo": shutil.which("pdfinfo") is not None,
        "pdftoppm": shutil.which("pdftoppm") is not None,
    }


def pdf_runtime_summary(language: str = "en") -> dict[str, object]:
    """Summarize the selected compiler and optional PDF inspection gates."""
    tools = pdf_tool_status()
    return {
        "language": language,
        "compiler": _available_course_pdf_compiler(language),
        "tools": tools,
        "compiled_pdf_checks": any(
            tools[name] for name in ("qpdf", "pdftotext", "pdfinfo", "pdftoppm")
        ),
    }


def _normalize_tool_version(tool: str, output: str) -> str | None:
    """Normalize a tool version without trusting wrapper preamble lines."""
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        return None
    if tool != "latexmk":
        return lines[0]

    # On Windows, the latexmk wrapper may print Perl/MiKTeX initialization
    # text before the semantic line, for example:
    # ``Latexmk: This is Latexmk, John Collins, 4.85.``
    patterns = (
        r"\blatexmk\b.*?\b(?:version|is)\b[^0-9]*([0-9]+(?:\.[0-9]+){1,3})",
        r"\blatexmk\b.*?,\s*(?:john\s+collins,?\s*)?([0-9]+(?:\.[0-9]+){1,3})",
        r"\blatexmk\b[^0-9]*([0-9]+(?:\.[0-9]+){1,3})",
    )
    for line in lines:
        for pattern in patterns:
            match = re.search(pattern, line, flags=re.IGNORECASE)
            if match:
                return f"latexmk version {match.group(1)}"
    return lines[0]


def _tool_version(tool: str) -> str | None:
    """Return a compact, normalized version string for an executable."""
    executable = shutil.which(tool)
    if not executable:
        return None
    version_argument = "-v" if tool in {"pdfinfo", "pdftoppm", "pdftotext"} else "--version"
    try:
        result = subprocess.run(
            (executable, version_argument),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return _normalize_tool_version(tool, _output(result))


def _pypdf_available() -> bool:
    """Return whether the optional pypdf parser is importable."""
    return importlib.util.find_spec("pypdf") is not None


def _tool_record(tool: str, role: str, *, version: bool = True) -> dict[str, object]:
    """Return one JSON-safe diagnostic record for a PDF tool."""
    executable = shutil.which(tool)
    record: dict[str, object] = {
        "available": executable is not None,
        "executable": executable,
        "role": role,
    }
    if version and executable is not None:
        record["version"] = _tool_version(tool)
    return record


def pdf_runtime_report(language: str = "en") -> dict[str, object]:
    """Return a detailed, JSON-safe report of the PDF runtime environment."""
    language_code = language.lower().split("-", 1)[0]
    compiler = _available_course_pdf_compiler(language)
    compiler_tools = ("xelatex",) if language_code in {"ja", "zh", "ko"} else ("latexmk", "pdflatex")
    tools = {
        "latexmk": _tool_record("latexmk", "compiler").copy(),
        "pdflatex": _tool_record("pdflatex", "compiler").copy(),
        "xelatex": _tool_record("xelatex", "cjk-compiler").copy(),
        "qpdf": _tool_record("qpdf", "structural-validator").copy(),
        "pdftotext": _tool_record("pdftotext", "text-extractor").copy(),
        "pdfinfo": _tool_record("pdfinfo", "metadata-inspector").copy(),
        "pdftoppm": _tool_record("pdftoppm", "page-renderer").copy(),
    }
    compiler_ready = compiler is not None
    inspection_names = ("qpdf", "pdftotext", "pdfinfo", "pdftoppm")
    inspection_available = any(
        bool(tools[name]["available"])
        for name in inspection_names
    ) or _pypdf_available()
    inspection_gates = {
        name: {
            "available": bool(tools[name]["available"]),
            "role": tools[name]["role"],
            "status": "available" if bool(tools[name]["available"]) else "unavailable_optional",
        }
        for name in inspection_names
    }
    pypdf_available = _pypdf_available()
    inspection_gates["pypdf"] = {
        "available": pypdf_available,
        "role": "parser",
        "status": "available" if pypdf_available else "unavailable_optional",
        "diagnostic": None if pypdf_available else "pypdf is not installed",
    }
    missing_gates = [
        "qpdf"
        for name in ("qpdf",)
        if not bool(tools[name]["available"])
    ]
    return {
        "schema": "edutex.pdf-runtime.v1",
        "language": language,
        "language_code": language_code,
        "compiler": compiler,
        "compiler_ready": compiler_ready,
        "required_compiler_tools": list(compiler_tools),
        "inspection_available": inspection_available,
        "inspection_gates": inspection_gates,
        "compiled_pdf_status": "ready" if compiler_ready else "skipped_no_compiler",
        "missing_gates": missing_gates,
        "tools": tools,
    }


def pdf_runtime_summary(language: str = "en") -> dict[str, object]:
    """Return the compact view derived from the detailed runtime report."""
    report = pdf_runtime_report(language)
    tools = report["tools"]
    assert isinstance(tools, dict)
    inspection_gates = report["inspection_gates"]
    assert isinstance(inspection_gates, dict)
    return {
        "language": report["language"],
        "language_code": report["language_code"],
        "compiler": report["compiler"],
        "compiler_ready": report["compiler_ready"],
        "required_compiler_tools": report["required_compiler_tools"],
        "tools": {name: bool(record["available"]) for name, record in tools.items()},
        "compiled_pdf_checks": report["inspection_available"],
        "compiled_pdf_status": report["compiled_pdf_status"],
        "inspection_gates": {
            name: record["status"] for name, record in inspection_gates.items()
        },
        "missing_gates": report["missing_gates"],
    }


def _pdfinfo_fields(output: str) -> dict[str, str]:
    """Parse simple ``pdfinfo`` key/value lines without locale assumptions."""
    fields: dict[str, str] = {}
    for line in output.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    return fields


def _validate_pdf_metadata(
    metadata: dict[str, str],
    *,
    title: str,
    author: str,
    subject: str,
) -> str | None:
    """Return the first mismatch in the required human-readable metadata."""
    expected = {"Title": title, "Author": author, "Subject": subject}
    for key, value in expected.items():
        if metadata.get(key) != value:
            return f"PDF metadata mismatch for {key}: expected {value!r}, got {metadata.get(key)!r}"
    return None


def _pypdf_gate_result(
    pdf_path: Path,
    *,
    expected_language: str = "en-US",
) -> tuple[str, str | None]:
    """Return an explicit pypdf gate status and optional diagnostic."""
    if not _pypdf_available():
        return "skipped_unavailable", "pypdf is not installed"
    error = _validate_pdf_parser(pdf_path, expected_language=expected_language)
    if error:
        return "failed", error
    return "passed", None


def _normalize_expected_pdf_language(language: str) -> str:
    """Normalize a course language to the PDF document-language tag expected by Q007."""
    normalized = language.strip().replace("_", "-")
    if normalized.lower() == "en":
        return "en-US"
    return normalized


def _validate_pdf_parser(
    pdf_path: Path,
    *,
    expected_language: str = "en-US",
) -> str | None:
    """Load a PDF with pypdf and verify its document language when possible."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return "pypdf parser is unavailable because the optional package is not installed"
    try:
        reader = PdfReader(str(pdf_path))
        if not reader.pages:
            return "pypdf loaded the PDF but found no pages"
        root = reader.trailer.get("/Root")
        document_language = root.get("/Lang") if root is not None else None
    except Exception as exc:  # pragma: no cover - parser failures are engine-specific
        return f"pypdf parser failed: {exc}"
    if document_language and document_language != expected_language:
        return f"PDF language mismatch: expected {expected_language!r}, got {document_language!r}"
    return None


PDF_LATEX_MARKERS = (
    r"\usepackage{cmap}",
    r"\ifdefined\pdfgentounicode",
    r"\IfFileExists{glyphtounicode.tex}{\input glyphtounicode}{}",
    r"\pdfgentounicode=1",
    "unicode=true",
    "bookmarks=true",
    "bookmarksopen=true",
    "bookmarksnumbered=true",
    "pdftitle={",
    "pdfauthor={",
    "pdfsubject={",
    "pdflang={",
)


def _validate_pdf_latex_source(source: str) -> str | None:
    """Return the first missing PDF/LaTeX accessibility contract marker."""
    for marker in PDF_LATEX_MARKERS:
        if marker not in source:
            return f"LaTeX accessibility marker missing: {marker}"
    return None


def _run_pdf_inspection_gates(
    pdf_path: Path,
    directory: Path,
    *,
    expected_language: str = "en-US",
) -> tuple[dict[str, str], list[str]]:
    """Run optional compiled-PDF gates and return statuses plus failures.

    ``expected_language`` defaults to the historical English PDF tag so existing
    callers and fixtures remain compatible.
    """
    validation_failures: list[str] = []
    gate_status = {
        "qpdf": "skipped_unavailable",
        "pdftotext": "skipped_unavailable",
        "pdfinfo": "skipped_unavailable",
        "pypdf": "skipped_unavailable",
        "pdftoppm": "skipped_unavailable",
    }
    if shutil.which("qpdf"):
        checked = run_subprocess(("qpdf", "--check", str(pdf_path)), directory)
        gate_status["qpdf"] = "passed" if checked.returncode == 0 else "failed"
        if checked.returncode != 0:
            validation_failures.append("qpdf --check failed: " + (_output(checked) or "no diagnostics"))

    text_path = directory / "output" / "course.txt"
    if shutil.which("pdftotext"):
        extracted = run_subprocess(("pdftotext", str(pdf_path), str(text_path)), directory)
        if extracted.returncode != 0:
            gate_status["pdftotext"] = "failed"
            validation_failures.append("pdftotext failed: " + (_output(extracted) or "no diagnostics"))
        elif "Quality Course" not in text_path.read_text(encoding="utf-8", errors="replace"):
            gate_status["pdftotext"] = "failed"
            validation_failures.append("pdftotext output did not contain the course title")
        else:
            gate_status["pdftotext"] = "passed"

    if shutil.which("pdfinfo"):
        info_result = run_subprocess(("pdfinfo", str(pdf_path)), directory)
        if info_result.returncode != 0:
            gate_status["pdfinfo"] = "failed"
            validation_failures.append("pdfinfo failed: " + (_output(info_result) or "no diagnostics"))
        else:
            metadata_error = _validate_pdf_metadata(
                _pdfinfo_fields(info_result.stdout),
                title="Quality Course",
                author="EduTeX",
                subject="EduTeX course roadmap",
            )
            gate_status["pdfinfo"] = "failed" if metadata_error else "passed"
            if metadata_error:
                validation_failures.append(metadata_error)

    parser_status, parser_diagnostic = _pypdf_gate_result(
        pdf_path,
        expected_language=expected_language,
    )
    gate_status["pypdf"] = parser_status
    if parser_status == "failed" and parser_diagnostic:
        validation_failures.append(parser_diagnostic)

    if shutil.which("pdftoppm"):
        preview_prefix = directory / "output" / "course-preview"
        rendered = run_subprocess(
            ("pdftoppm", "-f", "1", "-l", "1", "-singlefile", "-png", str(pdf_path), str(preview_prefix)),
            directory,
        )
        gate_status["pdftoppm"] = (
            "passed"
            if rendered.returncode == 0 and preview_prefix.with_suffix(".png").is_file()
            else "failed"
        )
        if gate_status["pdftoppm"] == "failed":
            validation_failures.append("pdftoppm render check failed: " + (_output(rendered) or "no diagnostics"))

    return gate_status, validation_failures


def _check_pdf_latex_accessibility(
    root: Path,
    *,
    language: str = "en",
) -> CheckResult:
    """Verify LaTeX accessibility source and environment-aware PDF output."""
    with tempfile.TemporaryDirectory(prefix="edutex-quality-pdf-") as temporary:
        directory = Path(temporary)
        _write_course_project(root, directory)

        latex = _run_module(root, "course", "build", "--project", str(directory), "--format", "latex")
        tex_path = directory / "output" / "course.tex"
        if latex.returncode != 0 or not tex_path.is_file():
            return CheckResult(
                "Q007 PDF/LaTeX accessibility contract",
                False,
                latex.returncode or 1,
                _output(latex) or "LaTeX output was not generated",
            )
        try:
            tex_source = tex_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            return CheckResult("Q007 PDF/LaTeX accessibility contract", False, 1, str(exc))
        source_error = _validate_pdf_latex_source(tex_source)
        if source_error:
            return CheckResult("Q007 PDF/LaTeX accessibility contract", False, 1, source_error)

        runtime = pdf_runtime_report(language)
        compiler_available = runtime["compiler"]
        if not compiler_available:
            return CheckResult(
                "Q007 PDF/LaTeX accessibility contract",
                True,
                detail=(
                    "LaTeX source accessibility markers passed; PDF skipped "
                    f"(supported latex compiler unavailable; schema={runtime['schema']}; "
                    f"inspection_gates={runtime['inspection_gates']}; "
                    f"tools={runtime['tools']})"
                ),
            )

        pdf = _run_module(root, "course", "build", "--project", str(directory), "--format", "pdf")
        pdf_path = directory / "output" / "course.pdf"
        if pdf.returncode != 0 or not pdf_path.is_file():
            return CheckResult(
                "Q007 PDF/LaTeX accessibility contract",
                False,
                pdf.returncode or 1,
                _output(pdf) or "PDF output was not generated",
            )

        expected_pdf_language = _normalize_expected_pdf_language(str(runtime["language"]))
        gate_status, validation_failures = _run_pdf_inspection_gates(
            pdf_path,
            directory,
            expected_language=expected_pdf_language,
        )
        gate_detail = "gates=" + ", ".join(f"{name}:{status}" for name, status in gate_status.items())
        if validation_failures:
            return CheckResult(
                "Q007 PDF/LaTeX accessibility contract",
                False,
                1,
                gate_detail + "\n" + "\n".join(validation_failures),
            )
    return CheckResult(
        "Q007 PDF/LaTeX accessibility contract",
        True,
        detail="LaTeX source and compiled PDF accessibility gates passed; " + gate_detail,
    )

def quality_baseline_report(results: Sequence[CheckResult]) -> dict[str, object]:
    """Return a stable JSON-safe report for CI consumers."""
    failed = next((result for result in results if not result.passed), None)
    return {
        "schema": "edutex.quality-baseline.v1",
        "passed": bool(results) and failed is None,
        "checks_completed": len(results),
        "checks_expected": len(CHECK_NAMES),
        "failed_check": failed.name if failed else None,
        "checks": [
            {
                "name": result.name,
                "passed": result.passed,
                "returncode": result.returncode,
                "detail": result.detail,
            }
            for result in results
        ],
    }


def run_quality(
    root: Path | None = None,
    *,
    verbose: bool = False,
    emit: bool = True,
) -> list[CheckResult]:
    """Run all checks in deterministic order, stopping at the first failure."""
    repository = (root or project_root()).resolve()
    checks = (
        _check_python_syntax,
        _check_pytest,
        _check_lint_json,
        _check_build_preflight,
        _check_cli_contract,
        _check_course_management,
        _check_pdf_latex_accessibility,
    )
    results: list[CheckResult] = []
    for check in checks:
        result = check(repository)
        results.append(result)
        status = "PASS" if result.passed else "FAIL"
        if emit:
            print(f"{status}: {result.name}")
            if result.detail and (verbose or not result.passed):
                print(result.detail)
        if not result.passed:
            break
    return results


def main(argv: Sequence[str] | None = None) -> int:
    """Run the quality baseline and return a process exit code."""
    parser = argparse.ArgumentParser(description="Run the EduTeX quality baseline.")
    parser.add_argument("--verbose", action="store_true", help="Print command diagnostics.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON report for CI consumers instead of human-readable output.",
    )
    arguments = parser.parse_args(argv)
    results = run_quality(verbose=arguments.verbose, emit=not arguments.json)
    if arguments.json:
        print(json.dumps(quality_baseline_report(results), indent=2, sort_keys=True))
    if not results or not results[-1].passed:
        return 1
    if not arguments.json:
        print(f"Quality baseline passed: {len(results)} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
