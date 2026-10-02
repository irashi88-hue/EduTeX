"""Contract tests for the course-build JSON report."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from edutex.core.cli import main


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "COURSE_BUILD_REPORT_CONTRACT.md"


def make_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    result = CliRunner().invoke(main, ["init", str(project)])
    assert result.exit_code == 0, result.output
    return project


def test_documentazione_course_build_report() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    for marker in (
        "--report-format text|json",
        "course_build",
        "status",
        "artifacts",
        "percorsi assoluti",
        "exit code `1`",
        "CourseBuildError",
    ):
        assert marker in contract, f"Marker mancante: {marker}"
    assert all(
        not line.rstrip("\n").endswith((" ", "\t"))
        for line in contract.splitlines(keepends=True)
    )


def test_course_build_json_success_lists_absolute_existing_artifacts(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    result = CliRunner().invoke(
        main,
        [
            "course",
            "build",
            "--project",
            str(project),
            "--format",
            "html",
            "--report-format",
            "json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    report = payload["course_build"]
    assert report["status"] == "completed"
    assert Path(report["project_root"]).resolve() == project.resolve()
    assert Path(report["manifest"]).resolve() == (project / "course.yaml").resolve()
    assert report["output_format"] == "html"
    assert Path(report["output"]).is_absolute()
    assert Path(report["output"]).is_file()
    artifacts = report["artifacts"]
    assert isinstance(artifacts, list)
    assert artifacts
    assert report["output"] in artifacts
    assert all(Path(item).is_absolute() and Path(item).is_file() for item in artifacts)
    assert any(Path(item).name == "course.html" for item in artifacts)
    assert any(Path(item).parent.name == "lessons" for item in artifacts)


def test_course_build_json_latex_lists_primary_artifact(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    result = CliRunner().invoke(
        main,
        [
            "course",
            "build",
            "--project",
            str(project),
            "--format",
            "latex",
            "--report-format",
            "json",
        ],
    )

    assert result.exit_code == 0, result.output
    report = json.loads(result.output)["course_build"]
    assert report["output_format"] == "latex"
    assert report["artifacts"] == [report["output"]]
    assert Path(report["output"]).suffix == ".tex"
    assert Path(report["output"]).is_file()


def test_course_build_json_failure_is_stable_and_has_no_artifacts(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    result = CliRunner().invoke(
        main,
        [
            "course",
            "build",
            "--project",
            str(project),
            "--manifest",
            "missing-course.yaml",
            "--report-format",
            "json",
        ],
    )

    assert result.exit_code == 1
    report = json.loads(result.output)["course_build"]
    assert report["status"] == "failed"
    assert report["error"]["type"] == "CourseBuildError"
    assert report["error"]["message"]
    assert "artifacts" not in report
