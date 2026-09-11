"""Unit tests for the EduTeX quality baseline runner."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from tools.quality_check import check_names, run_command


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
    )
    assert len(names) == len(set(names))



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


def test_quality_baseline_report_is_json_safe_and_ordered() -> None:
    from tools.quality_check import CheckResult, quality_baseline_report

    results = [
        CheckResult("Q001 Python syntax", True, detail="compiled 3 files"),
        CheckResult("Q002 pytest suite", False, 7, "pytest failed"),
    ]

    report = quality_baseline_report(results)

    assert report["schema"] == "edutex.quality-baseline.v1"
    assert report["passed"] is False
    assert report["checks_completed"] == 2
    assert report["checks_expected"] == 7
    assert report["failed_check"] == "Q002 pytest suite"
    assert report["checks"][0]["name"] == "Q001 Python syntax"
    assert report["checks"][1]["returncode"] == 7
    json.dumps(report)


def test_quality_baseline_report_marks_empty_results_as_failed() -> None:
    from tools.quality_check import quality_baseline_report

    report = quality_baseline_report([])

    assert report["passed"] is False
    assert report["checks_completed"] == 0
    assert report["failed_check"] is None


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

