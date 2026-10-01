"""Test del contratto JSON pubblico di EduTeX."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from edutex.core.cli import main


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "JSON_API_CONTRACT.md"


def parse_json(result, label: str) -> dict[str, object]:
    assert result.exit_code == 0, f"{label} fallito:\n{result.output}"

    try:
        payload = json.loads(result.output)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"{label} non ha prodotto JSON valido:\n{result.output}"
        ) from exc

    assert isinstance(payload, dict), f"{label} non ha una radice oggetto"
    return payload


def make_project(tmp_path: Path) -> tuple[Path, Path, Path]:
    runner = CliRunner()
    project = tmp_path / "project"
    result = runner.invoke(
        main,
        [
            "init",
            str(project),
            "--theme",
            "default",
            "--language",
            "it",
        ],
    )
    assert result.exit_code == 0, result.output

    config = project / "edutex.config.yaml"
    config_source = config.read_text(encoding="utf-8")
    old_format = 'output_format: "pdf"'
    html_format = 'output_format: "html"'
    pdf_count = config_source.count(old_format)
    html_count = config_source.count(html_format)

    if pdf_count == 1 and html_count == 0:
        config.write_text(
            config_source.replace(old_format, html_format, 1),
            encoding="utf-8",
        )
    elif pdf_count == 0 and html_count == 1:
        pass
    else:
        raise AssertionError(
            "Configurazione fixture ambigua: atteso un solo formato PDF "
            "oppure un solo formato HTML."
        )

    source = project / "assets" / "knowledge_models" / "example.md"
    manifest = project / "course.yaml"
    assert source.is_file()
    assert manifest.is_file()
    return project, source, manifest


def test_documentazione_json_pubblica() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")

    required_markers = (
        "edutex lint --format json",
        "edutex validate --format json",
        "edutex build --format json",
        "edutex course validate --format json",
        '"path"',
        '"validation"',
        '"lint"',
        '"build"',
        '"manifest"',
        '"diagnostics"',
        "ExtensionError",
        "layout.post_structure",
        "build.output_format",
        "--config",
    )

    for marker in required_markers:
        assert marker in contract, (
            f"Marker mancante nella documentazione JSON: {marker}"
        )

    assert all(
        not line.rstrip("\n").endswith((" ", "\t"))
        for line in contract.splitlines(keepends=True)
    )


def test_lint_json_contract(tmp_path: Path) -> None:
    runner = CliRunner()
    _, source, _ = make_project(tmp_path)

    result = runner.invoke(
        main,
        ["lint", str(source), "--format", "json"],
    )
    payload = parse_json(result, "lint --format json")

    assert set(payload) == {"path", "valid", "errors", "warnings"}
    assert isinstance(payload["path"], str)
    assert payload["valid"] is True
    assert isinstance(payload["errors"], list)
    assert isinstance(payload["warnings"], list)


def test_validate_json_contract(tmp_path: Path) -> None:
    runner = CliRunner()
    project, _, _ = make_project(tmp_path)
    config = project / "edutex.config.yaml"

    result = runner.invoke(
        main,
        [
            "validate",
            "--project",
            str(project),
            "--config",
            str(config),
            "--format",
            "json",
        ],
    )
    payload = parse_json(result, "validate --format json")

    assert set(payload) == {"validation"}
    validation = payload["validation"]
    assert isinstance(validation, dict)
    assert validation == {"status": "completed"}


def test_build_json_contract(tmp_path: Path) -> None:
    runner = CliRunner()
    project, _, _ = make_project(tmp_path)

    result = runner.invoke(
        main,
        [
            "build",
            "--project",
            str(project),
            "--format",
            "json",
        ],
    )
    payload = parse_json(result, "build --format json")

    assert set(payload) == {"lint", "build"}
    assert payload["lint"] is None
    assert isinstance(payload["build"], dict)
    assert payload["build"].get("status") == "completed"


def test_course_validate_json_contract(tmp_path: Path) -> None:
    runner = CliRunner()
    project, _, manifest = make_project(tmp_path)

    result = runner.invoke(
        main,
        [
            "course",
            "validate",
            "--project",
            str(project),
            "--manifest",
            str(manifest),
            "--format",
            "json",
        ],
    )
    payload = parse_json(result, "course validate --format json")

    assert set(payload) == {
        "manifest",
        "valid",
        "errors",
        "warnings",
        "diagnostics",
        "course",
    }
    assert isinstance(payload["manifest"], str)
    assert payload["valid"] is True
    assert isinstance(payload["errors"], list)
    assert isinstance(payload["warnings"], list)
    assert isinstance(payload["diagnostics"], list)
    assert isinstance(payload["course"], dict)


def test_json_contract_does_not_mix_human_prefixes(tmp_path: Path) -> None:
    runner = CliRunner()
    project, source, _ = make_project(tmp_path)

    commands = (
        ["lint", str(source), "--format", "json"],
        [
            "validate",
            "--project",
            str(project),
            "--format",
            "json",
        ],
        [
            "build",
            "--project",
            str(project),
            "--format",
            "json",
        ],
    )

    for arguments in commands:
        result = runner.invoke(main, arguments)
        assert result.exit_code == 0, result.output
        assert result.output.lstrip().startswith("{")
        assert result.output.rstrip().endswith("}")
        json.loads(result.output)
