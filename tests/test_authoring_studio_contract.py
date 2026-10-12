from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from edutex.core.cli import main
from edutex.course.studio import (
    StudioConflictError,
    StudioValidationError,
    load_course_document,
    save_course_document,
)


def make_project(root: Path, *, wrapped: bool = False) -> Path:
    source = root / "assets" / "knowledge_models" / "lesson.md"
    source.parent.mkdir(parents=True)
    source.write_text(
        "---\nid: lesson-01\ntitle: Prima lezione\nlanguage: it\nlevel: A1\nversion: 1.0.0\n---\n\nContenuto.\n",
        encoding="utf-8",
    )
    course = {
        "id": "scienze-a1",
        "title": "Scienze",
        "language": "it",
        "level": "A1",
        "version": "1.0.0",
        "author": "Autore",
        "description": "Corso di prova",
        "custom_metadata": {"keep": True},
        "modules": [{
            "id": "module-01",
            "title": "Introduzione",
            "lessons": [{"id": "lesson-01", "title": "Prima lezione", "source": "assets/knowledge_models/lesson.md"}],
        }],
    }
    raw = {"course": course, "custom_root_field": ["keep"]} if wrapped else course
    manifest = root / "course.yaml"
    manifest.write_text(yaml.safe_dump(raw, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return manifest


def test_load_and_save_preserve_unknown_fields_and_existing_manifest_shape(tmp_path: Path) -> None:
    manifest = make_project(tmp_path)
    document, etag, report = load_course_document(tmp_path)
    assert report.valid
    document["title"] = "Scienze naturali"
    new_etag, saved = save_course_document(tmp_path, document, etag)
    raw = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    assert saved.valid
    assert new_etag == hashlib.sha256(manifest.read_bytes()).hexdigest()
    assert raw["title"] == "Scienze naturali"
    assert raw["custom_metadata"] == {"keep": True}


def test_wrapped_course_manifest_shape_and_unknown_root_fields_are_preserved(tmp_path: Path) -> None:
    manifest = make_project(tmp_path, wrapped=True)
    document, etag, _ = load_course_document(tmp_path)
    document["course"]["title"] = "Scienze della natura"
    save_course_document(tmp_path, document, etag)
    raw = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    assert raw["course"]["title"] == "Scienze della natura"
    assert raw["custom_root_field"] == ["keep"]
    assert raw["course"]["custom_metadata"] == {"keep": True}


def test_invalid_save_does_not_change_manifest(tmp_path: Path) -> None:
    manifest = make_project(tmp_path)
    document, etag, _ = load_course_document(tmp_path)
    original = manifest.read_bytes()
    document["modules"][0]["lessons"][0]["source"] = "../outside.md"
    with pytest.raises(StudioValidationError):
        save_course_document(tmp_path, document, etag)
    assert manifest.read_bytes() == original


def test_stale_editor_save_is_rejected(tmp_path: Path) -> None:
    make_project(tmp_path)
    document, etag, _ = load_course_document(tmp_path)
    with pytest.raises(StudioConflictError):
        save_course_document(tmp_path, document, "stale-etag")


def test_studio_cli_is_registered_under_existing_author_group(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    make_project(tmp_path)
    calls: list[tuple[Path, Path, bool]] = []
    monkeypatch.setattr(
        "edutex.core.cli.run_author_studio",
        lambda root, manifest, *, open_browser: calls.append((root, manifest, open_browser)),
    )
    result = CliRunner().invoke(
        main, ["author", "studio", "--project", str(tmp_path), "--no-browser"]
    )
    assert result.exit_code == 0, result.output
    assert calls == [(tmp_path.resolve(), (tmp_path / "course.yaml").resolve(), False)]


def test_studio_help_describes_existing_manifest_workflow() -> None:
    result = CliRunner().invoke(main, ["author", "studio", "--help"])
    assert result.exit_code == 0
    assert "course.yaml" in result.output
    assert "--project" in result.output
    assert "--no-browser" in result.output
