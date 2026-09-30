"""Release metadata consistency checks."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "0.5.0"


def test_release_version_is_consistent_across_project_metadata() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    cli_source = (ROOT / "src" / "edutex" / "core" / "cli.py").read_text(encoding="utf-8")
    template = (ROOT / "src" / "edutex" / "project_template" / "edutex.config.yaml").read_text(encoding="utf-8")

    assert pyproject["project"]["version"] == EXPECTED_VERSION
    assert re.search(rf'CLI_VERSION = "{re.escape(EXPECTED_VERSION)}"', cli_source)
    assert re.search(rf'^  version: "{re.escape(EXPECTED_VERSION)}"$', template, re.MULTILINE)


def test_readme_identifies_current_release_and_json_build_output() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "## Release 0.5.0 — V1 release foundation" in readme
    assert "edutex build --project path/to/project --lint --format json" in readme
