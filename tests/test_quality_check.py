"""Unit tests for the EduTeX quality baseline runner."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from tools.quality_check import (
    check_names,
    public_cli_contract,
    quality_baseline_catalog_diagnostics,
    quality_baseline_missing_checks,
    quality_baseline_report_diagnostics,
    quality_baseline_summary,
    quality_check_id,
    quality_check_catalog,
    quality_check_execution_diagnostics,
    quality_check_execution_plan,
    packaging_contract,
    release_metadata_contract,
    quality_report_contract,
    run_command,
)


def completed(returncode: int, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["fake"], returncode, stdout, stderr)


def test_quality_check_names_are_stable_and_unique() -> None:
    names = check_names()

    assert names
    assert names == (
        "Q001 Python syntax",
        "Q002 pytest suite",
        "Q003 CLI lint JSON",
        "Q004 build lint preflight",
        "Q005 CLI contract",
        "Q006 Course management contract",
        "Q007 PDF/LaTeX accessibility contract",
        "Q008 Packaging contract",
        "Q009 Release metadata contract",
        "Q010 Quality report schema contract",
        "Q011 Quality report consistency contract",
        "Q012 Quality report diagnostics contract",
        "Q013 Quality report value-types contract",
        "Q014 Quality report identity contract",
        "Q015 Quality report catalog metadata contract",
        "Q016 Quality report serialization contract",
        "Q017 Quality CLI JSON output contract",
        "Q018 Quality runner stop-on-failure contract",
        "Q019 Quality runner/report alignment contract",
        "Q020 Quality report outcome contract",
        "Q021 Quality runner exception contract",
        "Q022 Quality runner identity contract",
        "Q023 Quality runner return-code contract",
        "Q024 Quality execution-plan structure contract",
        "Q025 Quality execution diagnostics/report contract",
        "Q026 Quality diagnostics channel separation contract",
        "Q027 Quality report diagnostic outcome contract",
        "Q028 Quality diagnostic value-types contract",
        "Q029 Quality diagnostic uniqueness contract",
        "Q030 Quality diagnostic determinism contract",
        "Q031 Quality diagnostic completeness contract",
        "Q032 Quality diagnostic channel isolation contract",
        "Q033 Quality diagnostic provenance contract",
        "Q034 Quality runner/report consistency contract",
        "Q035 Release baseline end-to-end contract",
        "Q036 Build/Validate JSON contract",
    )
    assert len(names) == len(set(names))



def test_quality_check_catalog_is_stable_unique_and_complete() -> None:
    catalog = quality_check_catalog()

    assert tuple(entry["name"] for entry in catalog) == check_names()
    assert tuple(entry["id"] for entry in catalog) == (
        "Q001", "Q002", "Q003", "Q004", "Q005", "Q006", "Q007", "Q008", "Q009", "Q010", "Q011", "Q012", "Q013", "Q014", "Q015", "Q016", "Q017", "Q018", "Q019", "Q020", "Q021", "Q022", "Q023", "Q024", "Q025", "Q026", "Q027", "Q028", "Q029", "Q030", "Q031", "Q032", "Q033", "Q034", "Q035", "Q036"
    )
    assert len({entry["id"] for entry in catalog}) == len(catalog)
    assert len({entry["name"] for entry in catalog}) == len(catalog)
    assert all(entry["required"] is True for entry in catalog)
    assert all(entry["description"] for entry in catalog)


def test_quality_execution_plan_matches_catalog_order() -> None:
    plan = quality_check_execution_plan()

    assert tuple(code for code, _ in plan) == (
        "Q001", "Q002", "Q003", "Q004", "Q005", "Q006", "Q007", "Q008", "Q009", "Q010", "Q011", "Q012", "Q013", "Q014", "Q015", "Q016", "Q017", "Q018", "Q019", "Q020", "Q021", "Q022", "Q023", "Q024", "Q025", "Q026", "Q027", "Q028", "Q029", "Q030", "Q031", "Q032", "Q033", "Q034", "Q035", "Q036"
    )
    assert quality_check_execution_diagnostics() == ()
    assert all(callable(check) for _, check in plan)


def test_public_cli_contract_is_stable_and_ordered() -> None:
    assert public_cli_contract() == (
        (("--help",), ("init", "lint", "build", "inspect", "validate")),
        (("init", "--help"), ("--theme", "--language")),
        (("lint", "--help"), ("--format",)),
        (("build", "--help"), ("--lint", "--profile")),
        (("inspect", "--help"), ("--project", "--config", "--format", "--profile")),
        (("validate", "--help"), ("--project", "--config", "--format", "--profile")),
        (("course", "build", "--help"), ("--profile",)),
    )


def test_packaging_contract_is_stable_and_covers_cli_surface() -> None:
    contract = dict(packaging_contract())

    assert "src/edutex/core/cli.py" in contract
    assert "pyproject.toml" in contract
    assert 'CLI_VERSION = "1.0.0"' in contract["src/edutex/core/cli.py"]
    assert '@main.group("course")' in contract["src/edutex/core/cli.py"]
    assert "def _format_build_error_json" in contract["src/edutex/core/cli.py"]


def test_packaging_contract_reports_obsolete_cli(tmp_path: Path) -> None:
    from tools.quality_check import _check_packaging_contract

    cli = tmp_path / "src" / "edutex" / "core"
    cli.mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text(
        '[project.scripts]\n'
        'edutex = "edutex.core.cli:main"\n'
        '[tool.setuptools.packages.find]\n',
        encoding="utf-8",
    )
    (cli / "cli.py").write_text(
        'CLI_VERSION = "0.1.0"\n'
        '@main.command("init")\n',
        encoding="utf-8",
    )

    result = _check_packaging_contract(tmp_path)

    assert not result.passed
    assert "obsolete CLI_VERSION 0.1.0" in result.detail
    assert "missing packaging markers" in result.detail


def test_release_metadata_contract_is_stable() -> None:
    assert release_metadata_contract() == (
        "pyproject.toml",
        "src/edutex/core/cli.py",
        'edutex = "edutex.core.cli:main"',
    )


def _write_release_metadata_fixture(root: Path, *, project_version: str = "0.3.0", cli_version: str = "0.3.0", entrypoint: str = "edutex.core.cli:main") -> None:
    cli = root / "src" / "edutex" / "core"
    cli.mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        "[project]\n"
        f"version = \"{project_version}\"\n\n"
        "[project.scripts]\n"
        f"edutex = \"{entrypoint}\"\n",
        encoding="utf-8",
    )
    (cli / "cli.py").write_text(
        f"CLI_VERSION = \"{cli_version}\"\n",
        encoding="utf-8",
    )


def test_release_metadata_contract_accepts_coherent_metadata(tmp_path: Path) -> None:
    from tools.quality_check import _check_release_metadata_contract

    _write_release_metadata_fixture(tmp_path)

    result = _check_release_metadata_contract(tmp_path)

    assert result.passed
    assert "version 0.3.0" in result.detail


def test_release_metadata_contract_reports_version_mismatch(tmp_path: Path) -> None:
    from tools.quality_check import _check_release_metadata_contract

    _write_release_metadata_fixture(tmp_path, cli_version="0.3.1")

    result = _check_release_metadata_contract(tmp_path)

    assert not result.passed
    assert "release version mismatch" in result.detail


def test_release_metadata_contract_reports_missing_or_invalid_versions(tmp_path: Path) -> None:
    from tools.quality_check import _check_release_metadata_contract

    _write_release_metadata_fixture(tmp_path, project_version="not-a-version")
    result = _check_release_metadata_contract(tmp_path)

    assert not result.passed
    assert "invalid release version in pyproject.toml" in result.detail

    (tmp_path / "pyproject.toml").write_text(
        "[project]\n\n[project.scripts]\n"
        'edutex = "edutex.core.cli:main"\n',
        encoding="utf-8",
    )
    result = _check_release_metadata_contract(tmp_path)

    assert not result.passed
    assert "missing [project] version" in result.detail


def test_release_metadata_contract_reports_entrypoint_mismatch(tmp_path: Path) -> None:
    from tools.quality_check import _check_release_metadata_contract

    _write_release_metadata_fixture(tmp_path, entrypoint="edutex.legacy:main")

    result = _check_release_metadata_contract(tmp_path)

    assert not result.passed
    assert "project entry point mismatch" in result.detail


def test_pdf_latex_source_contract_accepts_accessible_source() -> None:
    from tools.quality_check import PDF_LATEX_MARKERS, _validate_pdf_latex_source

    source = "\n".join(PDF_LATEX_MARKERS)

    assert _validate_pdf_latex_source(source) is None


def test_pdf_latex_source_contract_reports_missing_marker() -> None:
    from tools.quality_check import PDF_LATEX_MARKERS, _validate_pdf_latex_source

    source = "\n".join(PDF_LATEX_MARKERS[:-1])

    assert _validate_pdf_latex_source(source) == (
        "LaTeX accessibility marker missing: pdflang={"
    )

def test_pdf_compiler_selection_supports_cjk_fallbacks(monkeypatch) -> None:
    from tools import quality_check

    available = {"xelatex"}
    monkeypatch.setattr(quality_check.shutil, "which", lambda name: name if name in available else None)

    assert quality_check._available_course_pdf_compiler("ja") == "xelatex"
    assert quality_check._available_course_pdf_compiler("en") is None


def test_latexmk_version_normalization_ignores_windows_wrapper_preamble() -> None:
    from tools.quality_check import _normalize_tool_version

    output = """This is a Perl script wrapper initialization line.
Latexmk: This is Latexmk, John Collins, 4.85.
"""

    assert _normalize_tool_version("latexmk", output) == "latexmk version 4.85"


def test_latexmk_version_probe_normalizes_semantic_line(monkeypatch) -> None:
    from tools import quality_check

    monkeypatch.setattr(quality_check.shutil, "which", lambda name: "C:/MiKTeX/latexmk.exe")
    monkeypatch.setattr(
        quality_check.subprocess,
        "run",
        lambda *args, **kwargs: completed(
            0,
            "Perl wrapper startup\nLatexmk: This is Latexmk, John Collins, 4.86.\n",
        ),
    )

    assert quality_check._tool_version("latexmk") == "latexmk version 4.86"



def test_pypdf_gate_reports_missing_optional_dependency(tmp_path: Path, monkeypatch) -> None:
    from tools import quality_check

    pdf_path = tmp_path / "course.pdf"
    pdf_path.write_bytes(b"not a real pdf")
    monkeypatch.setattr(quality_check, "_pypdf_available", lambda: False)

    status, diagnostic = quality_check._pypdf_gate_result(
        pdf_path,
        expected_language="en-US",
    )

    assert status == "skipped_unavailable"
    assert diagnostic == "pypdf is not installed"


def test_pypdf_gate_reports_parser_failure(tmp_path: Path, monkeypatch) -> None:
    from tools import quality_check

    pdf_path = tmp_path / "course.pdf"
    pdf_path.write_bytes(b"not a real pdf")
    monkeypatch.setattr(quality_check, "_pypdf_available", lambda: True)
    monkeypatch.setattr(
        quality_check,
        "_validate_pdf_parser",
        lambda path, *, expected_language: "pypdf parser failed: malformed PDF",
    )

    status, diagnostic = quality_check._pypdf_gate_result(
        pdf_path,
        expected_language="en-US",
    )

    assert status == "failed"
    assert diagnostic == "pypdf parser failed: malformed PDF"


def test_expected_pdf_language_normalization_preserves_explicit_tags() -> None:
    from tools import quality_check

    assert quality_check._normalize_expected_pdf_language("en") == "en-US"
    assert quality_check._normalize_expected_pdf_language("it_IT") == "it-IT"
    assert quality_check._normalize_expected_pdf_language("ja") == "ja"


def test_pypdf_gate_accepts_configurable_non_english_language(tmp_path: Path, monkeypatch) -> None:
    from tools import quality_check

    pdf_path = tmp_path / "course.pdf"
    pdf_path.write_bytes(b"valid fixture")
    observed: list[str] = []
    monkeypatch.setattr(quality_check, "_pypdf_available", lambda: True)

    def validate(path, *, expected_language):
        observed.append(expected_language)
        return None

    monkeypatch.setattr(quality_check, "_validate_pdf_parser", validate)

    status, diagnostic = quality_check._pypdf_gate_result(
        pdf_path,
        expected_language="it-IT",
    )

    assert status == "passed"
    assert diagnostic is None
    assert observed == ["it-IT"]


def test_pypdf_gate_reports_configurable_language_mismatch(tmp_path: Path, monkeypatch) -> None:
    from tools import quality_check

    pdf_path = tmp_path / "course.pdf"
    pdf_path.write_bytes(b"valid fixture")
    monkeypatch.setattr(quality_check, "_pypdf_available", lambda: True)
    monkeypatch.setattr(
        quality_check,
        "_validate_pdf_parser",
        lambda path, *, expected_language: (
            f"PDF language mismatch: expected {expected_language!r}, got 'en-US'"
        ),
    )

    status, diagnostic = quality_check._pypdf_gate_result(
        pdf_path,
        expected_language="it-IT",
    )

    assert status == "failed"
    assert diagnostic == "PDF language mismatch: expected 'it-IT', got 'en-US'"


def test_pdf_inspection_gates_forward_expected_language(tmp_path: Path, monkeypatch) -> None:
    from tools import quality_check

    pdf_path = tmp_path / "course.pdf"
    pdf_path.write_bytes(b"valid fixture")
    monkeypatch.setattr(quality_check.shutil, "which", lambda name: None)
    observed: list[str] = []

    def fake_gate(path, *, expected_language):
        observed.append(expected_language)
        return "passed", None

    monkeypatch.setattr(quality_check, "_pypdf_gate_result", fake_gate)

    statuses, failures = quality_check._run_pdf_inspection_gates(
        pdf_path,
        tmp_path,
        expected_language="it-IT",
    )

    assert statuses["pypdf"] == "passed"
    assert failures == []
    assert observed == ["it-IT"]


def test_pypdf_gate_reports_success(tmp_path: Path, monkeypatch) -> None:
    from tools import quality_check

    pdf_path = tmp_path / "course.pdf"
    pdf_path.write_bytes(b"valid fixture")
    monkeypatch.setattr(quality_check, "_pypdf_available", lambda: True)
    monkeypatch.setattr(quality_check, "_validate_pdf_parser", lambda *args, **kwargs: None)

    status, diagnostic = quality_check._pypdf_gate_result(
        pdf_path,
        expected_language="en-US",
    )

    assert status == "passed"
    assert diagnostic is None


def test_pdf_inspection_gates_report_all_unavailable_tools(tmp_path: Path, monkeypatch) -> None:
    from tools import quality_check

    pdf_path = tmp_path / "course.pdf"
    pdf_path.write_bytes(b"not a real pdf")
    monkeypatch.setattr(quality_check.shutil, "which", lambda name: None)
    monkeypatch.setattr(quality_check, "_pypdf_available", lambda: False)
    monkeypatch.setattr(quality_check, "_validate_pdf_parser", lambda *args, **kwargs: None)

    statuses, failures = quality_check._run_pdf_inspection_gates(pdf_path, tmp_path)

    assert statuses == {
        "qpdf": "skipped_unavailable",
        "pdftotext": "skipped_unavailable",
        "pdfinfo": "skipped_unavailable",
        "pypdf": "skipped_unavailable",
        "pdftoppm": "skipped_unavailable",
    }
    assert failures == []


def test_pdf_inspection_gates_pass_text_metadata_and_render(tmp_path: Path, monkeypatch) -> None:
    from tools import quality_check

    output = tmp_path / "output"
    output.mkdir()
    pdf_path = output / "course.pdf"
    pdf_path.write_bytes(b"fake pdf")
    available = {"qpdf", "pdftotext", "pdfinfo", "pdftoppm"}
    monkeypatch.setattr(quality_check.shutil, "which", lambda name: name if name in available else None)
    monkeypatch.setattr(quality_check, "_pypdf_available", lambda: False)
    monkeypatch.setattr(quality_check, "_validate_pdf_parser", lambda *args, **kwargs: None)

    def fake_runner(command, cwd):
        tool = command[0]
        if tool == "pdftotext":
            Path(command[2]).write_text("Quality Course\n", encoding="utf-8")
        elif tool == "pdftoppm":
            Path(command[-1] + ".png").write_bytes(b"png")
        if tool == "pdfinfo":
            return completed(0, "Title: Quality Course\nAuthor: EduTeX\nSubject: EduTeX course roadmap\n")
        return completed(0)

    monkeypatch.setattr(quality_check, "run_subprocess", fake_runner)

    statuses, failures = quality_check._run_pdf_inspection_gates(pdf_path, tmp_path)

    assert statuses["qpdf"] == "passed"
    assert statuses["pdftotext"] == "passed"
    assert statuses["pdfinfo"] == "passed"
    assert statuses["pypdf"] == "skipped_unavailable"
    assert statuses["pdftoppm"] == "passed"
    assert failures == []


def test_pdf_inspection_gates_report_failed_gate_and_diagnostic(tmp_path: Path, monkeypatch) -> None:
    from tools import quality_check

    output = tmp_path / "output"
    output.mkdir()
    pdf_path = output / "course.pdf"
    pdf_path.write_bytes(b"fake pdf")
    monkeypatch.setattr(quality_check.shutil, "which", lambda name: name if name == "qpdf" else None)

    monkeypatch.setattr(
        quality_check,
        "run_subprocess",
        lambda command, cwd: completed(2, "", "malformed xref table"),
    )

    statuses, failures = quality_check._run_pdf_inspection_gates(pdf_path, tmp_path)

    assert statuses["qpdf"] == "failed"
    assert "qpdf --check failed" in failures[0]
    assert "malformed xref table" in failures[0]


def test_pdf_runtime_report_is_json_safe_and_role_aware(monkeypatch) -> None:
    from tools import quality_check

    available = {"qpdf", "pdftotext"}
    monkeypatch.setattr(quality_check.shutil, "which", lambda name: f"/bin/{name}" if name in available else None)
    monkeypatch.setattr(quality_check, "_tool_version", lambda name: f"{name} test-version")

    report = quality_check.pdf_runtime_report("en-US")
    assert report["schema"] == "edutex.pdf-runtime.v1"
    assert report["compiled_pdf_status"] == "skipped_no_compiler"
    assert report["inspection_available"] is True
    assert report["tools"]["qpdf"]["role"] == "structural-validator"
    assert report["tools"]["pdftotext"]["version"] == "pdftotext test-version"
    assert report["tools"]["latexmk"]["available"] is False
    assert report["missing_gates"] == []
    assert report["inspection_gates"]["qpdf"]["status"] == "available"
    assert report["inspection_gates"]["pdfinfo"]["status"] == "unavailable_optional"
    assert report["inspection_gates"]["pypdf"]["role"] == "parser"
    assert report["inspection_gates"]["pypdf"]["status"] in {"available", "unavailable_optional"}
    assert "diagnostic" in report["inspection_gates"]["pypdf"]


def test_pdf_tool_status_and_runtime_summary(monkeypatch) -> None:
    from tools import quality_check

    available = {"xelatex", "qpdf", "pdftotext"}
    monkeypatch.setattr(quality_check.shutil, "which", lambda name: name if name in available else None)

    status = quality_check.pdf_tool_status()
    assert status["xelatex"] is True
    assert status["qpdf"] is True
    assert status["pdfinfo"] is False
    summary = quality_check.pdf_runtime_summary("ja")
    assert summary["compiler"] == "xelatex"
    assert summary["language"] == "ja"
    assert summary["language_code"] == "ja"
    assert summary["compiler_ready"] is True
    assert summary["required_compiler_tools"] == ["xelatex"]
    assert summary["compiled_pdf_checks"] is True
    assert summary["compiled_pdf_status"] == "ready"
    assert summary["inspection_gates"]["qpdf"] == "available"
    assert summary["missing_gates"] == []


def test_pdf_runtime_summary_matches_report_fields(monkeypatch) -> None:
    from tools import quality_check

    available = {"pdftotext", "pdfinfo", "pdftoppm"}
    monkeypatch.setattr(quality_check.shutil, "which", lambda name: f"/bin/{name}" if name in available else None)
    monkeypatch.setattr(quality_check, "_pypdf_available", lambda: False)
    monkeypatch.setattr(quality_check, "_tool_version", lambda name: f"{name} test-version")

    report = quality_check.pdf_runtime_report("en-US")
    summary = quality_check.pdf_runtime_summary("en-US")

    assert summary["language"] == report["language"]
    assert summary["language_code"] == report["language_code"]
    assert summary["compiler"] == report["compiler"]
    assert summary["compiler_ready"] == report["compiler_ready"]
    assert summary["required_compiler_tools"] == report["required_compiler_tools"]
    assert summary["compiled_pdf_status"] == report["compiled_pdf_status"]
    assert summary["missing_gates"] == report["missing_gates"]
    assert summary["inspection_gates"] == {
        name: gate["status"] for name, gate in report["inspection_gates"].items()
    }


def test_pdfinfo_parser_and_metadata_contract() -> None:
    from tools.quality_check import _pdfinfo_fields, _validate_pdf_metadata

    output = """Title:           Quality Course
Author:          EduTeX
Subject:         EduTeX course roadmap
Pages:           2
"""
    fields = _pdfinfo_fields(output)
    assert fields["Title"] == "Quality Course"
    assert _validate_pdf_metadata(
        fields,
        title="Quality Course",
        author="EduTeX",
        subject="EduTeX course roadmap",
    ) is None


def test_pdf_metadata_contract_reports_mismatch() -> None:
    from tools.quality_check import _validate_pdf_metadata

    error = _validate_pdf_metadata(
        {"Title": "Wrong", "Author": "EduTeX", "Subject": "EduTeX course roadmap"},
        title="Quality Course",
        author="EduTeX",
        subject="EduTeX course roadmap",
    )
    assert error == "PDF metadata mismatch for Title: expected 'Quality Course', got 'Wrong'"


def test_quality_check_id_maps_stable_names_and_unknowns() -> None:
    assert quality_check_id("Q001 Python syntax") == "Q001"
    assert quality_check_id("Q007 PDF/LaTeX accessibility contract") == "Q007"
    assert quality_check_id("Q999 Unknown check") is None


def test_quality_baseline_missing_checks_tracks_unexecuted_catalog_ids() -> None:
    from tools.quality_check import CheckResult

    assert quality_baseline_missing_checks([]) == (
        "Q001", "Q002", "Q003", "Q004", "Q005", "Q006", "Q007", "Q008", "Q009", "Q010", "Q011", "Q012", "Q013", "Q014", "Q015", "Q016", "Q017", "Q018", "Q019", "Q020", "Q021", "Q022", "Q023", "Q024", "Q025", "Q026", "Q027", "Q028", "Q029", "Q030", "Q031", "Q032", "Q033", "Q034", "Q035", "Q036"
    )
    assert quality_baseline_missing_checks(
        [CheckResult("Q001 Python syntax", True), CheckResult("Q002 pytest suite", False)]
    ) == ("Q003", "Q004", "Q005", "Q006", "Q007", "Q008", "Q009", "Q010", "Q011", "Q012", "Q013", "Q014", "Q015", "Q016", "Q017", "Q018", "Q019", "Q020", "Q021", "Q022", "Q023", "Q024", "Q025", "Q026", "Q027", "Q028", "Q029", "Q030", "Q031", "Q032", "Q033", "Q034", "Q035", "Q036")
    assert quality_baseline_missing_checks(
        [CheckResult(name, True) for name in check_names()]
    ) == ()


def test_quality_baseline_catalog_diagnostics_accept_valid_prefix() -> None:
    from tools.quality_check import CheckResult

    results = [CheckResult(name, True) for name in check_names()[:3]]

    assert quality_baseline_catalog_diagnostics(results) == ()


def test_quality_baseline_catalog_diagnostics_reports_unknown_duplicate_and_order() -> None:
    from tools.quality_check import CheckResult

    results = [
        CheckResult("Q001 Python syntax", True),
        CheckResult("Q003 CLI lint JSON", True),
        CheckResult("Q003 CLI lint JSON", True),
        CheckResult("Q999 Unknown check", True),
    ]

    diagnostics = quality_baseline_catalog_diagnostics(results)

    assert "quality check order mismatch at position 2: expected Q002 pytest suite, got Q003 CLI lint JSON" in diagnostics
    assert "duplicate quality check result: Q003 CLI lint JSON" in diagnostics
    assert "unknown quality check at position 4: Q999 Unknown check" in diagnostics


def test_quality_baseline_catalog_diagnostics_reports_too_many_results() -> None:
    from tools.quality_check import CheckResult

    results = [CheckResult(name, True) for name in check_names()]
    results.append(CheckResult("Q008 Extra check", True))

    diagnostics = quality_baseline_catalog_diagnostics(results)

    assert any("too many quality check results" in item for item in diagnostics)


def test_quality_execution_diagnostics_reports_plan_drift(monkeypatch) -> None:
    from tools import quality_check

    original = quality_check.quality_check_execution_plan
    try:
        monkeypatch.setattr(
            quality_check,
            "quality_check_execution_plan",
            lambda: (("Q001", original()[0][1]), ("Q003", original()[2][1])),
        )
        diagnostics = quality_check.quality_check_execution_diagnostics()
    finally:
        monkeypatch.setattr(quality_check, "quality_check_execution_plan", original)

    assert diagnostics
    assert "execution order mismatch" in diagnostics[0]
    assert "execution count mismatch" in diagnostics[1]


def test_quality_baseline_status_distinguishes_outcomes() -> None:
    from tools.quality_check import CheckResult, quality_baseline_status

    passed_results = [CheckResult(name, True) for name in (
        "Q001 Python syntax",
        "Q002 pytest suite",
        "Q003 CLI lint JSON",
        "Q004 build lint preflight",
        "Q005 CLI contract",
        "Q006 Course management contract",
        "Q007 PDF/LaTeX accessibility contract",
        "Q008 Packaging contract",
        "Q009 Release metadata contract",
        "Q010 Quality report schema contract",
        "Q011 Quality report consistency contract",
        "Q012 Quality report diagnostics contract",
        "Q013 Quality report value-types contract",
        "Q014 Quality report identity contract",
        "Q015 Quality report catalog metadata contract",
        "Q016 Quality report serialization contract",
        "Q017 Quality CLI JSON output contract",
        "Q018 Quality runner stop-on-failure contract",
        "Q019 Quality runner/report alignment contract",
        "Q020 Quality report outcome contract",
        "Q021 Quality runner exception contract",
        "Q022 Quality runner identity contract",
        "Q023 Quality runner return-code contract",
        "Q024 Quality execution-plan structure contract",
        "Q025 Quality execution diagnostics/report contract",
        "Q026 Quality diagnostics channel separation contract",
        "Q027 Quality report diagnostic outcome contract",
        "Q028 Quality diagnostic value-types contract",
        "Q029 Quality diagnostic uniqueness contract",
        "Q030 Quality diagnostic determinism contract",
        "Q031 Quality diagnostic completeness contract",
        "Q032 Quality diagnostic channel isolation contract",
        "Q033 Quality diagnostic provenance contract",
        "Q034 Quality runner/report consistency contract",
        "Q035 Release baseline end-to-end contract",
        "Q036 Build/Validate JSON contract",
    )]

    assert quality_baseline_status(passed_results) == "passed"
    assert quality_baseline_status(passed_results[:-1]) == "incomplete"
    assert quality_baseline_status([*passed_results[:1], CheckResult("Q002 pytest suite", False)]) == "failed"
    assert quality_baseline_status([]) == "incomplete"


def test_new_quality_run_id_is_unique_uuid4() -> None:
    import uuid

    from tools.quality_check import new_quality_run_id

    first = new_quality_run_id()
    second = new_quality_run_id()

    assert first != second
    assert uuid.UUID(first).version == 4
    assert uuid.UUID(second).version == 4


def test_quality_baseline_report_preserves_supplied_run_id() -> None:
    from tools.quality_check import quality_baseline_report

    report = quality_baseline_report([], run_id="run-test-0528")

    assert report["run_id"] == "run-test-0528"


def test_quality_baseline_report_generates_run_id_when_omitted() -> None:
    import uuid

    from tools.quality_check import quality_baseline_report

    report = quality_baseline_report([])

    assert uuid.UUID(report["run_id"]).version == 4


def test_new_quality_run_started_at_is_utc_rfc3339() -> None:
    from datetime import datetime, timezone

    from tools.quality_check import new_quality_run_started_at

    value = new_quality_run_started_at()
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

    assert value.endswith("Z")
    assert parsed.tzinfo == timezone.utc


def test_quality_baseline_report_preserves_supplied_run_started_at() -> None:
    from tools.quality_check import quality_baseline_report

    report = quality_baseline_report([], run_started_at="2026-09-11T10:00:00Z")

    assert report["run_started_at"] == "2026-09-11T10:00:00Z"


def test_quality_baseline_report_generates_run_started_at_when_omitted() -> None:
    from datetime import datetime

    from tools.quality_check import quality_baseline_report

    report = quality_baseline_report([])
    value = report["run_started_at"]

    assert isinstance(value, str)
    assert value.endswith("Z")
    datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_new_quality_run_finished_at_is_utc_rfc3339() -> None:
    from datetime import datetime, timezone

    from tools.quality_check import new_quality_run_finished_at

    value = new_quality_run_finished_at()
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

    assert value.endswith("Z")
    assert parsed.tzinfo == timezone.utc


def test_quality_baseline_report_preserves_finish_and_duration() -> None:
    from tools.quality_check import quality_baseline_report

    report = quality_baseline_report(
        [],
        run_finished_at="2026-09-11T10:00:03Z",
        duration_seconds=3.25,
    )

    assert report["run_finished_at"] == "2026-09-11T10:00:03Z"
    assert report["duration_seconds"] == 3.25
    assert report["duration_seconds"] >= 0.0


def test_quality_baseline_report_generates_finish_and_default_duration() -> None:
    from datetime import datetime

    from tools.quality_check import quality_baseline_report

    report = quality_baseline_report([])

    assert isinstance(report["run_finished_at"], str)
    assert report["run_finished_at"].endswith("Z")
    datetime.fromisoformat(report["run_finished_at"].replace("Z", "+00:00"))
    assert report["duration_seconds"] == 0.0


def test_quality_baseline_summary_counts_passed_failed_and_pending() -> None:
    from tools.quality_check import CheckResult

    summary = quality_baseline_summary([
        CheckResult("Q001 Python syntax", True),
        CheckResult("Q002 pytest suite", False),
        CheckResult("Q003 CLI lint JSON", True),
    ])

    assert summary == {
        "passed": 2,
        "failed": 1,
        "pending": 33,
        "total": 36,
        "completed": 3,
        "pass_rate": 66.67,
        "completion_rate": 8.33,
        "failure_rate": 33.33,
    }


def test_quality_baseline_summary_is_non_negative_for_extra_results() -> None:
    from tools.quality_check import CheckResult

    results = [CheckResult(name, True) for name in (
        "Q001 Python syntax",
        "Q002 pytest suite",
        "Q003 CLI lint JSON",
        "Q004 build lint preflight",
        "Q005 CLI contract",
        "Q006 Course management contract",
        "Q007 PDF/LaTeX accessibility contract",
        "Q008 Packaging contract",
        "Q999 Unknown check",
    )]

    assert quality_baseline_summary(results) == {
        "passed": 9,
        "failed": 0,
        "pending": 27,
        "total": 36,
        "completed": 9,
        "pass_rate": 100.0,
        "completion_rate": 25.0,
        "failure_rate": 0.0,
    }


def test_quality_baseline_report_includes_summary() -> None:
    from tools.quality_check import CheckResult, quality_baseline_report

    report = quality_baseline_report([
        CheckResult("Q001 Python syntax", True),
        CheckResult("Q002 pytest suite", False),
    ])

    assert report["summary"] == {
        "passed": 1,
        "failed": 1,
        "pending": 34,
        "total": 36,
        "completed": 2,
        "pass_rate": 50.0,
        "completion_rate": 5.56,
        "failure_rate": 50.0,
    }


def test_quality_report_contract_exposes_required_field_groups() -> None:
    top_level, check_fields, summary_fields = quality_report_contract()

    assert "schema" in top_level
    assert "checks" in top_level
    assert check_fields == ("id", "name", "passed", "status", "returncode", "detail")
    assert summary_fields == (
        "passed", "failed", "pending", "total", "completed",
        "pass_rate", "completion_rate", "failure_rate",
    )


def test_quality_report_schema_contract_accepts_complete_failed_and_empty_reports() -> None:
    from tools.quality_check import _check_quality_report_schema_contract

    result = _check_quality_report_schema_contract(Path("."))

    assert result.passed
    assert "schema" in result.detail


def test_quality_report_schema_contract_is_in_execution_plan() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-27] == "Q010"


def test_quality_report_consistency_contract_accepts_representative_reports() -> None:
    from tools.quality_check import _check_quality_report_consistency_contract

    result = _check_quality_report_consistency_contract(Path("."))

    assert result.passed
    assert "counts" in result.detail


def test_quality_report_consistency_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-26] == "Q011"


def test_quality_report_diagnostics_contract_accepts_valid_and_detects_corruption() -> None:
    from tools.quality_check import _check_quality_report_diagnostics_contract

    result = _check_quality_report_diagnostics_contract(Path("."))

    assert result.passed
    assert "deterministic diagnostics" in result.detail


def test_quality_report_diagnostics_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-25] == "Q012"


def test_quality_report_value_types_contract_accepts_representative_reports() -> None:
    from tools.quality_check import _check_quality_report_value_types_contract

    result = _check_quality_report_value_types_contract(Path("."))

    assert result.passed
    assert "value types" in result.detail


def test_quality_report_value_types_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-24] == "Q013"


def test_quality_report_identity_contract_accepts_representative_reports() -> None:
    from tools.quality_check import _check_quality_report_identity_contract

    result = _check_quality_report_identity_contract(Path("."))

    assert result.passed
    assert "identifiers" in result.detail


def test_quality_report_identity_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-23] == "Q014"


def test_quality_report_catalog_metadata_contract_accepts_representative_reports() -> None:
    from tools.quality_check import _check_quality_report_catalog_metadata_contract

    result = _check_quality_report_catalog_metadata_contract(Path("."))

    assert result.passed
    assert "catalog metadata" in result.detail


def test_quality_report_catalog_metadata_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-22] == "Q015"


def test_quality_report_serialization_contract_accepts_representative_reports() -> None:
    from tools.quality_check import _check_quality_report_serialization_contract

    result = _check_quality_report_serialization_contract(Path("."))

    assert result.passed
    assert "serialize" in result.detail


def test_quality_report_serialization_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-21] == "Q016"


def test_quality_cli_json_output_contract_accepts_representative_run() -> None:
    from tools.quality_check import _check_quality_cli_json_output_contract

    result = _check_quality_cli_json_output_contract(Path("."))

    assert result.passed
    assert "JSON output" in result.detail


def test_quality_cli_json_output_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-20] == "Q017"


def test_quality_runner_stop_on_failure_contract_accepts_synthetic_plan() -> None:
    from tools.quality_check import _check_quality_runner_stop_on_failure_contract

    result = _check_quality_runner_stop_on_failure_contract(Path("."))

    assert result.passed
    assert "first failure" in result.detail


def test_quality_runner_stop_on_failure_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-19] == "Q018"


def test_quality_runner_report_alignment_contract_accepts_representative_runs() -> None:
    from tools.quality_check import _check_quality_runner_report_alignment_contract

    result = _check_quality_runner_report_alignment_contract(Path("."))

    assert result.passed
    assert "remain aligned" in result.detail


def test_quality_runner_report_alignment_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-18] == "Q019"


def test_quality_report_outcome_contract_accepts_representative_reports() -> None:
    from tools.quality_check import _check_quality_report_outcome_contract

    result = _check_quality_report_outcome_contract(Path("."))

    assert result.passed
    assert "exit semantics" in result.detail


def test_quality_report_outcome_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-17] == "Q020"


def test_quality_runner_exception_contract_accepts_raised_check() -> None:
    from tools.quality_check import _check_quality_runner_exception_contract

    result = _check_quality_runner_exception_contract(Path("."))

    assert result.passed
    assert "deterministic failed results" in result.detail


def test_quality_runner_exception_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-16] == "Q021"


def test_quality_runner_identity_contract_accepts_mismatched_result() -> None:
    from tools.quality_check import _check_quality_runner_identity_contract

    result = _check_quality_runner_identity_contract(Path("."))

    assert result.passed
    assert "identity alignment" in result.detail


def test_quality_runner_identity_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-15] == "Q022"


def test_quality_runner_returncode_contract_accepts_inconsistent_codes() -> None:
    from tools.quality_check import _check_quality_runner_returncode_contract

    result = _check_quality_runner_returncode_contract(Path("."))

    assert result.passed
    assert "return-code semantics" in result.detail


def test_quality_runner_returncode_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-14] == "Q023"


def test_quality_execution_plan_structure_contract_accepts_malformed_plans() -> None:
    from tools.quality_check import _check_quality_execution_plan_structure_contract

    result = _check_quality_execution_plan_structure_contract(Path("."))

    assert result.passed
    assert "diagnosed deterministically" in result.detail


def test_quality_execution_plan_structure_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-13] == "Q024"


def test_quality_execution_diagnostics_report_contract_accepts_malformed_plan() -> None:
    from tools.quality_check import _check_quality_execution_diagnostics_report_contract

    result = _check_quality_execution_diagnostics_report_contract(Path("."))

    assert result.passed
    assert "propagate deterministically" in result.detail


def test_quality_execution_diagnostics_report_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-12] == "Q025"


def test_quality_diagnostics_channel_separation_contract_accepts_combined_diagnostics() -> None:
    from tools.quality_check import _check_quality_diagnostics_channel_separation_contract

    result = _check_quality_diagnostics_channel_separation_contract(Path("."))

    assert result.passed
    assert "remain separate" in result.detail


def test_quality_diagnostics_channel_separation_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-11] == "Q026"


def test_quality_report_diagnostic_outcome_contract_accepts_coherent_reports() -> None:
    from tools.quality_check import _check_quality_report_diagnostic_outcome_contract

    result = _check_quality_report_diagnostic_outcome_contract(Path("."))

    assert result.passed
    assert "remain coherent" in result.detail


def test_quality_report_diagnostic_outcome_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-10] == "Q027"


def test_quality_diagnostic_value_types_contract_accepts_json_safe_reports() -> None:
    from tools.quality_check import _check_quality_diagnostic_value_types_contract

    result = _check_quality_diagnostic_value_types_contract(Path("."))

    assert result.passed
    assert "JSON-safe values" in result.detail


def test_quality_diagnostic_value_types_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-9] == "Q028"


def test_quality_diagnostic_uniqueness_contract_accepts_valid_messages() -> None:
    from tools.quality_check import _check_quality_diagnostic_uniqueness_contract

    result = _check_quality_diagnostic_uniqueness_contract(Path("."))

    assert result.passed
    assert "non-empty" in result.detail


def test_quality_diagnostic_uniqueness_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-8] == "Q029"


def test_quality_diagnostic_determinism_contract_accepts_repeated_reports() -> None:
    from tools.quality_check import _check_quality_diagnostic_determinism_contract

    result = _check_quality_diagnostic_determinism_contract(Path("."))

    assert result.passed
    assert "deterministic" in result.detail


def test_quality_diagnostic_determinism_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-7] == "Q030"


def test_quality_diagnostic_completeness_contract_accepts_complete_propagation() -> None:
    from tools.quality_check import _check_quality_diagnostic_completeness_contract

    result = _check_quality_diagnostic_completeness_contract(Path("."))

    assert result.passed
    assert "propagate completely" in result.detail


def test_quality_diagnostic_completeness_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-6] == "Q031"


def test_quality_diagnostic_channel_isolation_contract_accepts_single_source_failures() -> None:
    from tools.quality_check import _check_quality_diagnostic_channel_isolation_contract

    result = _check_quality_diagnostic_channel_isolation_contract(Path("."))

    assert result.passed
    assert "remain isolated" in result.detail


def test_quality_diagnostic_channel_isolation_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-5] == "Q032"


def test_quality_diagnostic_provenance_contract_accepts_distinct_failure_sources() -> None:
    from tools.quality_check import _check_quality_diagnostic_provenance_contract

    result = _check_quality_diagnostic_provenance_contract(Path("."))

    assert result.passed
    assert "distinct" in result.detail


def test_quality_diagnostic_provenance_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-4] == "Q033"


def test_quality_runner_report_consistency_contract_accepts_source_consistent_reports() -> None:
    from tools.quality_check import _check_quality_runner_report_consistency_contract

    result = _check_quality_runner_report_consistency_contract(Path("."))

    assert result.passed
    assert "source-consistent" in result.detail


def test_quality_runner_report_consistency_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-3] == "Q034"


def test_quality_release_baseline_end_to_end_contract_accepts_public_json_path() -> None:
    from tools.quality_check import _check_quality_release_baseline_end_to_end_contract

    result = _check_quality_release_baseline_end_to_end_contract(Path("."))

    assert result.passed
    assert "parseable" in result.detail


def test_quality_release_baseline_end_to_end_contract_is_last_execution_check() -> None:
    assert tuple(code for code, _ in quality_check_execution_plan())[-2] == "Q035"


def test_quality_baseline_report_diagnostics_accept_valid_report() -> None:
    from tools.quality_check import CheckResult, quality_baseline_report

    report = quality_baseline_report([
        CheckResult("Q001 Python syntax", True),
        CheckResult("Q002 pytest suite", False),
    ])

    assert quality_baseline_report_diagnostics(report) == ()


def test_quality_baseline_report_diagnostics_detect_status_and_summary_drift() -> None:
    from tools.quality_check import CheckResult, quality_baseline_report

    report = quality_baseline_report([CheckResult("Q001 Python syntax", True)])
    report["checks"][0]["status"] = "failed"
    del report["summary"]["failure_rate"]

    diagnostics = quality_baseline_report_diagnostics(report)

    assert "status mismatch" in diagnostics[0]
    assert "summary fields missing: failure_rate" in diagnostics[1]


def test_quality_baseline_report_is_json_safe_and_ordered() -> None:
    from tools.quality_check import CheckResult, quality_baseline_report

    results = [
        CheckResult("Q001 Python syntax", True, detail="compiled 3 files"),
        CheckResult("Q002 pytest suite", False, 7, "pytest failed"),
    ]

    report = quality_baseline_report(results)

    assert report["schema"] == "edutex.quality-baseline.v1"
    assert report["run_started_at"]
    assert report["run_finished_at"]
    assert report["duration_seconds"] == 0.0
    assert report["status"] == "failed"
    assert report["passed"] is False
    assert report["complete"] is False
    assert report["exit_code"] == 1
    assert report["catalog_consistent"] is True
    assert report["catalog_diagnostics"] == []
    assert report["execution_consistent"] is True
    assert report["execution_diagnostics"] == []
    assert report["checks_completed"] == 2
    assert report["checks_expected"] == 36
    assert report["missing_checks"] == ["Q003", "Q004", "Q005", "Q006", "Q007", "Q008", "Q009", "Q010", "Q011", "Q012", "Q013", "Q014", "Q015", "Q016", "Q017", "Q018", "Q019", "Q020", "Q021", "Q022", "Q023", "Q024", "Q025", "Q026", "Q027", "Q028", "Q029", "Q030", "Q031", "Q032", "Q033", "Q034", "Q035", "Q036"]
    assert report["summary"] == {
        "passed": 1,
        "failed": 1,
        "pending": 34,
        "total": 36,
        "completed": 2,
        "pass_rate": 50.0,
        "completion_rate": 5.56,
        "failure_rate": 50.0,
    }
    assert [entry["id"] for entry in report["check_catalog"]] == [
        "Q001", "Q002", "Q003", "Q004", "Q005", "Q006", "Q007", "Q008", "Q009", "Q010", "Q011", "Q012", "Q013", "Q014", "Q015", "Q016", "Q017", "Q018", "Q019", "Q020", "Q021", "Q022", "Q023", "Q024", "Q025", "Q026", "Q027", "Q028", "Q029", "Q030", "Q031", "Q032", "Q033", "Q034", "Q035", "Q036"
    ]
    assert report["failed_check"] == "Q002 pytest suite"
    assert report["failed_check_id"] == "Q002"
    assert report["checks"][0]["id"] == "Q001"
    assert report["checks"][0]["name"] == "Q001 Python syntax"
    assert report["checks"][0]["passed"] is True
    assert report["checks"][0]["status"] == "passed"
    assert report["checks"][1]["id"] == "Q002"
    assert report["checks"][1]["passed"] is False
    assert report["checks"][1]["status"] == "failed"
    assert report["checks"][1]["returncode"] == 7
    json.dumps(report)


def test_quality_baseline_report_exposes_failed_check_id() -> None:
    from tools.quality_check import CheckResult, quality_baseline_report

    report = quality_baseline_report([
        CheckResult("Q001 Python syntax", True),
        CheckResult("Q007 PDF/LaTeX accessibility contract", False),
    ])

    assert report["failed_check"] == "Q007 PDF/LaTeX accessibility contract"
    assert report["failed_check_id"] == "Q007"


def test_quality_baseline_report_fails_on_catalog_inconsistency() -> None:
    from tools.quality_check import CheckResult, quality_baseline_report

    report = quality_baseline_report([
        CheckResult("Q001 Python syntax", True),
        CheckResult("Q003 CLI lint JSON", True),
    ])

    assert report["status"] == "failed"
    assert report["passed"] is False
    assert report["catalog_consistent"] is False
    assert report["catalog_diagnostics"]
    assert report["exit_code"] == 1
    json.dumps(report)


def test_quality_baseline_report_marks_empty_results_incomplete() -> None:
    from tools.quality_check import quality_baseline_report

    report = quality_baseline_report([])

    assert report["status"] == "incomplete"
    assert report["passed"] is False
    assert report["complete"] is False
    assert report["exit_code"] == 1
    assert report["checks_completed"] == 0
    assert report["failed_check"] is None
    assert report["failed_check_id"] is None


def test_run_command_passes_for_zero_exit_code(tmp_path: Path) -> None:
    result = run_command(
        "QTEST success",
        ["fake", "success"],
        tmp_path,
        runner=lambda command, cwd: completed(0, "ok"),
    )

    assert result.passed
    assert result.returncode == 0
    assert result.detail == "ok"


def test_run_command_preserves_failure_and_output(tmp_path: Path) -> None:
    result = run_command(
        "QTEST failure",
        ["fake", "failure"],
        tmp_path,
        runner=lambda command, cwd: completed(7, "stdout", "stderr"),
    )

    assert not result.passed
    assert result.returncode == 7
    assert "stdout" in result.detail
    assert "stderr" in result.detail


def test_run_command_validator_can_fail_successful_process(tmp_path: Path) -> None:
    result = run_command(
        "QTEST validator",
        ["fake", "validator"],
        tmp_path,
        validator=lambda process: "contract mismatch",
        runner=lambda command, cwd: completed(0),
    )

    assert not result.passed
    assert result.returncode == 0
    assert result.detail == "contract mismatch"

def test_python_syntax_accepts_utf8_bom(tmp_path: Path) -> None:
    from tools.quality_check import _check_python_syntax

    (tmp_path / "tools").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "tools" / "bom_file.py").write_bytes(b"\xef\xbb\xbfvalue = 1\n")

    result = _check_python_syntax(tmp_path)

    assert result.passed, result.detail


def test_pdf_runtime_report_explicitly_identifies_missing_qpdf(monkeypatch) -> None:
    from tools import quality_check

    available = {"pdftotext", "pdfinfo", "pdftoppm"}
    monkeypatch.setattr(quality_check.shutil, "which", lambda name: f"/bin/{name}" if name in available else None)
    monkeypatch.setattr(quality_check, "_tool_version", lambda name: f"{name} test-version")

    report = quality_check.pdf_runtime_report("en")

    assert report["missing_gates"] == ["qpdf"]
    assert report["tools"]["qpdf"]["available"] is False
    assert report["tools"]["qpdf"]["role"] == "structural-validator"
    assert report["inspection_gates"]["qpdf"]["status"] == "unavailable_optional"
    assert report["inspection_gates"]["pdftotext"]["status"] == "available"
    assert report["inspection_gates"]["pypdf"]["status"] in {"available", "unavailable_optional"}

