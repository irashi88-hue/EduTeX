"""Contract tests for the preparation lesson shipped with the project template."""

from __future__ import annotations

from pathlib import Path

import yaml

from edutex.configuration.schema import DialogueConfig

TEMPLATE = Path(__file__).resolve().parents[2] / "src" / "edutex" / "project_template"
SETUP_LESSON = TEMPLATE / "assets" / "knowledge_models" / "00-preparazione.md"


def _course() -> dict:
    return yaml.safe_load((TEMPLATE / "course.yaml").read_text(encoding="utf-8"))


def test_setup_lesson_is_the_first_lesson() -> None:
    lessons = _course()["modules"][0]["lessons"]

    assert lessons[0]["id"] == "lesson-00"
    assert lessons[0]["source"] == "assets/knowledge_models/00-preparazione.md"


def test_setup_lesson_source_exists() -> None:
    assert SETUP_LESSON.is_file()


def test_setup_lesson_describes_the_skip_path() -> None:
    text = SETUP_LESSON.read_text(encoding="utf-8")

    assert "Se non puoi creare l'agente" in text
    assert "langdock_url" in text


def test_template_dialogue_config_is_valid_with_empty_link() -> None:
    data = yaml.safe_load((TEMPLATE / "edutex.config.yaml").read_text(encoding="utf-8"))

    cfg = DialogueConfig(**data["dialogue"])

    assert cfg.langdock_url == ""