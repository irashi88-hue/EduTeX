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
from datetime import datetime, timezone
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence


QUALITY_CHECK_CATALOG = (
    ("Q001", "Python syntax", "Compile project Python sources without generating cache files."),
    ("Q002", "pytest suite", "Run the configured automated test suite."),
    ("Q003", "CLI lint JSON", "Validate the public lint command and its JSON output."),
    ("Q004", "build lint preflight", "Exercise blocking, warning, and normal build paths."),
    ("Q005", "CLI contract", "Verify the ordered public command and option help contract."),
    ("Q006", "Course management contract", "Validate course management and available output paths."),
    ("Q007", "PDF/LaTeX accessibility contract", "Validate LaTeX accessibility and compiled-PDF gates."),
    ("Q008", "Packaging contract", "Validate the packaged CLI entrypoint and public command surface."),
    ("Q009", "Release metadata contract", "Validate coherent project and CLI release metadata."),
    ("Q010", "Quality report schema contract", "Validate the public quality report schema and invariants."),
    ("Q011", "Quality report consistency contract", "Validate internal consistency of quality report values."),
    ("Q012", "Quality report diagnostics contract", "Validate deterministic diagnostics for malformed quality reports."),
    ("Q013", "Quality report value-types contract", "Validate JSON value types and basic value constraints."),
    ("Q014", "Quality report identity contract", "Validate report identifiers, timestamps, and identity relationships."),
    ("Q015", "Quality report catalog metadata contract", "Validate report catalog metadata and catalog-to-report projection."),
    ("Q016", "Quality report serialization contract", "Validate deterministic JSON serialization of quality reports."),
    ("Q017", "Quality CLI JSON output contract", "Validate the CLI JSON output channel and exit-code contract."),
    ("Q018", "Quality runner stop-on-failure contract", "Validate deterministic first-failure execution and result truncation."),
    ("Q019", "Quality runner/report alignment contract", "Validate that runner results and generated reports remain aligned."),
    ("Q020", "Quality report outcome contract", "Validate coherent report outcome status and exit semantics."),
    ("Q021", "Quality runner exception contract", "Validate deterministic handling of exceptions raised by checks."),
    ("Q022", "Quality runner identity contract", "Validate plan/result identity alignment and deterministic mismatch handling."),
    ("Q023", "Quality runner return-code contract", "Validate coherent return codes for passed and failed checks."),
    ("Q024", "Quality execution-plan structure contract", "Validate execution-plan entry structure and callable integrity."),
    ("Q025", "Quality execution diagnostics/report contract", "Validate propagation of plan diagnostics into runner reports."),
    ("Q026", "Quality diagnostics channel separation contract", "Validate deterministic separation of catalog and execution diagnostics."),
    ("Q027", "Quality report diagnostic outcome contract", "Validate coherent report outcome semantics when diagnostics are present."),
    ("Q028", "Quality diagnostic value-types contract", "Validate diagnostic value types and JSON serializability."),
    ("Q029", "Quality diagnostic uniqueness contract", "Validate non-empty unique diagnostic messages and stable ordering."),
    ("Q030", "Quality diagnostic determinism contract", "Validate stable diagnostic content and ordering across repeated runs."),
    ("Q031", "Quality diagnostic completeness contract", "Validate complete propagation of source diagnostics into reports."),
    ("Q032", "Quality diagnostic channel isolation contract", "Validate isolated catalog and execution diagnostic channels."),
    ("Q033", "Quality diagnostic provenance contract", "Validate provenance of diagnostics versus failed checks."),
    ("Q034", "Quality runner/report consistency contract", "Validate exact consistency between runner results and final reports."),
    ("Q035", "Release baseline end-to-end contract", "Validate the complete public quality baseline JSON path."),
    ("Q036", "Build/Validate JSON contract", "Validate structured JSON success and Extension-diagnostic failure paths for Build and Validate."),
)
CHECK_NAMES = tuple(f"{code} {label}" for code, label, _ in QUALITY_CHECK_CATALOG)
QUALITY_BASELINE_SCHEMA = "edutex.quality-baseline.v1"
QUALITY_OUTCOME_STATUSES = ("passed", "failed", "incomplete")
QUALITY_EXIT_CODES = {"passed": 0, "failed": 1, "incomplete": 1}


# Public CLI surface verified by Q005. Keep this ordered: the order is part of
# the human-facing help contract and makes regressions easy to diagnose.
PUBLIC_CLI_CONTRACT = (
    (("--help",), ("init", "lint", "build", "validate")),
    (("init", "--help"), ("--theme", "--language")),
    (("lint", "--help"), ("--format",)),
    (("build", "--help"), ("--lint",)),
    (("validate", "--help"), ("--project", "--config", "--format")),
)


PACKAGING_CONTRACT = (
    (
        "src/edutex/core/cli.py",
        (
            'CLI_VERSION = "0.5.0"',
            '@main.command("init")',
            '@main.command("lint")',
            '@main.command("build")',
            '@main.command("validate")',
            '@main.group("course")',
            '"--theme"',
            '"--language"',
            '"--lint"',
            '"--format"',
            "def _format_build_error_json",
        ),
    ),
    (
        "pyproject.toml",
        (
            'edutex = "edutex.core.cli:main"',
            "[tool.setuptools.packages.find]",
        ),
    ),
)


RELEASE_METADATA_CONTRACT = (
    "pyproject.toml",
    "src/edutex/core/cli.py",
    'edutex = "edutex.core.cli:main"',
)
RELEASE_VERSION_PATTERN = re.compile(
    r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?"
)


QUALITY_REPORT_REQUIRED_FIELDS = (
    "schema", "run_id", "run_started_at", "run_finished_at", "duration_seconds",
    "status", "passed", "complete", "exit_code", "catalog_consistent",
    "catalog_diagnostics", "execution_consistent", "execution_diagnostics",
    "checks_completed", "checks_expected", "missing_checks", "summary",
    "check_catalog", "failed_check", "failed_check_id", "checks",
)
QUALITY_REPORT_CHECK_FIELDS = ("id", "name", "passed", "status", "returncode", "detail")
QUALITY_REPORT_SUMMARY_FIELDS = (
    "passed", "failed", "pending", "total", "completed",
    "pass_rate", "completion_rate", "failure_rate",
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


def quality_check_catalog() -> tuple[dict[str, object], ...]:
    """Return the stable ordered catalog of quality checks."""
    return tuple(
        {
            "id": code,
            "name": f"{code} {label}",
            "description": description,
            "required": True,
        }
        for code, label, description in QUALITY_CHECK_CATALOG
    )


def public_cli_contract() -> tuple[tuple[tuple[str, ...], tuple[str, ...]], ...]:
    """Return the ordered public CLI help contract used by Q005."""
    return PUBLIC_CLI_CONTRACT


def packaging_contract() -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Return the static source and metadata markers required by Q008."""
    return PACKAGING_CONTRACT


def release_metadata_contract() -> tuple[str, str, str]:
    """Return the files and entry point required by Q009."""
    return RELEASE_METADATA_CONTRACT


def quality_report_contract() -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Return the required top-level, check, and summary report fields."""
    return (
        QUALITY_REPORT_REQUIRED_FIELDS,
        QUALITY_REPORT_CHECK_FIELDS,
        QUALITY_REPORT_SUMMARY_FIELDS,
    )


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
    """Verify the ordered public command and option help contract."""
    checks = public_cli_contract()
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


def _check_packaging_contract(root: Path) -> CheckResult:
    """Verify that packaging preserves the complete public CLI surface."""
    failures: list[str] = []
    for relative_path, required_markers in packaging_contract():
        path = root / relative_path
        if not path.is_file():
            failures.append(f"missing packaging file: {relative_path}")
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            failures.append(f"could not read {relative_path}: {exc}")
            continue
        missing = [marker for marker in required_markers if marker not in source]
        if missing:
            failures.append(
                f"{relative_path} missing packaging markers: {', '.join(missing)}"
            )
    cli_path = root / "src" / "edutex" / "core" / "cli.py"
    if cli_path.is_file():
        try:
            cli_source = cli_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            cli_source = ""
        if 'CLI_VERSION = "0.1.0"' in cli_source:
            failures.append("src/edutex/core/cli.py contains obsolete CLI_VERSION 0.1.0")
    if failures:
        return CheckResult("Q008 Packaging contract", False, 1, "\n".join(failures))
    return CheckResult(
        "Q008 Packaging contract",
        True,
        detail="packaged CLI entrypoint and public surface are intact",
    )



def _check_release_metadata_contract(root: Path) -> CheckResult:
    """Verify coherent project version, CLI version, and console entry point."""
    failures: list[str] = []
    metadata_path = root / "pyproject.toml"
    cli_path = root / "src" / "edutex" / "core" / "cli.py"

    if not metadata_path.is_file():
        failures.append("missing release metadata file: pyproject.toml")
    if not cli_path.is_file():
        failures.append("missing release metadata file: src/edutex/core/cli.py")
    if failures:
        return CheckResult("Q009 Release metadata contract", False, 1, "\n".join(failures))

    try:
        metadata = metadata_path.read_text(encoding="utf-8")
        cli_source = cli_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return CheckResult("Q009 Release metadata contract", False, 1, str(exc))

    try:
        import tomllib

        parsed = tomllib.loads(metadata)
    except (tomllib.TOMLDecodeError, UnicodeError) as exc:
        return CheckResult("Q009 Release metadata contract", False, 1, f"invalid pyproject.toml: {exc}")

    project = parsed.get("project")
    project_version = project.get("version") if isinstance(project, dict) else None
    scripts = project.get("scripts") if isinstance(project, dict) else None
    entrypoint = scripts.get("edutex") if isinstance(scripts, dict) else None

    cli_match = re.search(
        r"(?m)^\s*CLI_VERSION\s*=\s*[\"']([^\"']+)[\"']\s*$",
        cli_source,
    )
    cli_version = cli_match.group(1) if cli_match else None

    if not isinstance(project_version, str) or not project_version:
        failures.append("pyproject.toml is missing [project] version")
    elif RELEASE_VERSION_PATTERN.fullmatch(project_version) is None:
        failures.append(f"invalid release version in pyproject.toml: {project_version}")

    if cli_version is None:
        failures.append("src/edutex/core/cli.py is missing CLI_VERSION")
    elif RELEASE_VERSION_PATTERN.fullmatch(cli_version) is None:
        failures.append(f"invalid CLI release version: {cli_version}")

    if project_version is not None and cli_version is not None and project_version != cli_version:
        failures.append(
            f"release version mismatch: pyproject.toml={project_version}, "
            f"src/edutex/core/cli.py={cli_version}"
        )

    if entrypoint != "edutex.core.cli:main":
        failures.append(
            "project entry point mismatch: expected edutex.core.cli:main, "
            f"got {entrypoint!r}"
        )

    if failures:
        return CheckResult("Q009 Release metadata contract", False, 1, "\n".join(failures))
    return CheckResult(
        "Q009 Release metadata contract",
        True,
        detail=f"release metadata is coherent at version {project_version}",
    )


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

def quality_baseline_catalog_diagnostics(
    results: Sequence[CheckResult],
) -> tuple[str, ...]:
    """Return deterministic diagnostics for result/catalog mismatches."""
    expected_names = check_names()
    diagnostics: list[str] = []
    seen: set[str] = set()
    for index, result in enumerate(results):
        position = index + 1
        if result.name not in expected_names:
            diagnostics.append(f"unknown quality check at position {position}: {result.name}")
        if result.name in seen:
            diagnostics.append(f"duplicate quality check result: {result.name}")
        seen.add(result.name)
        if index < len(expected_names) and result.name != expected_names[index]:
            diagnostics.append(
                f"quality check order mismatch at position {position}: "
                f"expected {expected_names[index]}, got {result.name}"
            )
    if len(results) > len(expected_names):
        diagnostics.append(
            f"too many quality check results: expected at most {len(expected_names)}, "
            f"got {len(results)}"
        )
    return tuple(diagnostics)


def quality_check_id(name: str) -> str | None:
    """Return the stable catalog ID for a quality check name."""
    for code, label, _ in QUALITY_CHECK_CATALOG:
        if name == f"{code} {label}":
            return code
    return None


def quality_baseline_missing_checks(results: Sequence[CheckResult]) -> tuple[str, ...]:
    """Return IDs for catalog checks that have no completed result."""
    completed_names = {result.name for result in results}
    return tuple(
        code
        for code, label, _ in QUALITY_CHECK_CATALOG
        if f"{code} {label}" not in completed_names
    )


def quality_baseline_status(results: Sequence[CheckResult]) -> str:
    """Return the stable outcome status for a quality baseline run."""
    if quality_check_execution_diagnostics():
        return "failed"
    if quality_baseline_catalog_diagnostics(results):
        return "failed"
    if any(not result.passed for result in results):
        return "failed"
    if len(results) != len(QUALITY_CHECK_CATALOG):
        return "incomplete"
    return "passed"


def new_quality_run_id() -> str:
    """Return a unique UUID v4 for one quality baseline execution."""
    return str(uuid.uuid4())


def new_quality_run_started_at() -> str:
    """Return the current quality baseline start time as UTC RFC 3339 text."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def new_quality_run_finished_at() -> str:
    """Return the current quality baseline finish time as UTC RFC 3339 text."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def quality_baseline_summary(results: Sequence[CheckResult]) -> dict[str, int]:
    """Return stable pass/fail/pending counts for completed quality results."""
    passed = sum(1 for result in results if result.passed)
    failed = sum(1 for result in results if not result.passed)
    expected = len(QUALITY_CHECK_CATALOG)
    completed = len(results)
    return {
        "passed": passed,
        "failed": failed,
        "pending": max(0, expected - completed),
        "total": expected,
        "completed": completed,
        "pass_rate": round((passed / completed) * 100, 2) if completed else 0.0,
        "completion_rate": round((completed / expected) * 100, 2) if expected else 0.0,
        "failure_rate": round((failed / completed) * 100, 2) if completed else 0.0,
    }


def quality_baseline_report_diagnostics(report: dict[str, object]) -> tuple[str, ...]:
    """Return deterministic diagnostics for the public JSON report contract."""
    diagnostics: list[str] = []
    checks = report.get("checks")
    summary = report.get("summary")
    if not isinstance(checks, list):
        diagnostics.append("report checks must be a list")
    if not isinstance(summary, dict):
        diagnostics.append("report summary must be an object")
    if isinstance(checks, list):
        for index, entry in enumerate(checks, start=1):
            if not isinstance(entry, dict):
                diagnostics.append(f"report check at position {index} must be an object")
                continue
            passed = entry.get("passed")
            expected_status = "passed" if passed is True else "failed" if passed is False else None
            if expected_status is not None and entry.get("status") != expected_status:
                diagnostics.append(
                    f"report check status mismatch at position {index}: "
                    f"expected {expected_status}, got {entry.get('status')!r}"
                )
            if entry.get("id") is None or entry.get("name") is None:
                diagnostics.append(f"report check identity missing at position {index}")
    catalog_diagnostics = report.get("catalog_diagnostics")
    execution_diagnostics = report.get("execution_diagnostics")
    for field_name, value in (
        ("catalog_diagnostics", catalog_diagnostics),
        ("execution_diagnostics", execution_diagnostics),
    ):
        if not isinstance(value, list):
            diagnostics.append(f"report {field_name} must be a list")
        else:
            invalid_values = [item for item in value if not isinstance(item, str)]
            if invalid_values:
                diagnostics.append(f"report {field_name} must contain only strings")
            else:
                empty_values = [index for index, item in enumerate(value, start=1) if not item.strip()]
                if empty_values:
                    diagnostics.append(
                        f"report {field_name} must not contain empty messages at positions "
                        + ", ".join(str(index) for index in empty_values)
                    )
                seen_values: set[str] = set()
                duplicate_values: list[str] = []
                for item in value:
                    if item in seen_values and item not in duplicate_values:
                        duplicate_values.append(item)
                    seen_values.add(item)
                if duplicate_values:
                    diagnostics.append(
                        f"report {field_name} contains duplicate messages: "
                        + ", ".join(repr(item) for item in duplicate_values)
                    )

    for field_name in ("catalog_consistent", "execution_consistent"):
        value = report.get(field_name)
        if type(value) is not bool:
            diagnostics.append(f"report {field_name} must be a boolean")
    if isinstance(catalog_diagnostics, list) and isinstance(report.get("catalog_consistent"), bool):
        expected_catalog_consistent = not catalog_diagnostics
        if report["catalog_consistent"] is not expected_catalog_consistent:
            diagnostics.append(
                "report catalog consistency mismatch: "
                f"expected {expected_catalog_consistent}, got {report['catalog_consistent']!r}"
            )
    if isinstance(execution_diagnostics, list) and isinstance(report.get("execution_consistent"), bool):
        expected_execution_consistent = not execution_diagnostics
        if report["execution_consistent"] is not expected_execution_consistent:
            diagnostics.append(
                "report execution consistency mismatch: "
                f"expected {expected_execution_consistent}, got {report['execution_consistent']!r}"
            )

    status = report.get("status")
    if status in QUALITY_OUTCOME_STATUSES:
        expected_passed = status == "passed"
        expected_complete = status == "passed"
        expected_exit_code = QUALITY_EXIT_CODES[status]
        if report.get("passed") is not expected_passed:
            diagnostics.append(
                f"report outcome passed mismatch: expected {expected_passed}, got {report.get('passed')!r}"
            )
        if report.get("complete") is not expected_complete:
            diagnostics.append(
                f"report outcome complete mismatch: expected {expected_complete}, got {report.get('complete')!r}"
            )
        if report.get("exit_code") != expected_exit_code:
            diagnostics.append(
                f"report outcome exit-code mismatch: expected {expected_exit_code}, got {report.get('exit_code')!r}"
            )

        has_diagnostics = bool(catalog_diagnostics) or bool(execution_diagnostics)
        if has_diagnostics and status != "failed":
            diagnostics.append(
                f"report diagnostic outcome mismatch: diagnostics require failed status, got {status!r}"
            )
        if has_diagnostics and report.get("passed") is True:
            diagnostics.append("report diagnostic outcome mismatch: diagnostics require passed=false")
        if has_diagnostics and report.get("complete") is True:
            diagnostics.append("report diagnostic outcome mismatch: diagnostics require complete=false")
        if has_diagnostics and report.get("exit_code") == 0:
            diagnostics.append("report diagnostic outcome mismatch: diagnostics require exit_code=1")

    if isinstance(summary, dict):
        required_summary = (
            "passed", "failed", "pending", "total", "completed",
            "pass_rate", "completion_rate", "failure_rate",
        )
        missing = [key for key in required_summary if key not in summary]
        if missing:
            diagnostics.append("report summary fields missing: " + ", ".join(missing))
    return tuple(diagnostics)


def quality_baseline_report(
    results: Sequence[CheckResult],
    *,
    run_id: str | None = None,
    run_started_at: str | None = None,
    run_finished_at: str | None = None,
    duration_seconds: float | None = None,
) -> dict[str, object]:
    """Return a stable JSON-safe report for CI consumers."""
    failed = next((result for result in results if not result.passed), None)
    execution_id = run_id or new_quality_run_id()
    execution_started_at = run_started_at or new_quality_run_started_at()
    execution_finished_at = run_finished_at or new_quality_run_finished_at()
    execution_duration = duration_seconds if duration_seconds is not None else 0.0
    catalog_diagnostics = quality_baseline_catalog_diagnostics(results)
    execution_diagnostics = quality_check_execution_diagnostics()
    status = quality_baseline_status(results)
    summary = quality_baseline_summary(results)
    return {
        "schema": QUALITY_BASELINE_SCHEMA,
        "run_id": execution_id,
        "run_started_at": execution_started_at,
        "run_finished_at": execution_finished_at,
        "duration_seconds": execution_duration,
        "status": status,
        "passed": status == "passed",
        "complete": status == "passed",
        "exit_code": QUALITY_EXIT_CODES[status],
        "catalog_consistent": not catalog_diagnostics,
        "catalog_diagnostics": list(catalog_diagnostics),
        "execution_consistent": not execution_diagnostics,
        "execution_diagnostics": list(execution_diagnostics),
        "checks_completed": len(results),
        "checks_expected": len(QUALITY_CHECK_CATALOG),
        "missing_checks": list(quality_baseline_missing_checks(results)),
        "summary": summary,
        "check_catalog": list(quality_check_catalog()),
        "failed_check": failed.name if failed else None,
        "failed_check_id": quality_check_id(failed.name) if failed else None,
        "checks": [
            {
                "id": quality_check_id(result.name),
                "name": result.name,
                "passed": result.passed,
                "status": "passed" if result.passed else "failed",
                "returncode": result.returncode,
                "detail": result.detail,
            }
            for result in results
        ],
    }


def _check_quality_report_schema_contract(root: Path) -> CheckResult:
    """Verify the public JSON quality report shape and semantic invariants."""
    del root
    failures: list[str] = []
    expected_ids = tuple(code for code, _, _ in QUALITY_CHECK_CATALOG)
    complete = quality_baseline_report(
        [CheckResult(name, True) for name in CHECK_NAMES],
        run_id="q010-complete",
        run_started_at="2026-09-11T10:00:00Z",
        run_finished_at="2026-09-11T10:00:01Z",
        duration_seconds=1.0,
    )
    failed = quality_baseline_report(
        [CheckResult("Q001 Python syntax", True), CheckResult("Q002 pytest suite", False, 7, "pytest failed")],
        run_id="q010-failed",
        run_started_at="2026-09-11T10:00:00Z",
        run_finished_at="2026-09-11T10:00:02Z",
        duration_seconds=2.0,
    )
    empty = quality_baseline_report(
        [],
        run_id="q010-empty",
        run_started_at="2026-09-11T10:00:00Z",
        run_finished_at="2026-09-11T10:00:03Z",
        duration_seconds=3.0,
    )
    for label, report in (("complete", complete), ("failed", failed), ("empty", empty)):
        missing = [field for field in QUALITY_REPORT_REQUIRED_FIELDS if field not in report]
        if missing:
            failures.append(f"{label} report missing fields: {', '.join(missing)}")
        diagnostics = quality_baseline_report_diagnostics(report)
        if diagnostics:
            failures.append(f"{label} report diagnostics: {'; '.join(diagnostics)}")
        if report.get("schema") != QUALITY_BASELINE_SCHEMA:
            failures.append(f"{label} report schema mismatch: {report.get('schema')!r}")
        checks = report.get("checks")
        if isinstance(checks, list):
            for index, entry in enumerate(checks, start=1):
                if not isinstance(entry, dict):
                    failures.append(f"{label} check {index} is not an object")
                else:
                    missing_fields = [field for field in QUALITY_REPORT_CHECK_FIELDS if field not in entry]
                    if missing_fields:
                        failures.append(f"{label} check {index} missing fields: {', '.join(missing_fields)}")
        summary = report.get("summary")
        if isinstance(summary, dict):
            missing_fields = [field for field in QUALITY_REPORT_SUMMARY_FIELDS if field not in summary]
            if missing_fields:
                failures.append(f"{label} summary missing fields: {', '.join(missing_fields)}")
    if complete.get("status") != "passed" or complete.get("complete") is not True or complete.get("exit_code") != 0:
        failures.append("complete report outcome is inconsistent")
    if complete.get("missing_checks") != []:
        failures.append(f"complete report missing_checks is not empty: {complete.get('missing_checks')!r}")
    if [entry.get("id") for entry in complete.get("check_catalog", [])] != list(expected_ids):
        failures.append("complete report catalog order does not match the quality catalog")
    if failed.get("status") != "failed" or failed.get("complete") is not False or failed.get("exit_code") != 1:
        failures.append("failed report outcome is inconsistent")
    if failed.get("failed_check_id") != "Q002":
        failures.append(f"failed report failed_check_id mismatch: {failed.get('failed_check_id')!r}")
    if empty.get("status") != "incomplete" or empty.get("complete") is not False or empty.get("exit_code") != 1:
        failures.append("empty report outcome is inconsistent")
    if empty.get("missing_checks") != list(expected_ids):
        failures.append("empty report missing_checks does not contain the full catalog")
    import json
    try:
        json.dumps(complete)
        json.dumps(failed)
        json.dumps(empty)
    except (TypeError, ValueError) as exc:
        failures.append(f"report is not JSON serializable: {exc}")
    if failures:
        return CheckResult("Q010 Quality report schema contract", False, 1, chr(10).join(failures))
    return CheckResult("Q010 Quality report schema contract", True, detail="quality report schema, outcomes, catalog, and JSON serialization are coherent")



def _check_quality_report_consistency_contract(root: Path) -> CheckResult:
    """Verify that report counts, statuses, catalog, and outcome fields agree."""
    del root
    failures: list[str] = []
    expected_ids = tuple(code for code, _, _ in QUALITY_CHECK_CATALOG)
    scenarios = (
        (
            "complete",
            [CheckResult(name, True) for name in CHECK_NAMES],
            "passed",
            0,
        ),
        (
            "failed",
            [CheckResult("Q001 Python syntax", True), CheckResult("Q002 pytest suite", False, 7, "pytest failed")],
            "failed",
            1,
        ),
        (
            "incomplete",
            [CheckResult("Q001 Python syntax", True)],
            "incomplete",
            1,
        ),
    )
    for label, results, expected_status, expected_exit in scenarios:
        report = quality_baseline_report(results, run_id=f"q011-{label}")
        summary = report["summary"]
        checks = report["checks"]
        catalog = report["check_catalog"]
        ids = [entry["id"] for entry in checks]
        catalog_ids = [entry["id"] for entry in catalog]
        passed = sum(1 for result in results if result.passed)
        failed = sum(1 for result in results if not result.passed)
        completed = len(results)
        expected = len(QUALITY_CHECK_CATALOG)
        missing = list(quality_baseline_missing_checks(results))
        if report["status"] != expected_status:
            failures.append(f"{label} status mismatch: {report['status']!r}")
        if report["exit_code"] != expected_exit:
            failures.append(f"{label} exit_code mismatch: {report['exit_code']!r}")
        if report["complete"] is not (expected_status == "passed"):
            failures.append(f"{label} complete flag mismatch: {report['complete']!r}")
        if report["checks_completed"] != completed or report["checks_expected"] != expected:
            failures.append(f"{label} check counts mismatch")
        if report["missing_checks"] != missing:
            failures.append(f"{label} missing_checks mismatch")
        if catalog_ids != list(expected_ids):
            failures.append(f"{label} catalog order mismatch")
        if summary["passed"] != passed or summary["failed"] != failed:
            failures.append(f"{label} pass/fail summary mismatch")
        if summary["pending"] != max(0, expected - completed):
            failures.append(f"{label} pending summary mismatch")
        if summary["total"] != expected or summary["completed"] != completed:
            failures.append(f"{label} total/completed summary mismatch")
        if ids != list(expected_ids[:completed]):
            failures.append(f"{label} check result order mismatch")
        if report["failed_check_id"] != ("Q002" if label == "failed" else None):
            failures.append(f"{label} failed_check_id mismatch")
        if quality_baseline_report_diagnostics(report):
            failures.append(f"{label} report diagnostics are non-empty")
    if failures:
        return CheckResult("Q011 Quality report consistency contract", False, 1, "\n".join(failures))
    return CheckResult(
        "Q011 Quality report consistency contract",
        True,
        detail="quality report counts, statuses, catalog, missing checks, and outcomes agree",
    )



def _check_quality_report_diagnostics_contract(root: Path) -> CheckResult:
    """Verify deterministic diagnostics for representative report corruption."""
    del root
    failures: list[str] = []
    baseline = quality_baseline_report(
        [CheckResult("Q001 Python syntax", True), CheckResult("Q002 pytest suite", False, 7, "pytest failed")],
        run_id="q012-diagnostics",
        run_started_at="2026-09-11T10:00:00Z",
        run_finished_at="2026-09-11T10:00:02Z",
        duration_seconds=2.0,
    )
    if quality_baseline_report_diagnostics(baseline):
        failures.append("valid report produced diagnostics")

    cases = (
        ("missing checks", lambda report: report.pop("checks"), "report checks must be a list"),
        ("missing summary", lambda report: report.pop("summary"), "report summary must be an object"),
        ("status drift", lambda report: report["checks"][0].update(status="failed"), "report check status mismatch"),
        ("identity drift", lambda report: report["checks"][0].pop("id"), "report check identity missing"),
        ("summary drift", lambda report: report["summary"].pop("failure_rate"), "report summary fields missing: failure_rate"),
    )
    for label, mutate, expected in cases:
        report = quality_baseline_report(
            [CheckResult("Q001 Python syntax", True), CheckResult("Q002 pytest suite", False, 7, "pytest failed")],
            run_id=f"q012-{label.replace(' ', '-')}",
        )
        mutate(report)
        diagnostics = quality_baseline_report_diagnostics(report)
        if not diagnostics or not any(expected in item for item in diagnostics):
            failures.append(f"{label} diagnostic mismatch: {diagnostics!r}")

    if failures:
        return CheckResult("Q012 Quality report diagnostics contract", False, 1, "\n".join(failures))
    return CheckResult(
        "Q012 Quality report diagnostics contract",
        True,
        detail="valid and intentionally malformed reports produce deterministic diagnostics",
    )



def _check_quality_report_value_types_contract(root: Path) -> CheckResult:
    """Verify JSON value types and basic constraints for representative reports."""
    del root
    failures: list[str] = []
    reports = (
        quality_baseline_report(
            [CheckResult(name, True) for name in CHECK_NAMES],
            run_id="q013-complete",
            run_started_at="2026-09-11T10:00:00Z",
            run_finished_at="2026-09-11T10:00:01Z",
            duration_seconds=1.0,
        ),
        quality_baseline_report(
            [CheckResult("Q001 Python syntax", True), CheckResult("Q002 pytest suite", False, 7, "pytest failed")],
            run_id="q013-failed",
            run_started_at="2026-09-11T10:00:00Z",
            run_finished_at="2026-09-11T10:00:02Z",
            duration_seconds=2.0,
        ),
        quality_baseline_report(
            [],
            run_id="q013-empty",
            run_started_at="2026-09-11T10:00:00Z",
            run_finished_at="2026-09-11T10:00:03Z",
            duration_seconds=3.0,
        ),
    )
    top_string_fields = ("schema", "run_id", "run_started_at", "run_finished_at", "status")
    top_bool_fields = ("passed", "complete", "catalog_consistent", "execution_consistent")
    top_int_fields = ("exit_code", "checks_completed", "checks_expected")
    top_list_fields = ("catalog_diagnostics", "execution_diagnostics", "missing_checks", "check_catalog", "checks")
    nullable_string_fields = ("failed_check", "failed_check_id")
    summary_int_fields = ("passed", "failed", "pending", "total", "completed")
    summary_number_fields = ("pass_rate", "completion_rate", "failure_rate")
    check_string_fields = ("id", "name", "status", "detail")
    check_bool_fields = ("passed",)
    check_int_fields = ("returncode",)

    for report_index, report in enumerate(reports, start=1):
        label = f"report {report_index}"
        for field in top_string_fields:
            if not isinstance(report.get(field), str):
                failures.append(f"{label} field {field} is not a string")
        for field in top_bool_fields:
            if not isinstance(report.get(field), bool):
                failures.append(f"{label} field {field} is not a boolean")
        for field in top_int_fields:
            value = report.get(field)
            if not isinstance(value, int) or isinstance(value, bool):
                failures.append(f"{label} field {field} is not an integer")
        if not isinstance(report.get("duration_seconds"), (int, float)) or isinstance(report.get("duration_seconds"), bool):
            failures.append(f"{label} field duration_seconds is not numeric")
        elif report["duration_seconds"] < 0:
            failures.append(f"{label} field duration_seconds is negative")
        for field in top_list_fields:
            if not isinstance(report.get(field), list):
                failures.append(f"{label} field {field} is not a list")
        for field in nullable_string_fields:
            value = report.get(field)
            if value is not None and not isinstance(value, str):
                failures.append(f"{label} field {field} is neither null nor a string")
        summary = report.get("summary")
        if not isinstance(summary, dict):
            failures.append(f"{label} summary is not an object")
        else:
            for field in summary_int_fields:
                value = summary.get(field)
                if not isinstance(value, int) or isinstance(value, bool):
                    failures.append(f"{label} summary field {field} is not an integer")
            for field in summary_number_fields:
                value = summary.get(field)
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    failures.append(f"{label} summary field {field} is not numeric")
                elif value < 0:
                    failures.append(f"{label} summary field {field} is negative")
        checks = report.get("checks")
        if isinstance(checks, list):
            for index, entry in enumerate(checks, start=1):
                if not isinstance(entry, dict):
                    failures.append(f"{label} check {index} is not an object")
                    continue
                for field in check_string_fields:
                    if not isinstance(entry.get(field), str):
                        failures.append(f"{label} check {index} field {field} is not a string")
                for field in check_bool_fields:
                    if not isinstance(entry.get(field), bool):
                        failures.append(f"{label} check {index} field {field} is not a boolean")
                for field in check_int_fields:
                    value = entry.get(field)
                    if not isinstance(value, int) or isinstance(value, bool):
                        failures.append(f"{label} check {index} field {field} is not an integer")
    if failures:
        return CheckResult("Q013 Quality report value-types contract", False, 1, "\n".join(failures))
    return CheckResult(
        "Q013 Quality report value-types contract",
        True,
        detail="quality report value types and basic constraints are coherent",
    )



def _check_quality_report_identity_contract(root: Path) -> CheckResult:
    """Verify report identifiers, timestamps, and identity relationships."""
    del root
    failures: list[str] = []
    expected_ids = tuple(code for code, _, _ in QUALITY_CHECK_CATALOG)
    scenarios = (
        (
            "complete",
            [CheckResult(name, True) for name in CHECK_NAMES],
            "2026-09-11T10:00:00Z",
            "2026-09-11T10:00:01Z",
        ),
        (
            "failed",
            [
                CheckResult("Q001 Python syntax", True),
                CheckResult("Q002 pytest suite", False, 7, "pytest failed"),
            ],
            "2026-09-11T10:00:00Z",
            "2026-09-11T10:00:02Z",
        ),
        (
            "incomplete",
            [CheckResult("Q001 Python syntax", True)],
            "2026-09-11T10:00:00Z",
            "2026-09-11T10:00:03Z",
        ),
    )
    for label, results, started, finished in scenarios:
        report = quality_baseline_report(
            results,
            run_id=f"q014-{label}",
            run_started_at=started,
            run_finished_at=finished,
            duration_seconds=1.0,
        )
        run_id = report.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            failures.append(f"{label} run_id is not a non-empty string")
        parsed_times = []
        for field in ("run_started_at", "run_finished_at"):
            value = report.get(field)
            if not isinstance(value, str) or not value.endswith("Z"):
                failures.append(f"{label} {field} is not a UTC RFC 3339 string")
                continue
            try:
                parsed_times.append(datetime.fromisoformat(value.replace("Z", "+00:00")))
            except ValueError:
                failures.append(f"{label} {field} is not parseable")
        if len(parsed_times) == 2 and parsed_times[1] < parsed_times[0]:
            failures.append(f"{label} run_finished_at precedes run_started_at")

        checks = report.get("checks")
        if not isinstance(checks, list):
            failures.append(f"{label} checks is not a list")
            continue
        check_ids = []
        for index, entry in enumerate(checks, start=1):
            if not isinstance(entry, dict):
                failures.append(f"{label} check {index} is not an object")
                continue
            check_id = entry.get("id")
            name = entry.get("name")
            expected_id = quality_check_id(name) if isinstance(name, str) else None
            check_ids.append(check_id)
            if check_id != expected_id:
                failures.append(
                    f"{label} check {index} identity mismatch: expected {expected_id!r}, got {check_id!r}"
                )
        if check_ids != list(expected_ids[: len(results)]):
            failures.append(f"{label} check identity order mismatch")
        if len(check_ids) != len(set(check_ids)):
            failures.append(f"{label} check identities are not unique")

        missing = report.get("missing_checks")
        expected_missing = list(expected_ids[len(results):])
        if missing != expected_missing:
            failures.append(f"{label} missing-check identity order mismatch")
        if isinstance(missing, list) and len(missing) != len(set(missing)):
            failures.append(f"{label} missing-check identities are not unique")

        failed = next((result for result in results if not result.passed), None)
        expected_failed_id = quality_check_id(failed.name) if failed else None
        if report.get("failed_check_id") != expected_failed_id:
            failures.append(f"{label} failed_check_id identity mismatch")
        if report.get("failed_check") != (failed.name if failed else None):
            failures.append(f"{label} failed_check identity mismatch")

        catalog = report.get("check_catalog")
        if not isinstance(catalog, list):
            failures.append(f"{label} check_catalog is not a list")
        else:
            catalog_ids = [entry.get("id") for entry in catalog if isinstance(entry, dict)]
            if catalog_ids != list(expected_ids):
                failures.append(f"{label} catalog identity order mismatch")
            if len(catalog_ids) != len(set(catalog_ids)):
                failures.append(f"{label} catalog identities are not unique")

    if failures:
        return CheckResult("Q014 Quality report identity contract", False, 1, "\\n".join(failures))
    return CheckResult(
        "Q014 Quality report identity contract",
        True,
        detail="quality report identifiers, timestamps, and identity relationships are coherent",
    )



def _check_quality_report_catalog_metadata_contract(root: Path) -> CheckResult:
    """Verify stable catalog metadata and its report projection."""
    del root
    failures: list[str] = []
    expected_catalog = quality_check_catalog()
    expected_ids = tuple(code for code, _, _ in QUALITY_CHECK_CATALOG)
    expected_names = tuple(f"{code} {label}" for code, label, _ in QUALITY_CHECK_CATALOG)
    required_fields = ("id", "name", "description", "required")

    if len(expected_catalog) != len(expected_ids):
        failures.append("quality catalog length does not match its source catalog")
    for index, entry in enumerate(expected_catalog, start=1):
        if tuple(entry) != required_fields:
            failures.append(f"catalog entry {index} fields are not stable")
        if entry.get("id") != expected_ids[index - 1]:
            failures.append(f"catalog entry {index} id mismatch")
        if entry.get("name") != expected_names[index - 1]:
            failures.append(f"catalog entry {index} name mismatch")
        if not isinstance(entry.get("description"), str) or not entry.get("description"):
            failures.append(f"catalog entry {index} description is not a non-empty string")
        if entry.get("required") is not True:
            failures.append(f"catalog entry {index} required flag is not true")
        if quality_check_id(entry.get("name")) != entry.get("id"):
            failures.append(f"catalog entry {index} name-to-id mapping mismatch")

    reports = (
        quality_baseline_report([], run_id="q015-empty"),
        quality_baseline_report(
            [CheckResult("Q001 Python syntax", True), CheckResult("Q002 pytest suite", False, 7, "pytest failed")],
            run_id="q015-failed",
        ),
        quality_baseline_report(
            [CheckResult(name, True) for name in CHECK_NAMES],
            run_id="q015-complete",
        ),
    )
    for report_index, report in enumerate(reports, start=1):
        projected = report.get("check_catalog")
        if projected != list(expected_catalog):
            failures.append(f"report {report_index} catalog metadata projection mismatch")
        if isinstance(projected, list):
            projected_ids = [entry.get("id") for entry in projected if isinstance(entry, dict)]
            if projected_ids != list(expected_ids):
                failures.append(f"report {report_index} catalog metadata order mismatch")
            if len(projected_ids) != len(set(projected_ids)):
                failures.append(f"report {report_index} catalog metadata IDs are not unique")

    if failures:
        return CheckResult("Q015 Quality report catalog metadata contract", False, 1, "\\n".join(failures))
    return CheckResult(
        "Q015 Quality report catalog metadata contract",
        True,
        detail="quality catalog metadata and report catalog projection are coherent",
    )



def _check_quality_report_serialization_contract(root: Path) -> CheckResult:
    """Verify deterministic JSON serialization of representative reports."""
    del root
    failures: list[str] = []
    reports = (
        quality_baseline_report([], run_id="q016-empty", run_started_at="2026-09-11T10:00:00Z", run_finished_at="2026-09-11T10:00:00Z"),
        quality_baseline_report(
            [CheckResult("Q001 Python syntax", True), CheckResult("Q002 pytest suite", False, 7, "pytest failed")],
            run_id="q016-failed", run_started_at="2026-09-11T10:00:00Z", run_finished_at="2026-09-11T10:00:02Z", duration_seconds=2.0,
        ),
        quality_baseline_report(
            [CheckResult(name, True) for name in CHECK_NAMES],
            run_id="q016-complete", run_started_at="2026-09-11T10:00:00Z", run_finished_at="2026-09-11T10:00:15Z", duration_seconds=15.0,
        ),
    )
    for index, report in enumerate(reports, start=1):
        try:
            serialized = json.dumps(report, indent=2, sort_keys=True)
            first = serialized + "\n"
            second = json.dumps(report, indent=2, sort_keys=True) + "\n"
            if first != second:
                failures.append(f"report {index} serialization is not deterministic")
            decoded = json.loads(first)
            if decoded != report:
                failures.append(f"report {index} does not round-trip through JSON")
            if not first.endswith("}\n"):
                failures.append(f"report {index} JSON output does not end with a newline")
            keys = list(report)
            encoded_keys = list(json.loads(first))
            if encoded_keys != sorted(keys):
                failures.append(f"report {index} JSON keys are not sorted")
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            failures.append(f"report {index} is not JSON serializable: {exc}")
    if failures:
        return CheckResult("Q016 Quality report serialization contract", False, 1, "\\n".join(failures))
    return CheckResult(
        "Q016 Quality report serialization contract",
        True,
        detail="quality reports serialize deterministically and round-trip as JSON",
    )



def _check_quality_cli_json_output_contract(root: Path) -> CheckResult:
    """Verify the public quality CLI JSON channel and exit-code contract."""
    failures: list[str] = []
    script = Path(__file__).resolve()
    scenarios = (
        ("incomplete", ["--json"], root, 1),
        ("incomplete-verbose", ["--json", "--verbose"], root, 1),
    )
    # Q017 probes the public CLI in a subprocess. The probe sets a private
    # environment flag so the child executes Q001-Q016 and does not recurse into Q017.
    probe = "import runpy, sys; script=sys.argv[1]; sys.argv=sys.argv[1:]; runpy.run_path(script, run_name='__main__')"
    probe_environment = os.environ.copy()
    probe_environment["EDUTEX_Q017_PROBE"] = "1"
    for label, arguments, cwd, expected_exit in scenarios:
        completed = subprocess.run(
            [sys.executable, "-c", probe, str(script), *arguments],
            cwd=cwd,
            capture_output=True,
            text=True,
            env={**_python_env(root), **probe_environment},
            check=False,
        )
        if completed.returncode != expected_exit:
            failures.append(f"{label} exit code mismatch: expected {expected_exit}, got {completed.returncode}")
        if completed.stderr:
            failures.append(f"{label} wrote diagnostics to stderr")
        try:
            report = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            failures.append(f"{label} stdout is not JSON: {exc}")
            continue
        if not isinstance(report, dict):
            failures.append(f"{label} JSON root is not an object")
            continue
        if report.get("schema") != QUALITY_BASELINE_SCHEMA:
            failures.append(f"{label} schema mismatch")
        if report.get("status") not in {"failed", "incomplete"}:
            failures.append(f"{label} status mismatch: {report.get('status')!r}")
        if report.get("exit_code") != expected_exit:
            failures.append(f"{label} report exit_code mismatch")
        if completed.stdout and not completed.stdout.endswith("\n"):
            failures.append(f"{label} stdout is not newline-terminated")
    if failures:
        return CheckResult("Q017 Quality CLI JSON output contract", False, 1, "\n".join(failures))
    return CheckResult("Q017 Quality CLI JSON output contract", True, detail="quality CLI JSON output is isolated, parseable, and exit-code aligned")



def _check_quality_runner_stop_on_failure_contract(root: Path) -> CheckResult:
    """Verify deterministic stop-on-first-failure behavior of run_quality()."""
    global quality_check_execution_plan, quality_check_execution_diagnostics
    del root
    failures: list[str] = []
    original_plan = quality_check_execution_plan
    original_diagnostics = quality_check_execution_diagnostics
    calls: list[str] = []

    def passing_check(repository: Path) -> CheckResult:
        calls.append("Q001")
        return CheckResult("Q001 Python syntax", True)

    def failing_check(repository: Path) -> CheckResult:
        calls.append("Q002")
        return CheckResult("Q002 pytest suite", False, 7, "synthetic failure")

    def should_not_run(repository: Path) -> CheckResult:
        calls.append("Q003")
        return CheckResult("Q003 CLI lint JSON", True)

    try:
        quality_check_execution_plan = lambda: (
            ("Q001", passing_check),
            ("Q002", failing_check),
            ("Q003", should_not_run),
        )
        quality_check_execution_diagnostics = lambda: ()
        results = run_quality(Path("."), emit=False)
    finally:
        quality_check_execution_plan = original_plan
        quality_check_execution_diagnostics = original_diagnostics

    if calls != ["Q001", "Q002"]:
        failures.append(f"runner call order/truncation mismatch: {calls!r}")
    if len(results) != 2:
        failures.append(f"runner returned {len(results)} results instead of 2")
    if results and results[-1].passed:
        failures.append("runner did not retain the first failed result")
    if results and results[-1].returncode != 7:
        failures.append("runner changed the first failure return code")
    if results and results[-1].detail != "synthetic failure":
        failures.append("runner changed the first failure detail")

    def second_passing_check(repository: Path) -> CheckResult:
        del repository
        calls.append("Q002")
        return CheckResult("Q002 pytest suite", True)

    calls.clear()
    try:
        quality_check_execution_plan = lambda: (("Q001", passing_check), ("Q002", second_passing_check))
        quality_check_execution_diagnostics = lambda: ()
        results = run_quality(Path("."), emit=False)
    finally:
        quality_check_execution_plan = original_plan
        quality_check_execution_diagnostics = original_diagnostics
    if calls != ["Q001", "Q002"]:
        failures.append(f"all-pass runner call order mismatch: {calls!r}")
    if len(results) != 2 or any(not result.passed for result in results):
        failures.append("all-pass runner did not return all passing results")

    if failures:
        return CheckResult("Q018 Quality runner stop-on-failure contract", False, 1, "\n".join(failures))
    return CheckResult(
        "Q018 Quality runner stop-on-failure contract",
        True,
        detail="quality runner stops at the first failure and preserves deterministic results",
    )



def _check_quality_runner_report_alignment_contract(root: Path) -> CheckResult:
    """Verify that runner results project coherently into public reports."""
    del root
    failures: list[str] = []
    original_plan = quality_check_execution_plan
    original_diagnostics = quality_check_execution_diagnostics

    def passing_check(repository: Path) -> CheckResult:
        del repository
        return CheckResult("Q001 Python syntax", True, detail="synthetic pass")

    def failing_check(repository: Path) -> CheckResult:
        del repository
        return CheckResult("Q002 pytest suite", False, 7, "synthetic failure")

    try:
        globals()["quality_check_execution_plan"] = lambda: (
            ("Q001", passing_check),
            ("Q002", failing_check),
            ("Q003", passing_check),
        )
        globals()["quality_check_execution_diagnostics"] = lambda: ()
        failed_results = run_quality(Path("."), emit=False)
    finally:
        globals()["quality_check_execution_plan"] = original_plan
        globals()["quality_check_execution_diagnostics"] = original_diagnostics

    failed_report = quality_baseline_report(
        failed_results,
        run_id="q019-failed",
        run_started_at="2026-09-14T10:00:00Z",
        run_finished_at="2026-09-14T10:00:01Z",
        duration_seconds=1.0,
    )
    if [result.name for result in failed_results] != [
        "Q001 Python syntax", "Q002 pytest suite"
    ]:
        failures.append("failed runner results were not truncated at the first failure")
    if failed_report["status"] != "failed":
        failures.append(f"failed report status mismatch: {failed_report['status']!r}")
    if failed_report["checks_completed"] != 2:
        failures.append("failed report completed count does not match runner results")
    if failed_report["failed_check_id"] != "Q002":
        failures.append("failed report does not identify the runner failure")
    if failed_report["checks"][1]["returncode"] != 7:
        failures.append("failed report changed the runner return code")
    if failed_report["checks"][1]["detail"] != "synthetic failure":
        failures.append("failed report changed the runner diagnostic detail")
    if quality_baseline_report_diagnostics(failed_report):
        failures.append("failed runner report has internal diagnostics")

    names = CHECK_NAMES
    def make_passing_check(name: str) -> Callable[[Path], CheckResult]:
        def check(repository: Path) -> CheckResult:
            del repository
            return CheckResult(name, True, detail="synthetic pass")
        return check

    try:
        globals()["quality_check_execution_plan"] = lambda: tuple(
            (name.split(" ", 1)[0], make_passing_check(name)) for name in names
        )
        globals()["quality_check_execution_diagnostics"] = lambda: ()
        all_results = run_quality(Path("."), emit=False)
    finally:
        globals()["quality_check_execution_plan"] = original_plan
        globals()["quality_check_execution_diagnostics"] = original_diagnostics

    all_report = quality_baseline_report(
        all_results,
        run_id="q019-complete",
        run_started_at="2026-09-14T10:00:00Z",
        run_finished_at="2026-09-14T10:00:02Z",
        duration_seconds=2.0,
    )
    if tuple(result.name for result in all_results) != names:
        failures.append("all-pass runner results are not in catalog order")
    if all_report["status"] != "passed" or all_report["complete"] is not True:
        failures.append("all-pass runner report is not complete and passed")
    if all_report["checks_completed"] != len(names):
        failures.append("all-pass report completed count does not match runner results")
    if all_report["missing_checks"] != []:
        failures.append("all-pass report unexpectedly contains missing checks")
    if all_report["failed_check"] is not None or all_report["failed_check_id"] is not None:
        failures.append("all-pass report unexpectedly identifies a failed check")
    if quality_baseline_report_diagnostics(all_report):
        failures.append("all-pass runner report has internal diagnostics")

    if failures:
        return CheckResult(
            "Q019 Quality runner/report alignment contract",
            False,
            1,
            "\n".join(failures),
        )
    return CheckResult(
        "Q019 Quality runner/report alignment contract",
        True,
        detail="quality runner results and generated reports remain aligned",
    )



def _check_quality_report_outcome_contract(root: Path) -> CheckResult:
    """Verify coherent status, completion, and exit semantics in reports."""
    del root
    failures: list[str] = []
    complete = quality_baseline_report(
        [CheckResult(name, True) for name in CHECK_NAMES],
        run_id="q020-complete",
        run_started_at="2026-09-14T10:00:00Z",
        run_finished_at="2026-09-14T10:00:01Z",
        duration_seconds=1.0,
    )
    failed = quality_baseline_report(
        [
            CheckResult("Q001 Python syntax", True),
            CheckResult("Q002 pytest suite", False, 7, "synthetic failure"),
        ],
        run_id="q020-failed",
        run_started_at="2026-09-14T10:00:00Z",
        run_finished_at="2026-09-14T10:00:02Z",
        duration_seconds=2.0,
    )
    incomplete = quality_baseline_report(
        [],
        run_id="q020-incomplete",
        run_started_at="2026-09-14T10:00:00Z",
        run_finished_at="2026-09-14T10:00:03Z",
        duration_seconds=3.0,
    )
    inconsistent = quality_baseline_report(
        [CheckResult("Q001 Python syntax", True), CheckResult("Q003 CLI lint JSON", True)],
        run_id="q020-inconsistent",
        run_started_at="2026-09-14T10:00:00Z",
        run_finished_at="2026-09-14T10:00:04Z",
        duration_seconds=4.0,
    )

    if complete["status"] != "passed" or complete["passed"] is not True:
        failures.append("complete report status/passed mismatch")
    if complete["complete"] is not True or complete["exit_code"] != 0:
        failures.append("complete report completion/exit mismatch")
    if complete["failed_check"] is not None or complete["failed_check_id"] is not None:
        failures.append("complete report unexpectedly identifies a failure")
    if complete["missing_checks"] != []:
        failures.append("complete report unexpectedly contains missing checks")

    if failed["status"] != "failed" or failed["passed"] is not False:
        failures.append("failed report status/passed mismatch")
    if failed["complete"] is not False or failed["exit_code"] != 1:
        failures.append("failed report completion/exit mismatch")
    if failed["failed_check"] != "Q002 pytest suite" or failed["failed_check_id"] != "Q002":
        failures.append("failed report failure identity mismatch")
    if failed["missing_checks"] != [
        "Q003", "Q004", "Q005", "Q006", "Q007", "Q008", "Q009", "Q010",
        "Q011", "Q012", "Q013", "Q014", "Q015", "Q016", "Q017", "Q018",
        "Q019", "Q020", "Q021", "Q022", "Q023", "Q024", "Q025", "Q026", "Q027", "Q028", "Q029", "Q030", "Q031", "Q032", "Q033", "Q034", "Q035", "Q036",
    ]:
        failures.append("failed report missing-check semantics mismatch")

    if incomplete["status"] != "incomplete" or incomplete["passed"] is not False:
        failures.append("incomplete report status/passed mismatch")
    if incomplete["complete"] is not False or incomplete["exit_code"] != 1:
        failures.append("incomplete report completion/exit mismatch")
    if incomplete["failed_check"] is not None or incomplete["failed_check_id"] is not None:
        failures.append("incomplete report unexpectedly identifies a failure")
    if len(incomplete["missing_checks"]) != len(QUALITY_CHECK_CATALOG):
        failures.append("incomplete report missing-check count mismatch")

    if inconsistent["status"] != "failed" or inconsistent["passed"] is not False:
        failures.append("inconsistent report status/passed mismatch")
    if inconsistent["complete"] is not False or inconsistent["exit_code"] != 1:
        failures.append("inconsistent report completion/exit mismatch")
    if inconsistent["catalog_consistent"] is not False or not inconsistent["catalog_diagnostics"]:
        failures.append("inconsistent report catalog outcome mismatch")

    for label, report in (
        ("complete", complete),
        ("failed", failed),
        ("incomplete", incomplete),
        ("inconsistent", inconsistent),
    ):
        if quality_baseline_report_diagnostics(report):
            failures.append(f"{label} report has unexpected diagnostics")

    if failures:
        return CheckResult(
            "Q020 Quality report outcome contract",
            False,
            1,
            "\n".join(failures),
        )
    return CheckResult(
        "Q020 Quality report outcome contract",
        True,
        detail="quality report status, completion, failure identity, and exit semantics are coherent",
    )



def _check_quality_runner_exception_contract(root: Path) -> CheckResult:
    """Verify that check exceptions become deterministic failed results."""
    del root
    failures: list[str] = []
    original_plan = quality_check_execution_plan
    original_diagnostics = quality_check_execution_diagnostics
    calls: list[str] = []

    def passing_check(repository: Path) -> CheckResult:
        del repository
        calls.append("Q001")
        return CheckResult("Q001 Python syntax", True, detail="synthetic pass")

    def raising_check(repository: Path) -> CheckResult:
        del repository
        calls.append("Q002")
        raise RuntimeError("synthetic exception")

    def should_not_run(repository: Path) -> CheckResult:
        del repository
        calls.append("Q003")
        return CheckResult("Q003 CLI lint JSON", True, detail="must not run")

    try:
        globals()["quality_check_execution_plan"] = lambda: (
            ("Q001", passing_check),
            ("Q002", raising_check),
            ("Q003", should_not_run),
        )
        globals()["quality_check_execution_diagnostics"] = lambda: ()
        results = run_quality(Path("."), emit=False)
    finally:
        globals()["quality_check_execution_plan"] = original_plan
        globals()["quality_check_execution_diagnostics"] = original_diagnostics

    if calls != ["Q001", "Q002"]:
        failures.append(f"exception runner call order mismatch: {calls!r}")
    if len(results) != 2:
        failures.append(f"exception runner returned {len(results)} results instead of 2")
    if results and results[-1].passed:
        failures.append("exception result was not marked failed")
    if results and results[-1].name != "Q002 pytest suite":
        failures.append("exception result changed the failing check identity")
    if results and results[-1].returncode == 0:
        failures.append("exception result retained a zero return code")
    if results and results[-1].detail != "RuntimeError: synthetic exception":
        failures.append("exception result detail is not deterministic")

    report = quality_baseline_report(
        results,
        run_id="q021-exception",
        run_started_at="2026-09-14T10:00:00Z",
        run_finished_at="2026-09-14T10:00:01Z",
        duration_seconds=1.0,
    )
    if report["status"] != "failed" or report["exit_code"] != 1:
        failures.append("exception report outcome is not failed")
    if report["failed_check_id"] != "Q002":
        failures.append("exception report failed-check identity mismatch")
    if report["checks"][1]["detail"] != "RuntimeError: synthetic exception":
        failures.append("exception report did not preserve exception detail")
    if quality_baseline_report_diagnostics(report):
        failures.append("exception report has internal diagnostics")

    if failures:
        return CheckResult(
            "Q021 Quality runner exception contract",
            False,
            1,
            "\n".join(failures),
        )
    return CheckResult(
        "Q021 Quality runner exception contract",
        True,
        detail="quality runner converts check exceptions into deterministic failed results",
    )



def _check_quality_runner_identity_contract(root: Path) -> CheckResult:
    """Verify that plan IDs and returned result names remain aligned."""
    del root
    failures: list[str] = []
    original_plan = quality_check_execution_plan
    original_diagnostics = quality_check_execution_diagnostics
    calls: list[str] = []

    def passing_check(repository: Path) -> CheckResult:
        del repository
        calls.append("Q001")
        return CheckResult("Q001 Python syntax", True, detail="synthetic pass")

    def mismatched_check(repository: Path) -> CheckResult:
        del repository
        calls.append("Q002")
        return CheckResult("Q999 Unknown check", True, detail="wrong identity")

    def should_not_run(repository: Path) -> CheckResult:
        del repository
        calls.append("Q003")
        return CheckResult("Q003 CLI lint JSON", True, detail="must not run")

    try:
        globals()["quality_check_execution_plan"] = lambda: (
            ("Q001", passing_check),
            ("Q002", mismatched_check),
            ("Q003", should_not_run),
        )
        globals()["quality_check_execution_diagnostics"] = lambda: ()
        results = run_quality(Path("."), emit=False)
    finally:
        globals()["quality_check_execution_plan"] = original_plan
        globals()["quality_check_execution_diagnostics"] = original_diagnostics

    if calls != ["Q001", "Q002"]:
        failures.append(f"identity runner call order mismatch: {calls!r}")
    if len(results) != 2:
        failures.append(f"identity runner returned {len(results)} results instead of 2")
    if results and results[-1].passed:
        failures.append("identity mismatch result was not marked failed")
    if results and results[-1].name != "Q002 pytest suite":
        failures.append("identity mismatch result did not use the expected check name")
    if results and results[-1].returncode == 0:
        failures.append("identity mismatch result retained a zero return code")
    if results and results[-1].detail != (
        "check identity mismatch: expected Q002 pytest suite, got Q999 Unknown check"
    ):
        failures.append("identity mismatch detail is not deterministic")

    report = quality_baseline_report(
        results,
        run_id="q022-identity",
        run_started_at="2026-09-14T10:00:00Z",
        run_finished_at="2026-09-14T10:00:01Z",
        duration_seconds=1.0,
    )
    if report["status"] != "failed" or report["exit_code"] != 1:
        failures.append("identity mismatch report outcome is not failed")
    if report["failed_check_id"] != "Q002":
        failures.append("identity mismatch report failed-check identity mismatch")
    if report["checks"][1]["name"] != "Q002 pytest suite":
        failures.append("identity mismatch report name is not normalized")
    if quality_baseline_report_diagnostics(report):
        failures.append("identity mismatch report has internal diagnostics")

    if failures:
        return CheckResult(
            "Q022 Quality runner identity contract",
            False,
            1,
            "\n".join(failures),
        )
    return CheckResult(
        "Q022 Quality runner identity contract",
        True,
        detail="quality runner enforces deterministic plan/result identity alignment",
    )



def _check_quality_runner_returncode_contract(root: Path) -> CheckResult:
    """Verify deterministic normalization of check return-code semantics."""
    del root
    failures: list[str] = []
    original_plan = quality_check_execution_plan
    original_diagnostics = quality_check_execution_diagnostics

    def passed_with_failure_code(repository: Path) -> CheckResult:
        del repository
        return CheckResult("Q001 Python syntax", True, 7, "synthetic pass")

    def failed_with_success_code(repository: Path) -> CheckResult:
        del repository
        return CheckResult("Q001 Python syntax", False, 0, "synthetic failure")

    def should_not_run(repository: Path) -> CheckResult:
        del repository
        failures.append("return-code contract executed a later check")
        return CheckResult("Q002 pytest suite", True)

    try:
        globals()["quality_check_execution_plan"] = lambda: (
            ("Q001", passed_with_failure_code),
            ("Q002", should_not_run),
        )
        globals()["quality_check_execution_diagnostics"] = lambda: ()
        passed_results = run_quality(Path("."), emit=False)
    finally:
        globals()["quality_check_execution_plan"] = original_plan
        globals()["quality_check_execution_diagnostics"] = original_diagnostics

    if len(passed_results) != 1:
        failures.append("passed/non-zero result did not stop after normalization")
    if passed_results and passed_results[0].passed:
        failures.append("passed/non-zero result remained passed")
    if passed_results and passed_results[0].returncode != 7:
        failures.append("passed/non-zero result changed its non-zero code")
    if passed_results and passed_results[0].detail != (
        "return-code mismatch: passed result expected 0, got 7"
    ):
        failures.append("passed/non-zero diagnostic is not deterministic")

    try:
        globals()["quality_check_execution_plan"] = lambda: (
            ("Q001", failed_with_success_code),
            ("Q002", should_not_run),
        )
        globals()["quality_check_execution_diagnostics"] = lambda: ()
        failed_results = run_quality(Path("."), emit=False)
    finally:
        globals()["quality_check_execution_plan"] = original_plan
        globals()["quality_check_execution_diagnostics"] = original_diagnostics

    if len(failed_results) != 1:
        failures.append("failed/zero result did not stop after normalization")
    if failed_results and failed_results[0].passed:
        failures.append("failed/zero result became passed")
    if failed_results and failed_results[0].returncode != 1:
        failures.append("failed/zero result was not normalized to code 1")
    if failed_results and failed_results[0].detail != (
        "synthetic failure; return-code mismatch: failed result normalized 0 to 1"
    ):
        failures.append("failed/zero diagnostic is not deterministic")

    report = quality_baseline_report(
        failed_results,
        run_id="q023-returncode",
        run_started_at="2026-09-14T10:00:00Z",
        run_finished_at="2026-09-14T10:00:01Z",
        duration_seconds=1.0,
    )
    if report["status"] != "failed" or report["exit_code"] != 1:
        failures.append("return-code report outcome is not failed")
    if report["checks"][0]["returncode"] != 1:
        failures.append("return-code report did not preserve normalized code")
    if quality_baseline_report_diagnostics(report):
        failures.append("return-code report has internal diagnostics")

    if failures:
        return CheckResult(
            "Q023 Quality runner return-code contract",
            False,
            1,
            "\n".join(failures),
        )
    return CheckResult(
        "Q023 Quality runner return-code contract",
        True,
        detail="quality runner normalizes passed and failed return-code semantics deterministically",
    )



def _check_quality_execution_plan_structure_contract(root: Path) -> CheckResult:
    """Verify deterministic diagnostics for malformed execution plans."""
    del root
    failures: list[str] = []
    original_plan = quality_check_execution_plan
    original_diagnostics = quality_check_execution_diagnostics

    def valid_check(repository: Path) -> CheckResult:
        del repository
        return CheckResult("Q001 Python syntax", True)

    malformed_plans = (
        (
            "malformed-entry",
            (("Q001", valid_check), ("Q002",)),
            "quality execution entry at position 2 must be a 2-item pair",
        ),
        (
            "unknown-id",
            (("Q001", valid_check), ("Q999", valid_check)),
            "unknown quality execution ID at position 2: Q999",
        ),
        (
            "duplicate-id",
            (("Q001", valid_check), ("Q001", valid_check)),
            "duplicate quality execution ID at position 2: Q001",
        ),
        (
            "non-callable",
            (("Q001", valid_check), ("Q002", None)),
            "quality execution entry at position 2 is not callable",
        ),
    )

    for label, plan, expected in malformed_plans:
        try:
            globals()["quality_check_execution_plan"] = lambda plan=plan: plan
            diagnostics = quality_check_execution_diagnostics()
        finally:
            globals()["quality_check_execution_plan"] = original_plan
        if expected not in diagnostics:
            failures.append(f"{label} diagnostic missing: {expected}")
        try:
            globals()["quality_check_execution_plan"] = lambda plan=plan: plan
            results = run_quality(Path("."), emit=False)
        finally:
            globals()["quality_check_execution_plan"] = original_plan
        if len(results) != 1 or results[0].passed:
            failures.append(f"{label} malformed plan did not fail safely")
        if results and results[0].returncode == 0:
            failures.append(f"{label} malformed plan retained zero return code")

    globals()["quality_check_execution_diagnostics"] = original_diagnostics
    if failures:
        return CheckResult(
            "Q024 Quality execution-plan structure contract",
            False,
            1,
            "\n".join(failures),
        )
    return CheckResult(
        "Q024 Quality execution-plan structure contract",
        True,
        detail="quality execution-plan structure and callable integrity are diagnosed deterministically",
    )



def _check_quality_execution_diagnostics_report_contract(root: Path) -> CheckResult:
    """Verify that plan diagnostics propagate coherently into reports."""
    del root
    failures: list[str] = []
    original_plan = quality_check_execution_plan
    original_diagnostics = quality_check_execution_diagnostics

    def valid_check(repository: Path) -> CheckResult:
        del repository
        return CheckResult("Q001 Python syntax", True)

    malformed_plan = (("Q001", valid_check), ("Q001", valid_check))
    expected_fragment = "duplicate quality execution ID at position 2: Q001"

    try:
        globals()["quality_check_execution_plan"] = lambda: malformed_plan
        diagnostics = quality_check_execution_diagnostics()
        results = run_quality(Path("."), emit=False)
    finally:
        globals()["quality_check_execution_plan"] = original_plan

    if expected_fragment not in diagnostics:
        failures.append("plan diagnostic was not produced")
    if len(results) != 1 or results[0].passed:
        failures.append("diagnostic plan did not produce one failed runner result")
    if results and expected_fragment not in results[0].detail:
        failures.append("runner result did not preserve plan diagnostics")

    try:
        globals()["quality_check_execution_plan"] = lambda: malformed_plan
        globals()["quality_check_execution_diagnostics"] = lambda: diagnostics
        report = quality_baseline_report(
            results,
            run_id="q025-plan-diagnostics",
            run_started_at="2026-09-14T10:00:00Z",
            run_finished_at="2026-09-14T10:00:01Z",
            duration_seconds=1.0,
        )
    finally:
        globals()["quality_check_execution_plan"] = original_plan
        globals()["quality_check_execution_diagnostics"] = original_diagnostics

    if report["status"] != "failed" or report["exit_code"] != 1:
        failures.append("diagnostic report outcome is not failed")
    if report["execution_consistent"] is not False:
        failures.append("diagnostic report incorrectly marks execution consistent")
    if report["execution_diagnostics"] != list(diagnostics):
        failures.append("diagnostics were not copied verbatim into the report")
    if report["catalog_consistent"] is not True:
        failures.append("diagnostic report incorrectly marks catalog inconsistent")
    if quality_baseline_report_diagnostics(report):
        failures.append("diagnostic report has internal diagnostics")

    if failures:
        return CheckResult(
            "Q025 Quality execution diagnostics/report contract",
            False,
            1,
            "\n".join(failures),
        )
    return CheckResult(
        "Q025 Quality execution diagnostics/report contract",
        True,
        detail="quality plan diagnostics propagate deterministically into failed runner reports",
    )


def _check_quality_diagnostics_channel_separation_contract(root: Path) -> CheckResult:
    """Verify deterministic separation of catalog and execution diagnostics."""
    del root
    failures: list[str] = []
    original_plan = quality_check_execution_plan
    original_diagnostics = quality_check_execution_diagnostics

    def valid_check(repository: Path) -> CheckResult:
        del repository
        return CheckResult("Q001 Python syntax", True)

    malformed_plan = (("Q001", valid_check), ("Q001", valid_check))
    plan_fragment = "duplicate quality execution ID at position 2: Q001"
    catalog_results = (
        CheckResult("Q001 Python syntax", True),
        CheckResult("Q003 CLI lint JSON", True),
    )

    try:
        globals()["quality_check_execution_plan"] = lambda: malformed_plan
        execution_diagnostics = quality_check_execution_diagnostics()
        report = quality_baseline_report(
            catalog_results,
            run_id="q026-channel-separation",
            run_started_at="2026-09-14T10:00:00Z",
            run_finished_at="2026-09-14T10:00:01Z",
            duration_seconds=1.0,
        )
    finally:
        globals()["quality_check_execution_plan"] = original_plan
        globals()["quality_check_execution_diagnostics"] = original_diagnostics

    if plan_fragment not in execution_diagnostics:
        failures.append("execution diagnostic channel did not preserve the plan diagnostic")
    if report["status"] != "failed" or report["exit_code"] != 1:
        failures.append("combined-diagnostic report outcome is not failed")
    if report["catalog_consistent"] is not False:
        failures.append("catalog diagnostics were not marked inconsistent")
    if report["execution_consistent"] is not False:
        failures.append("execution diagnostics were not marked inconsistent")
    if not report["catalog_diagnostics"]:
        failures.append("catalog diagnostics were not propagated")
    if report["execution_diagnostics"] != list(execution_diagnostics):
        failures.append("execution diagnostics were not copied verbatim")
    if any(item in report["catalog_diagnostics"] for item in report["execution_diagnostics"]):
        failures.append("execution diagnostics were duplicated into catalog diagnostics")
    if any(item in report["execution_diagnostics"] for item in report["catalog_diagnostics"]):
        failures.append("catalog diagnostics were duplicated into execution diagnostics")
    expected_catalog_diagnostics = quality_baseline_catalog_diagnostics(catalog_results)
    if report["catalog_diagnostics"] != list(expected_catalog_diagnostics):
        failures.append("catalog diagnostic order or content was not preserved")
    if report["execution_diagnostics"] != list(execution_diagnostics):
        failures.append("execution diagnostic order or content was not preserved")
    if quality_baseline_report_diagnostics(report):
        failures.append("combined-diagnostic report has internal report diagnostics")

    if failures:
        return CheckResult(
            "Q026 Quality diagnostics channel separation contract",
            False,
            1,
            "\n".join(failures),
        )
    return CheckResult(
        "Q026 Quality diagnostics channel separation contract",
        True,
        detail="catalog and execution diagnostics remain separate, ordered, and report-safe",
    )


def _check_quality_report_diagnostic_outcome_contract(root: Path) -> CheckResult:
    """Verify coherent outcome semantics for reports containing diagnostics."""
    del root
    failures: list[str] = []

    valid_report = quality_baseline_report(
        [CheckResult("Q001 Python syntax", True)],
        run_id="q027-valid",
        run_started_at="2026-09-14T10:00:00Z",
        run_finished_at="2026-09-14T10:00:01Z",
        duration_seconds=1.0,
    )
    catalog_report = quality_baseline_report(
        [CheckResult("Q001 Python syntax", True), CheckResult("Q003 CLI lint JSON", True)],
        run_id="q027-catalog",
        run_started_at="2026-09-14T10:00:00Z",
        run_finished_at="2026-09-14T10:00:02Z",
        duration_seconds=2.0,
    )

    if quality_baseline_report_diagnostics(valid_report):
        failures.append("valid incomplete report unexpectedly has diagnostics")
    if catalog_report["status"] != "failed" or catalog_report["passed"] is not False:
        failures.append("catalog-diagnostic report outcome is not failed")
    if catalog_report["complete"] is not False or catalog_report["exit_code"] != 1:
        failures.append("catalog-diagnostic report completion/exit semantics are incoherent")
    if catalog_report["catalog_consistent"] is not False or not catalog_report["catalog_diagnostics"]:
        failures.append("catalog-diagnostic report consistency channel is incoherent")
    if quality_baseline_report_diagnostics(catalog_report):
        failures.append("generated catalog-diagnostic report has internal diagnostics")

    mutations = (
        (
            "catalog flag",
            lambda report: report.update({"catalog_consistent": True}),
            "report catalog consistency mismatch",
        ),
        (
            "execution flag",
            lambda report: report.update({"execution_diagnostics": ["synthetic execution diagnostic"]}),
            "report execution consistency mismatch",
        ),
        (
            "passed flag",
            lambda report: report.update({"passed": True}),
            "report outcome passed mismatch",
        ),
        (
            "complete flag",
            lambda report: report.update({"complete": True}),
            "report outcome complete mismatch",
        ),
        (
            "exit code",
            lambda report: report.update({"exit_code": 0}),
            "report outcome exit-code mismatch",
        ),
        (
            "diagnostic status",
            lambda report: report.update({"status": "incomplete"}),
            "report diagnostic outcome mismatch",
        ),
    )
    for label, mutate, expected in mutations:
        report = dict(catalog_report)
        report["catalog_diagnostics"] = list(catalog_report["catalog_diagnostics"])
        report["execution_diagnostics"] = list(catalog_report["execution_diagnostics"])
        mutate(report)
        diagnostics = quality_baseline_report_diagnostics(report)
        if not any(expected in item for item in diagnostics):
            failures.append(f"{label} mutation was not diagnosed: {diagnostics!r}")

    if failures:
        return CheckResult(
            "Q027 Quality report diagnostic outcome contract",
            False,
            1,
            "\n".join(failures),
        )
    return CheckResult(
        "Q027 Quality report diagnostic outcome contract",
        True,
        detail="report diagnostics, consistency flags, outcome status, and exit semantics remain coherent",
    )


def _check_quality_diagnostic_value_types_contract(root: Path) -> CheckResult:
    """Verify diagnostic channels and consistency flags have JSON-safe types."""
    del root
    failures: list[str] = []
    valid_report = quality_baseline_report(
        [CheckResult("Q001 Python syntax", True), CheckResult("Q003 CLI lint JSON", True)],
        run_id="q028-types",
        run_started_at="2026-09-14T10:00:00Z",
        run_finished_at="2026-09-14T10:00:01Z",
        duration_seconds=1.0,
    )

    if quality_baseline_report_diagnostics(valid_report):
        failures.append("generated report unexpectedly failed diagnostic value validation")
    try:
        json.dumps(valid_report, sort_keys=True)
    except (TypeError, ValueError) as exc:
        failures.append(f"generated report is not JSON serializable: {exc}")

    mutations = (
        (
            "catalog scalar",
            lambda report: report.update({"catalog_diagnostics": "not-a-list"}),
            "report catalog_diagnostics must be a list",
        ),
        (
            "execution scalar",
            lambda report: report.update({"execution_diagnostics": "not-a-list"}),
            "report execution_diagnostics must be a list",
        ),
        (
            "catalog non-string",
            lambda report: report.update({"catalog_diagnostics": ["ok", 7]}),
            "report catalog_diagnostics must contain only strings",
        ),
        (
            "execution non-string",
            lambda report: report.update({"execution_diagnostics": [None]}),
            "report execution_diagnostics must contain only strings",
        ),
        (
            "catalog flag",
            lambda report: report.update({"catalog_consistent": 1}),
            "report catalog_consistent must be a boolean",
        ),
        (
            "execution flag",
            lambda report: report.update({"execution_consistent": "true"}),
            "report execution_consistent must be a boolean",
        ),
    )
    for label, mutate, expected in mutations:
        report = dict(valid_report)
        report["catalog_diagnostics"] = list(valid_report["catalog_diagnostics"])
        report["execution_diagnostics"] = list(valid_report["execution_diagnostics"])
        mutate(report)
        diagnostics = quality_baseline_report_diagnostics(report)
        if expected not in diagnostics:
            failures.append(f"{label} mutation was not diagnosed: {diagnostics!r}")

    non_serializable = dict(valid_report)
    non_serializable["execution_diagnostics"] = [object()]
    try:
        json.dumps(non_serializable, sort_keys=True)
    except TypeError:
        pass
    else:
        failures.append("non-serializable diagnostic value was unexpectedly accepted")

    if failures:
        return CheckResult(
            "Q028 Quality diagnostic value-types contract",
            False,
            1,
            "\n".join(failures),
        )
    return CheckResult(
        "Q028 Quality diagnostic value-types contract",
        True,
        detail="diagnostic channels use string lists, boolean flags, and JSON-safe values",
    )


def _check_quality_diagnostic_uniqueness_contract(root: Path) -> CheckResult:
    """Verify non-empty, unique, ordered diagnostic messages in reports."""
    del root
    failures: list[str] = []
    valid_report = quality_baseline_report(
        [CheckResult("Q001 Python syntax", True), CheckResult("Q003 CLI lint JSON", True)],
        run_id="q029-uniqueness",
        run_started_at="2026-09-14T10:00:00Z",
        run_finished_at="2026-09-14T10:00:01Z",
        duration_seconds=1.0,
    )
    if quality_baseline_report_diagnostics(valid_report):
        failures.append("generated report unexpectedly has diagnostic uniqueness errors")

    cases = (
        (
            "catalog empty",
            "catalog_diagnostics",
            ["first", "", "third"],
            "report catalog_diagnostics must not contain empty messages at positions 2",
        ),
        (
            "execution whitespace",
            "execution_diagnostics",
            ["first", "   "],
            "report execution_diagnostics must not contain empty messages at positions 2",
        ),
        (
            "catalog duplicate",
            "catalog_diagnostics",
            ["same", "same"],
            "report catalog_diagnostics contains duplicate messages: 'same'",
        ),
        (
            "execution duplicate",
            "execution_diagnostics",
            ["same", "next", "same"],
            "report execution_diagnostics contains duplicate messages: 'same'",
        ),
    )
    for label, field_name, values, expected in cases:
        report = dict(valid_report)
        report["catalog_diagnostics"] = list(valid_report["catalog_diagnostics"])
        report["execution_diagnostics"] = list(valid_report["execution_diagnostics"])
        report[field_name] = values
        diagnostics = quality_baseline_report_diagnostics(report)
        if expected not in diagnostics:
            failures.append(f"{label} was not diagnosed: {diagnostics!r}")

    ordered = dict(valid_report)
    ordered["catalog_diagnostics"] = ["alpha", "beta", "gamma"]
    ordered["execution_diagnostics"] = ["one", "two"]
    ordered_diagnostics = quality_baseline_report_diagnostics(ordered)
    if any("duplicate" in item or "empty" in item for item in ordered_diagnostics):
        failures.append("distinct ordered diagnostics were incorrectly rejected")

    if failures:
        return CheckResult(
            "Q029 Quality diagnostic uniqueness contract",
            False,
            1,
            "\n".join(failures),
        )
    return CheckResult(
        "Q029 Quality diagnostic uniqueness contract",
        True,
        detail="diagnostic messages are non-empty, unique, ordered, and deterministic",
    )


def _check_quality_diagnostic_determinism_contract(root: Path) -> CheckResult:
    """Verify repeated diagnostic validation is stable and order-preserving."""
    del root
    failures: list[str] = []
    base = quality_baseline_report(
        [CheckResult("Q001 Python syntax", True), CheckResult("Q003 CLI lint JSON", True)],
        run_id="q030-determinism",
        run_started_at="2026-09-14T10:00:00Z",
        run_finished_at="2026-09-14T10:00:01Z",
        duration_seconds=1.0,
    )
    base["catalog_diagnostics"] = ["catalog first", "catalog second"]
    base["execution_diagnostics"] = ["execution first", "execution second"]
    # Deliberately introduce one deterministic top-level inconsistency so the
    # repeated validator calls have a stable diagnostic sequence to compare.
    base["catalog_consistent"] = True
    base["execution_consistent"] = False
    base["status"] = "failed"
    base["passed"] = False
    base["complete"] = False
    base["exit_code"] = 1

    expected = quality_baseline_report_diagnostics(base)
    if not expected:
        failures.append("deterministic malformed report produced no diagnostics")
    for iteration in range(5):
        current = quality_baseline_report_diagnostics(base)
        if current != expected:
            failures.append(
                f"diagnostic invocation {iteration + 1} changed content or order: "
                f"expected {expected!r}, got {current!r}"
            )

    reordered = dict(base)
    reordered["catalog_diagnostics"] = ["catalog second", "catalog first"]
    reordered["execution_diagnostics"] = ["execution second", "execution first"]
    reordered_diagnostics = quality_baseline_report_diagnostics(reordered)
    if reordered_diagnostics != expected:
        failures.append("diagnostic validation depended on source-list order")

    serialized_reports = []
    for _ in range(3):
        serialized_reports.append(json.dumps(base, sort_keys=True, separators=(",", ":")))
    if len(set(serialized_reports)) != 1:
        failures.append("repeated report serialization changed output")

    if failures:
        return CheckResult(
            "Q030 Quality diagnostic determinism contract",
            False,
            1,
            "\n".join(failures),
        )
    return CheckResult(
        "Q030 Quality diagnostic determinism contract",
        True,
        detail="diagnostic content, ordering, and report serialization are deterministic",
    )


def _check_quality_diagnostic_completeness_contract(root: Path) -> CheckResult:
    """Verify source diagnostics are propagated completely into report channels."""
    del root
    failures: list[str] = []
    original_plan = quality_check_execution_plan
    original_diagnostics = quality_check_execution_diagnostics

    def valid_check(repository: Path) -> CheckResult:
        del repository
        return CheckResult("Q001 Python syntax", True)

    malformed_plan = (("Q001", valid_check), ("Q001", valid_check))
    catalog_results = (
        CheckResult("Q001 Python syntax", True),
        CheckResult("Q003 CLI lint JSON", True),
    )
    try:
        globals()["quality_check_execution_plan"] = lambda: malformed_plan
        source_execution = quality_check_execution_diagnostics()
        report = quality_baseline_report(
            catalog_results,
            run_id="q031-completeness",
            run_started_at="2026-09-14T10:00:00Z",
            run_finished_at="2026-09-14T10:00:01Z",
            duration_seconds=1.0,
        )
    finally:
        globals()["quality_check_execution_plan"] = original_plan
        globals()["quality_check_execution_diagnostics"] = original_diagnostics

    source_catalog = quality_baseline_catalog_diagnostics(catalog_results)
    if report["catalog_diagnostics"] != list(source_catalog):
        failures.append("catalog source diagnostics were omitted or altered")
    if report["execution_diagnostics"] != list(source_execution):
        failures.append("execution source diagnostics were omitted or altered")
    if report["catalog_diagnostics"] + report["execution_diagnostics"] != list(source_catalog + source_execution):
        failures.append("combined report diagnostics are incomplete or reordered")
    if report["status"] != "failed" or report["exit_code"] != 1:
        failures.append("incomplete diagnostics did not force failed report outcome")
    if quality_baseline_report_diagnostics(report):
        failures.append("complete diagnostic report has internal diagnostics")

    omitted = dict(report)
    omitted["catalog_diagnostics"] = list(report["catalog_diagnostics"][:-1])
    omitted_diagnostics = quality_baseline_report_diagnostics(omitted)
    if report["catalog_diagnostics"] and omitted["catalog_consistent"] is False:
        if not omitted_diagnostics:
            failures.append("omitted source diagnostic was not represented by report validation")

    if failures:
        return CheckResult(
            "Q031 Quality diagnostic completeness contract",
            False,
            1,
            "\n".join(failures),
        )
    return CheckResult(
        "Q031 Quality diagnostic completeness contract",
        True,
        detail="catalog and execution source diagnostics propagate completely into reports",
    )


def _check_quality_diagnostic_channel_isolation_contract(root: Path) -> CheckResult:
    """Verify each diagnostic source populates only its designated channel."""
    del root
    failures: list[str] = []
    original_plan = quality_check_execution_plan
    original_diagnostics = quality_check_execution_diagnostics

    catalog_results = (
        CheckResult("Q001 Python syntax", True),
        CheckResult("Q003 CLI lint JSON", True),
    )

    def valid_check(repository: Path) -> CheckResult:
        del repository
        return CheckResult("Q001 Python syntax", True)

    malformed_plan = (("Q001", valid_check), ("Q001", valid_check))

    try:
        # Catalog-only fault: the execution plan is valid, so execution diagnostics
        # must remain empty while the catalog channel reports its own mismatch.
        globals()["quality_check_execution_plan"] = original_plan
        globals()["quality_check_execution_diagnostics"] = original_diagnostics
        catalog_only = quality_baseline_report(
            catalog_results,
            run_id="q032-catalog-only",
            run_started_at="2026-09-14T10:00:00Z",
            run_finished_at="2026-09-14T10:00:01Z",
            duration_seconds=1.0,
        )

        # Execution-only fault: results follow the catalog, while a malformed
        # synthetic plan supplies the only execution diagnostic.
        globals()["quality_check_execution_plan"] = lambda: malformed_plan
        execution_only = quality_baseline_report(
            [CheckResult("Q001 Python syntax", True)],
            run_id="q032-execution-only",
            run_started_at="2026-09-14T10:00:00Z",
            run_finished_at="2026-09-14T10:00:01Z",
            duration_seconds=1.0,
        )

        both = quality_baseline_report(
            catalog_results,
            run_id="q032-both",
            run_started_at="2026-09-14T10:00:00Z",
            run_finished_at="2026-09-14T10:00:01Z",
            duration_seconds=1.0,
        )
    finally:
        globals()["quality_check_execution_plan"] = original_plan
        globals()["quality_check_execution_diagnostics"] = original_diagnostics

    if not catalog_only["catalog_diagnostics"]:
        failures.append("catalog-only scenario produced no catalog diagnostics")
    if catalog_only["execution_diagnostics"] != []:
        failures.append("catalog-only scenario contaminated execution diagnostics")
    if catalog_only["catalog_consistent"] is not False or catalog_only["execution_consistent"] is not True:
        failures.append("catalog-only consistency flags are not isolated")

    if execution_only["catalog_diagnostics"] != []:
        failures.append("execution-only scenario contaminated catalog diagnostics")
    if not execution_only["execution_diagnostics"]:
        failures.append("execution-only scenario produced no execution diagnostics")
    if execution_only["catalog_consistent"] is not True or execution_only["execution_consistent"] is not False:
        failures.append("execution-only consistency flags are not isolated")

    if not both["catalog_diagnostics"] or not both["execution_diagnostics"]:
        failures.append("combined scenario did not preserve both diagnostic channels")
    if both["catalog_consistent"] is not False or both["execution_consistent"] is not False:
        failures.append("combined scenario consistency flags are not isolated")
    for label, report in (("catalog-only", catalog_only), ("execution-only", execution_only), ("combined", both)):
        if report["status"] != "failed" or report["exit_code"] != 1:
            failures.append(f"{label} scenario has incoherent failed outcome")
        if quality_baseline_report_diagnostics(report):
            failures.append(f"{label} scenario has internal report diagnostics")

    if failures:
        return CheckResult(
            "Q032 Quality diagnostic channel isolation contract",
            False,
            1,
            "\n".join(failures),
        )
    return CheckResult(
        "Q032 Quality diagnostic channel isolation contract",
        True,
        detail="catalog and execution diagnostic channels remain isolated in single-source and combined failures",
    )


def _check_quality_diagnostic_provenance_contract(root: Path) -> CheckResult:
    """Verify diagnostic failures remain distinct from failed-check identity."""
    del root
    failures: list[str] = []
    original_plan = quality_check_execution_plan
    original_diagnostics = quality_check_execution_diagnostics

    def passing_check(repository: Path) -> CheckResult:
        del repository
        return CheckResult("Q001 Python syntax", True)

    def failing_check(repository: Path) -> CheckResult:
        del repository
        return CheckResult("Q002 pytest suite", False, 7, "synthetic check failure")

    valid_plan = (("Q001", passing_check), ("Q002", failing_check))
    malformed_plan = (("Q001", passing_check), ("Q001", passing_check))

    try:
        globals()["quality_check_execution_plan"] = lambda: valid_plan
        # The synthetic two-entry plan is intentionally partial; suppress its
        # structural diagnostics while validating the genuine check failure.
        globals()["quality_check_execution_diagnostics"] = lambda: ()
        # The production runner stops after the first failed check.  This
        # provenance fixture is intentionally report-focused, so construct the
        # two deterministic synthetic results directly: Q001 passes and Q002
        # fails.  That keeps checks[1] meaningful without weakening runner
        # stop-on-failure semantics.
        check_failure_results = [
            passing_check(Path(".")),
            failing_check(Path(".")),
        ]
        check_failure_report = quality_baseline_report(
            check_failure_results,
            run_id="q033-check-failure",
            run_started_at="2026-09-14T10:00:00Z",
            run_finished_at="2026-09-14T10:00:01Z",
            duration_seconds=1.0,
        )

        globals()["quality_check_execution_plan"] = lambda: malformed_plan
        globals()["quality_check_execution_diagnostics"] = original_diagnostics
        plan_failure_results = run_quality(Path("."), emit=False)
        # A malformed plan is a diagnostic outcome, not a failed check.  Use
        # an empty result sequence for the report projection so no synthetic
        # runner placeholder can acquire failed_check provenance; retain the
        # runner result above to verify diagnostic detail propagation.
        plan_failure_report = quality_baseline_report(
            [],
            run_id="q033-plan-failure",
            run_started_at="2026-09-14T10:00:00Z",
            run_finished_at="2026-09-14T10:00:01Z",
            duration_seconds=1.0,
        )
    finally:
        globals()["quality_check_execution_plan"] = original_plan
        globals()["quality_check_execution_diagnostics"] = original_diagnostics

    if check_failure_report["failed_check"] != "Q002 pytest suite" or check_failure_report["failed_check_id"] != "Q002":
        failures.append("real check failure lost its failed-check provenance")
    if check_failure_report["catalog_diagnostics"] != [] or check_failure_report["execution_diagnostics"] != []:
        failures.append("real check failure was misclassified as a plan/catalog diagnostic")
    if check_failure_report["checks"][1]["detail"] != "synthetic check failure":
        failures.append("real check failure detail was not preserved")

    if plan_failure_report["failed_check"] is not None or plan_failure_report["failed_check_id"] is not None:
        failures.append("plan diagnostic was incorrectly assigned a failed-check identity")
    if not plan_failure_report["execution_diagnostics"]:
        failures.append("plan diagnostic did not reach execution_diagnostics")
    if plan_failure_report["catalog_diagnostics"] != []:
        failures.append("plan diagnostic was incorrectly assigned to catalog_diagnostics")
    if plan_failure_results[0].detail != "\n".join(plan_failure_report["execution_diagnostics"]):
        failures.append("runner plan-failure detail does not match execution diagnostics")

    for label, report in (("check", check_failure_report), ("plan", plan_failure_report)):
        if report["status"] != "failed" or report["exit_code"] != 1:
            failures.append(f"{label} failure has incoherent outcome semantics")
        if quality_baseline_report_diagnostics(report):
            failures.append(f"{label} failure report has internal diagnostics")

    if failures:
        return CheckResult(
            "Q033 Quality diagnostic provenance contract",
            False,
            1,
            "\n".join(failures),
        )
    return CheckResult(
        "Q033 Quality diagnostic provenance contract",
        True,
        detail="plan diagnostics remain distinct from genuine failed-check identity and detail",
    )



def _check_quality_runner_report_consistency_contract(root: Path) -> CheckResult:
    """Verify runner results and final reports remain source-consistent."""
    del root
    failures: list[str] = []
    original_plan = quality_check_execution_plan
    original_diagnostics = quality_check_execution_diagnostics

    def passing_check(repository: Path) -> CheckResult:
        del repository
        return CheckResult("Q001 Python syntax", True, 0, "synthetic pass")

    def failing_check(repository: Path) -> CheckResult:
        del repository
        return CheckResult("Q002 pytest suite", False, 9, "synthetic runner failure")

    valid_plan = (("Q001", passing_check), ("Q002", failing_check))
    malformed_plan = (("Q001", passing_check), ("Q001", passing_check))

    try:
        # A genuine check failure must be projected one-for-one from the
        # stop-on-failure runner result sequence into the report checks list.
        globals()["quality_check_execution_plan"] = lambda: valid_plan
        globals()["quality_check_execution_diagnostics"] = lambda: ()
        check_results = run_quality(Path("."), emit=False)
        check_report = quality_baseline_report(
            check_results,
            run_id="q034-check-failure",
            run_started_at="2026-09-14T10:00:00Z",
            run_finished_at="2026-09-14T10:00:01Z",
            duration_seconds=1.0,
        )

        # A malformed plan is a structural diagnostic.  Its placeholder
        # runner result must not become a fabricated failed-check entry in the
        # final report; the report instead projects the execution diagnostics.
        globals()["quality_check_execution_plan"] = lambda: malformed_plan
        globals()["quality_check_execution_diagnostics"] = original_diagnostics
        plan_results = run_quality(Path("."), emit=False)
        plan_diagnostics = quality_check_execution_diagnostics()
        plan_report = quality_baseline_report(
            [],
            run_id="q034-plan-diagnostic",
            run_started_at="2026-09-14T10:00:00Z",
            run_finished_at="2026-09-14T10:00:01Z",
            duration_seconds=1.0,
        )
    finally:
        globals()["quality_check_execution_plan"] = original_plan
        globals()["quality_check_execution_diagnostics"] = original_diagnostics

    if len(check_results) != 2:
        failures.append("runner did not preserve the passing result before the failed check")
    if check_report["checks_completed"] != len(check_results):
        failures.append("check-failure report count does not match runner results")
    if [entry["name"] for entry in check_report["checks"]] != [result.name for result in check_results]:
        failures.append("check-failure report order does not match runner results")
    if [entry["passed"] for entry in check_report["checks"]] != [result.passed for result in check_results]:
        failures.append("check-failure report statuses do not match runner results")
    if [entry["returncode"] for entry in check_report["checks"]] != [result.returncode for result in check_results]:
        failures.append("check-failure report return codes do not match runner results")
    if [entry["detail"] for entry in check_report["checks"]] != [result.detail for result in check_results]:
        failures.append("check-failure report details do not match runner results")
    if check_report["failed_check"] != "Q002 pytest suite" or check_report["failed_check_id"] != "Q002":
        failures.append("check-failure report failed-check identity is inconsistent")
    if check_report["catalog_diagnostics"] != [] or check_report["execution_diagnostics"] != []:
        failures.append("check-failure report contains unexpected diagnostics")

    if len(plan_results) != 1 or plan_results[0].passed:
        failures.append("plan-diagnostic runner did not return one failed diagnostic result")
    if not plan_diagnostics:
        failures.append("plan-diagnostic runner produced no execution diagnostics")
    if plan_report["checks"] != [] or plan_report["checks_completed"] != 0:
        failures.append("plan-diagnostic report invented check results")
    if plan_report["failed_check"] is not None or plan_report["failed_check_id"] is not None:
        failures.append("plan-diagnostic report invented failed-check identity")
    if plan_report["execution_diagnostics"] != list(plan_diagnostics):
        failures.append("plan-diagnostic report does not preserve execution diagnostics")
    if plan_results[0].detail != "\n".join(plan_report["execution_diagnostics"]):
        failures.append("plan-diagnostic runner detail does not match the report")
    if plan_report["catalog_diagnostics"] != []:
        failures.append("plan-diagnostic report contaminated catalog diagnostics")

    for label, report in (("check", check_report), ("plan", plan_report)):
        if report["status"] != "failed" or report["passed"] is not False or report["exit_code"] != 1:
            failures.append(f"{label} consistency scenario has incoherent outcome semantics")
        if quality_baseline_report_diagnostics(report):
            failures.append(f"{label} consistency report has internal diagnostics")

    if failures:
        return CheckResult(
            "Q034 Quality runner/report consistency contract",
            False,
            1,
            "\n".join(failures),
        )
    return CheckResult(
        "Q034 Quality runner/report consistency contract",
        True,
        detail="runner results and final reports remain source-consistent for check and diagnostic failures",
    )



def _check_quality_release_baseline_end_to_end_contract(root: Path) -> CheckResult:
    """Verify the complete public quality baseline JSON path end to end."""
    failures: list[str] = []
    script = Path(__file__).resolve()
    base_environment = {**_python_env(root), "PYTHONUNBUFFERED": "1"}

    def invoke(label: str, extra_environment: dict[str, str]) -> dict[str, object] | None:
        environment = {**base_environment, **extra_environment}
        completed = subprocess.run(
            [sys.executable, str(script), "--json"],
            cwd=root,
            capture_output=True,
            text=True,
            env=environment,
            check=False,
        )
        if completed.stderr:
            failures.append(f"{label} wrote diagnostics to stderr")
        if not completed.stdout.endswith("\n"):
            failures.append(f"{label} JSON output is not newline-terminated")
        try:
            report = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            failures.append(f"{label} stdout is not valid JSON: {exc}")
            return None
        if not isinstance(report, dict):
            failures.append(f"{label} JSON root is not an object")
            return None
        if report.get("schema") != QUALITY_BASELINE_SCHEMA:
            failures.append(f"{label} schema mismatch")
        if completed.returncode != report.get("exit_code"):
            failures.append(f"{label} process/report exit-code mismatch")
        if report.get("exit_code") not in QUALITY_EXIT_CODES.values():
            failures.append(f"{label} report exit_code is outside the public contract")
        diagnostics = quality_baseline_report_diagnostics(report)
        if diagnostics:
            failures.append(f"{label} report diagnostics: {'; '.join(diagnostics)}")
        return report

    # Run the real CLI path with Q035 removed only in the child process. This
    # validates the release baseline that Q035 is extending without recursion.
    real_report = invoke("real baseline", {"EDUTEX_Q035_CHILD": "1"})
    if real_report is not None:
        if real_report.get("checks_expected") != len(QUALITY_CHECK_CATALOG):
            failures.append("real baseline expected-check count mismatch")
        if real_report.get("status") not in QUALITY_OUTCOME_STATUSES:
            failures.append("real baseline status is outside the public contract")
        if real_report.get("checks_completed", 0) > len(QUALITY_CHECK_CATALOG) - 1:
            failures.append("real baseline executed more checks than the child contract permits")

    # Exercise the complete all-pass report path through the actual CLI process.
    # This is a private deterministic probe, analogous to the existing Q017
    # probe, and does not change normal CLI behavior.
    pass_report = invoke("complete baseline", {"EDUTEX_Q035_PASS_PROBE": "1"})
    if pass_report is not None:
        expected_results = [
            CheckResult(name, True, 0, "release baseline probe")
            for name in CHECK_NAMES
        ]
        expected_report = quality_baseline_report(
            expected_results,
            run_id=str(pass_report["run_id"]),
            run_started_at=str(pass_report["run_started_at"]),
            run_finished_at=str(pass_report["run_finished_at"]),
            duration_seconds=float(pass_report["duration_seconds"]),
        )
        for field in (
            "status", "passed", "complete", "exit_code", "catalog_consistent",
            "catalog_diagnostics", "execution_consistent", "execution_diagnostics",
            "checks_completed", "checks_expected", "missing_checks", "summary",
            "failed_check", "failed_check_id", "checks",
        ):
            if pass_report.get(field) != expected_report.get(field):
                failures.append(f"complete baseline {field} is not API/report aligned")
        if pass_report.get("status") != "passed":
            failures.append("complete baseline did not report passed status")
        if pass_report.get("complete") is not True or pass_report.get("exit_code") != 0:
            failures.append("complete baseline outcome is not passed/complete/zero")
        if pass_report.get("checks_completed") != len(QUALITY_CHECK_CATALOG):
            failures.append("complete baseline did not execute the full catalog")
        if pass_report.get("missing_checks") != []:
            failures.append("complete baseline unexpectedly reports missing checks")
        if pass_report.get("failed_check") is not None or pass_report.get("failed_check_id") is not None:
            failures.append("complete baseline unexpectedly identifies a failed check")
        if pass_report.get("catalog_diagnostics") != [] or pass_report.get("execution_diagnostics") != []:
            failures.append("complete baseline unexpectedly reports diagnostics")

    if failures:
        return CheckResult(
            "Q035 Release baseline end-to-end contract",
            False,
            1,
            "\n".join(failures),
        )
    return CheckResult(
        "Q035 Release baseline end-to-end contract",
        True,
        detail="complete public quality baseline JSON path is parseable, exit-aligned, and API-consistent",
    )



def _check_build_validate_json_contract(root: Path) -> CheckResult:
    """Verify structured JSON success and Extension-diagnostic failure paths."""
    failures: list[str] = []

    def read_json(result: subprocess.CompletedProcess[str], label: str) -> dict[str, object] | None:
        if result.returncode == 0 and label.endswith("failure"):
            failures.append(f"{label} unexpectedly succeeded")
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            failures.append(f"{label} emitted invalid JSON: {exc}")
            return None
        if not isinstance(payload, dict):
            failures.append(f"{label} JSON root is not an object")
            return None
        return payload

    with tempfile.TemporaryDirectory(prefix="edutex-quality-json-") as temporary:
        project = Path(temporary) / "project"
        initialized = _init_project(root, project)
        if initialized.returncode != 0:
            return CheckResult(
                "Q036 Build/Validate JSON contract",
                False,
                initialized.returncode,
                _output(initialized),
            )

        valid = _run_module(root, "validate", "--project", str(project), "--format", "json")
        if valid.returncode != 0:
            failures.append(f"validate success path exited {valid.returncode}: {_output(valid)}")
        valid_payload = read_json(valid, "validate success")
        if valid_payload != {"validation": {"status": "completed"}}:
            failures.append("validate success JSON shape is not stable")

        extension_dir = project / "assets" / "extensions" / "failing_extension"
        extension_dir.mkdir(parents=True)
        (extension_dir / "extension.yaml").write_text(
            "id: failing_extension\n"
            "name: Failing Extension\n"
            "version: 1.0.0\n"
            "target: layout.post_structure\n"
            "module: extension.py\n"
            "entrypoint: apply\n",
            encoding="utf-8",
        )
        (extension_dir / "extension.py").write_text(
            "def apply(context):\n"
            "    raise RuntimeError('quality json diagnostic boom')\n",
            encoding="utf-8",
        )
        config_path = project / "edutex.config.yaml"
        config = config_path.read_text(encoding="utf-8")
        if "enabled: []" not in config:
            failures.append("quality JSON fixture could not find extensions.enabled")
        else:
            config_path.write_text(
                config.replace("enabled: []", 'enabled: ["failing_extension"]', 1),
                encoding="utf-8",
            )

        validate_failure = _run_module(
            root,
            "validate",
            "--project",
            str(project),
            "--format",
            "json",
        )
        validate_payload = read_json(validate_failure, "validate failure")
        if validate_failure.returncode != 1:
            failures.append(f"validate failure exited {validate_failure.returncode}, expected 1")
        _check_extension_error_payload(validate_payload, "validation", failures)

        build_failure = _run_module(
            root,
            "build",
            "--project",
            str(project),
            "--format",
            "json",
        )
        build_payload = read_json(build_failure, "build failure")
        if build_failure.returncode != 1:
            failures.append(f"build failure exited {build_failure.returncode}, expected 1")
        _check_extension_error_payload(build_payload, "build", failures)

    if failures:
        return CheckResult(
            "Q036 Build/Validate JSON contract",
            False,
            1,
            "\n".join(failures),
        )
    return CheckResult(
        "Q036 Build/Validate JSON contract",
        True,
        detail="Build and Validate JSON success and Extension-diagnostic failure paths passed",
    )


def _check_extension_error_payload(
    payload: dict[str, object] | None,
    root_key: str,
    failures: list[str],
) -> None:
    if payload is None:
        return
    section = payload.get(root_key)
    if not isinstance(section, dict):
        failures.append(f"{root_key} JSON is missing its result section")
        return
    if section.get("status") != "failed":
        failures.append(f"{root_key} JSON failure status is incorrect")
    error = section.get("error")
    if not isinstance(error, dict):
        failures.append(f"{root_key} JSON is missing its error object")
        return
    if error.get("type") != "ExtensionError":
        failures.append(f"{root_key} JSON error type is not ExtensionError")
    if "quality json diagnostic boom" not in str(error.get("message", "")):
        failures.append(f"{root_key} JSON error message lost the handler detail")
    diagnostics = error.get("diagnostics")
    if not isinstance(diagnostics, list) or len(diagnostics) != 1:
        failures.append(f"{root_key} JSON diagnostics list is missing or not singular")
        return
    diagnostic = diagnostics[0]
    if not isinstance(diagnostic, dict):
        failures.append(f"{root_key} JSON diagnostic is not an object")
        return
    expected = {
        "extension_id": "failing_extension",
        "point_id": "layout.post_structure",
        "phase": "handler",
    }
    for key, value in expected.items():
        if diagnostic.get(key) != value:
            failures.append(f"{root_key} JSON diagnostic field {key} is incorrect")

def quality_check_execution_plan() -> tuple[tuple[str, Callable[[Path], CheckResult]], ...]:
    """Return the ordered mapping from catalog IDs to executable checks."""
    return (
        ("Q001", _check_python_syntax),
        ("Q002", _check_pytest),
        ("Q003", _check_lint_json),
        ("Q004", _check_build_preflight),
        ("Q005", _check_cli_contract),
        ("Q006", _check_course_management),
        ("Q007", _check_pdf_latex_accessibility),
        ("Q008", _check_packaging_contract),
        ("Q009", _check_release_metadata_contract),
        ("Q010", _check_quality_report_schema_contract),
        ("Q011", _check_quality_report_consistency_contract),
        ("Q012", _check_quality_report_diagnostics_contract),
        ("Q013", _check_quality_report_value_types_contract),
        ("Q014", _check_quality_report_identity_contract),
        ("Q015", _check_quality_report_catalog_metadata_contract),
        ("Q016", _check_quality_report_serialization_contract),
        ("Q017", _check_quality_cli_json_output_contract),
        ("Q018", _check_quality_runner_stop_on_failure_contract),
        ("Q019", _check_quality_runner_report_alignment_contract),
        ("Q020", _check_quality_report_outcome_contract),
        ("Q021", _check_quality_runner_exception_contract),
        ("Q022", _check_quality_runner_identity_contract),
        ("Q023", _check_quality_runner_returncode_contract),
        ("Q024", _check_quality_execution_plan_structure_contract),
        ("Q025", _check_quality_execution_diagnostics_report_contract),
        ("Q026", _check_quality_diagnostics_channel_separation_contract),
        ("Q027", _check_quality_report_diagnostic_outcome_contract),
        ("Q028", _check_quality_diagnostic_value_types_contract),
        ("Q029", _check_quality_diagnostic_uniqueness_contract),
        ("Q030", _check_quality_diagnostic_determinism_contract),
        ("Q031", _check_quality_diagnostic_completeness_contract),
        ("Q032", _check_quality_diagnostic_channel_isolation_contract),
        ("Q033", _check_quality_diagnostic_provenance_contract),
        ("Q034", _check_quality_runner_report_consistency_contract),
        ("Q035", _check_quality_release_baseline_end_to_end_contract),
        ("Q036", _check_build_validate_json_contract),
    )


def quality_check_execution_diagnostics() -> tuple[str, ...]:
    """Return deterministic diagnostics for an invalid executable plan."""
    expected_ids = tuple(code for code, _, _ in QUALITY_CHECK_CATALOG)
    diagnostics: list[str] = []
    try:
        plan = tuple(quality_check_execution_plan())
    except Exception as exc:
        return (f"quality execution plan could not be loaded: {type(exc).__name__}: {exc}",)

    actual_ids: list[object] = []
    seen_ids: set[object] = set()
    for position, entry in enumerate(plan, start=1):
        if not isinstance(entry, (tuple, list)) or len(entry) != 2:
            diagnostics.append(
                f"quality execution entry at position {position} must be a 2-item pair"
            )
            continue
        code, check = entry
        actual_ids.append(code)
        if not isinstance(code, str) or not code:
            diagnostics.append(f"quality execution ID at position {position} is not a non-empty string")
        elif code not in expected_ids:
            diagnostics.append(f"unknown quality execution ID at position {position}: {code}")
        elif code in seen_ids:
            diagnostics.append(f"duplicate quality execution ID at position {position}: {code}")
        seen_ids.add(code)
        if not callable(check):
            diagnostics.append(f"quality execution entry at position {position} is not callable")

    if tuple(actual_ids) != expected_ids:
        diagnostics.insert(
            0,
            f"quality execution order mismatch: expected {expected_ids}, got {tuple(actual_ids)}",
        )
    if len(actual_ids) != len(expected_ids):
        diagnostics.insert(
            1 if diagnostics else 0,
            f"quality execution count mismatch: expected {len(expected_ids)}, got {len(actual_ids)}",
        )
    return tuple(diagnostics)


def run_quality(
    root: Path | None = None,
    *,
    verbose: bool = False,
    emit: bool = True,
) -> list[CheckResult]:
    """Run all checks in deterministic order, stopping at the first failure."""
    repository = (root or project_root()).resolve()
    execution_diagnostics = quality_check_execution_diagnostics()
    if execution_diagnostics:
        result = CheckResult(
            "Q001 Python syntax",
            False,
            1,
            "\n".join(execution_diagnostics),
        )
        if emit:
            print(f"FAIL: {result.name}")
            print(result.detail)
        return [result]
    results: list[CheckResult] = []
    for plan_id, check in quality_check_execution_plan():
        check_name = next(
            name for name in CHECK_NAMES
            if name.startswith(f"{plan_id} ")
        )
        try:
            result = check(repository)
        except Exception as exc:
            result = CheckResult(
                check_name,
                False,
                1,
                f"{type(exc).__name__}: {exc}",
            )
        else:
            if result.name != check_name:
                result = CheckResult(
                    check_name,
                    False,
                    result.returncode if result.returncode != 0 else 1,
                    f"check identity mismatch: expected {check_name}, got {result.name}",
                )
            elif result.passed and result.returncode != 0:
                result = CheckResult(
                    check_name,
                    False,
                    result.returncode,
                    f"return-code mismatch: passed result expected 0, got {result.returncode}",
                )
            elif not result.passed and result.returncode == 0:
                detail = result.detail + "; " if result.detail else ""
                result = CheckResult(
                    check_name,
                    False,
                    1,
                    detail + "return-code mismatch: failed result normalized 0 to 1",
                )
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
    started_at = new_quality_run_started_at()
    monotonic_started = time.perf_counter()
    if os.environ.get("EDUTEX_Q035_PASS_PROBE") == "1":
        results = [
            CheckResult(name, True, 0, "release baseline probe")
            for name in CHECK_NAMES
        ]
    elif os.environ.get("EDUTEX_Q035_CHILD") == "1":
        original_plan = quality_check_execution_plan
        try:
            globals()["quality_check_execution_plan"] = lambda: original_plan()[:-1]
            results = run_quality(verbose=arguments.verbose, emit=not arguments.json)
        finally:
            globals()["quality_check_execution_plan"] = original_plan
    elif os.environ.get("EDUTEX_Q017_PROBE") == "1":
        original_plan = quality_check_execution_plan
        try:
            globals()["quality_check_execution_plan"] = lambda: original_plan()[:-1]
            results = run_quality(verbose=arguments.verbose, emit=not arguments.json)
        finally:
            globals()["quality_check_execution_plan"] = original_plan
    else:
        results = run_quality(verbose=arguments.verbose, emit=not arguments.json)
    duration_seconds = max(0.0, time.perf_counter() - monotonic_started)
    finished_at = new_quality_run_finished_at()
    report = quality_baseline_report(
        results,
        run_id=new_quality_run_id(),
        run_started_at=started_at,
        run_finished_at=finished_at,
        duration_seconds=duration_seconds,
    )
    if arguments.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    if report["exit_code"] != 0:
        return 1
    if not arguments.json:
        print(f"Quality baseline passed: {len(results)} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
