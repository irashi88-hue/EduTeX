"""Unit tests for the EduTeX quality baseline runner."""

from __future__ import annotations

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
    )
    assert len(names) == len(set(names))


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
