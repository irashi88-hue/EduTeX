"""Run EduTeX's local quality baseline without network access."""

from __future__ import annotations

import argparse
import json
import os
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

        blocked_json = _run_module(
            root,
            "build",
            "--project",
            str(error_project),
            "--lint",
            "--format",
            "json",
        )
        if blocked_json.returncode != 1:
            return CheckResult("Q004 build lint preflight", False, blocked_json.returncode or 1, _output(blocked_json))
        try:
            blocked_payload = json.loads(blocked_json.stdout)
        except json.JSONDecodeError as exc:
            return CheckResult("Q004 build lint preflight", False, 1, f"invalid build JSON: {exc}")
        if (
            blocked_payload.get("lint", {}).get("valid") is not False
            or blocked_payload.get("build", {}).get("status") != "blocked"
        ):
            return CheckResult("Q004 build lint preflight", False, 1, "invalid blocked build JSON contract")

        warning_project = directory / "warning-project"
        initialized = _init_project(root, warning_project)
        if initialized.returncode != 0:
            return CheckResult("Q004 build lint preflight", False, initialized.returncode, _output(initialized))
        _replace_model(warning_project, "::: exercise\nWrite a sentence.\n:::\n")
        warning_build = _run_module(
            root,
            "build",
            "--project",
            str(warning_project),
            "--lint",
            "--format",
            "json",
        )
        if warning_build.returncode != 0 or not (warning_project / "output" / "document.html").exists():
            return CheckResult("Q004 build lint preflight", False, warning_build.returncode or 1, _output(warning_build))
        try:
            warning_payload = json.loads(warning_build.stdout)
        except json.JSONDecodeError as exc:
            return CheckResult("Q004 build lint preflight", False, 1, f"invalid build JSON: {exc}")
        if (
            warning_payload.get("lint", {}).get("warnings", [{}])[0].get("code") != "SC201"
            or warning_payload.get("build", {}).get("status") != "completed"
        ):
            return CheckResult("Q004 build lint preflight", False, 1, "invalid warning build JSON contract")

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
        (("build", "--help"), ("--lint", "--format")),
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


def run_quality(root: Path | None = None, *, verbose: bool = False) -> list[CheckResult]:
    """Run all checks in deterministic order, stopping at the first failure."""
    repository = (root or project_root()).resolve()
    checks = (
        _check_python_syntax,
        _check_pytest,
        _check_lint_json,
        _check_build_preflight,
        _check_cli_contract,
    )
    results: list[CheckResult] = []
    for check in checks:
        result = check(repository)
        results.append(result)
        status = "PASS" if result.passed else "FAIL"
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
    arguments = parser.parse_args(argv)
    results = run_quality(verbose=arguments.verbose)
    if not results or not results[-1].passed:
        return 1
    print(f"Quality baseline passed: {len(results)} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
