"""Run EduTeX release checks without requiring the complete runtime install."""

from __future__ import annotations

import compileall
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")
    print(f"PASS: {message}")


def main() -> int:
    pyproject = read("pyproject.toml")
    config = read("edutex.config.yaml")
    cli = read("src/edutex/core/cli.py")
    readme = read("README.md")
    renderer = read("src/edutex/build/html_renderer.py")

    check('version = "1.0.0"' in pyproject, "pyproject version")
    check(bool(re.search(r"^\s*version:\s*['\"]?1\.0\.0", config, re.MULTILINE)), "config version")
    check('CLI_VERSION = "1.0.0"' in cli, "CLI version")
    check("Release 1.0.0" in readme, "README release section")
    check(compileall.compile_dir(str(ROOT / "src"), quiet=1, maxlevels=20), "Python compilation")

    exercise_detectors = (
        "_is_short_answer_exercise",
        "_is_cloze_exercise",
        "_is_true_false_exercise",
        "_is_sentence_builder_exercise",
        "_is_matching_exercise",
        "_is_translation_exercise",
        "_is_choice_exercise",
    )
    for detector in exercise_detectors:
        check(detector in renderer, f"renderer detector: {detector}")

    for marker in ('meta name="viewport"', 'class="skip-link"', ':focus-visible', "aria-live="):
        check(marker in renderer, f"HTML accessibility marker: {marker}")

    check("<script src=" not in renderer, "self-contained JavaScript")
    check("http://" not in renderer and "https://" not in renderer, "no remote renderer dependency")
    print("EduTeX release validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
