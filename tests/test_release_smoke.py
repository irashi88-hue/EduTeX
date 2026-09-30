"""Release smoke tests for the EduTeX 0.5.0 baseline.

These checks intentionally avoid importing the full runtime. They remain useful
when a source snapshot is incomplete, while still protecting the release
contract exposed by the renderer and project metadata.
"""

from __future__ import annotations

import compileall
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "0.5.0"
RENDERER = ROOT / "src" / "edutex" / "build" / "html_renderer.py"
README = ROOT / "README.md"
PYPROJECT = ROOT / "pyproject.toml"
CONFIG = ROOT / "edutex.config.yaml"
CLI = ROOT / "src" / "edutex" / "core" / "cli.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def test_release_version_is_consistent() -> None:
    pyproject = _read(PYPROJECT)
    config = yaml.safe_load(_read(CONFIG))
    cli = _read(CLI)
    readme = _read(README)

    assert f'version = "{EXPECTED_VERSION}"' in pyproject
    assert config["edutex"]["version"] == EXPECTED_VERSION
    assert f'CLI_VERSION = "{EXPECTED_VERSION}"' in cli
    assert f"Release {EXPECTED_VERSION}" in readme


def test_python_source_compiles() -> None:
    assert compileall.compile_dir(
        str(ROOT / "src"),
        quiet=1,
        maxlevels=20,
        optimize=0,
    )


def test_renderer_dispatches_all_supported_interactive_exercises() -> None:
    source = _read(RENDERER)
    expected = {
        "short_answer": "_is_short_answer_exercise",
        "cloze": "_is_cloze_exercise",
        "true_false": "_is_true_false_exercise",
        "builder": "_is_sentence_builder_exercise",
        "matching": "_is_matching_exercise",
        "translation": "_is_translation_exercise",
        "choice": "_is_choice_exercise",
    }

    for exercise_type, detector in expected.items():
        assert f'type: {exercise_type}' in source or exercise_type in source
        assert detector in source


def test_renderer_keeps_accessibility_and_self_contained_contract() -> None:
    source = _read(RENDERER)

    for marker in (
        'meta name="viewport"',
        'class="skip-link"',
        ':focus-visible',
        'aria-label=',
        'aria-live=',
        'type="button"',
    ):
        assert marker in source

    # The generated HTML must not depend on a remote JavaScript bundle.
    assert "<script src=" not in source
    assert "http://" not in source
    assert "https://" not in source


def test_renderer_preserves_solution_and_localization_contract() -> None:
    source = _read(RENDERER)

    for marker in (
        "show_solution",
        "solution-inline",
        "solutions",
        '"en"',
        '"it"',
        "special_chars",
    ):
        assert marker in source

def test_renderer_preserves_recent_accessibility_and_layout_contracts() -> None:
    """Protect the renderer contracts added after the 0.3.0 smoke baseline."""
    source = _read(RENDERER)

    # Dark-mode contract: semantic light tokens plus a dark preference override.
    for marker in (
        "--canvas-bg:",
        "--surface:",
        "--ink:",
        "--muted:",
        "@media (prefers-color-scheme: dark)",
        "color-scheme: dark;",
    ):
        assert marker in source

    # Hierarchical table of contents contract.
    for marker in (
        "def render_nodes(nodes: list[dict[str, object]]) -> str:",
        "parts.append(render_nodes(children))",
        ".toc ol ol {{ margin-top: .15rem; }}",
    ):
        assert marker in source

    # Responsive exercise contract.
    for marker in (
        "@media (max-width: 640px)",
        ".matching-row {{",
        ".true-false-row {{",
        "grid-template-columns: 1fr;",
        "width: 100%;",
    ):
        assert marker in source

    # Keyboard-focus contract must not depend on :has().
    assert ".true-false-option:focus-within {{" in source
    assert ".true-false-option:has(input:focus-visible)" not in source


def test_renderer_keeps_duplicate_id_and_remote_dependency_guards() -> None:
    source = _read(RENDERER)
    assert "_used_ids" in source
    assert "def _unique_id" in source
    assert "<script src=" not in source
    assert "http://" not in source
    assert "https://" not in source
