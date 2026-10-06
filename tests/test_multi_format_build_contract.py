from __future__ import annotations

from pathlib import Path

import pytest

from edutex.build.multi_format import (
    MultiFormatBuildPlan,
    execute_multi_format,
    normalize_output_formats,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "MULTI_FORMAT_BUILD_CONTRACT.md"
IMPLEMENTATION = ROOT / "src" / "edutex" / "build" / "multi_format.py"


def test_normalize_output_formats_is_stable_and_preserves_order() -> None:
    assert normalize_output_formats(" PDF, html, latex ") == ("pdf", "html", "latex")
    assert normalize_output_formats(("html", "pdf")) == ("html", "pdf")


@pytest.mark.parametrize(
    "value",
    ("", "html,html", "html, epub", ("html", ""), ("html", "html")),
)
def test_normalize_output_formats_rejects_invalid_values(value: object) -> None:
    with pytest.raises(ValueError):
        normalize_output_formats(value)  # type: ignore[arg-type]


def test_plan_has_deterministic_output_paths() -> None:
    plan = MultiFormatBuildPlan.create(("html", "latex", "pdf"), Path("output"), "course")
    assert plan.output_paths() == (
        Path("output/course.html"),
        Path("output/course.tex"),
        Path("output/course.pdf"),
    )
    assert plan.output_paths() == plan.output_paths()


def test_plan_rejects_ambiguous_output_names() -> None:
    with pytest.raises(ValueError, match="suffix"):
        MultiFormatBuildPlan.create("html", Path("output"), "course.html")
    with pytest.raises(ValueError, match="directory separators"):
        MultiFormatBuildPlan.create("html", Path("output"), "nested/course")


def test_execute_multi_format_runs_once_in_declared_order(tmp_path: Path) -> None:
    plan = MultiFormatBuildPlan.create(("latex", "html"), tmp_path / "output", "course")
    calls: list[tuple[str, Path]] = []

    def build_one(output_format: str, destination: Path) -> Path:
        calls.append((output_format, destination))
        destination.write_text(output_format, encoding="utf-8")
        return destination

    outputs = execute_multi_format(plan, build_one)

    assert [item[0] for item in calls] == ["latex", "html"]
    assert outputs == plan.output_paths()
    assert all(path.is_file() for path in outputs)


def test_execute_multi_format_rejects_wrong_builder_destination(tmp_path: Path) -> None:
    plan = MultiFormatBuildPlan.create("html", tmp_path / "output", "course")

    with pytest.raises(ValueError, match="expected"):
        execute_multi_format(plan, lambda _format, _destination: tmp_path / "wrong.html")


def test_documentation_and_implementation_markers_are_present() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    implementation = IMPLEMENTATION.read_text(encoding="utf-8")
    for marker in ("opt-in", "ordine dichiarato", "build singolo", "deterministico"):
        assert marker in contract
    for marker in (
        "SUPPORTED_OUTPUT_FORMATS",
        "normalize_output_formats",
        "MultiFormatBuildPlan",
        "execute_multi_format",
    ):
        assert marker in implementation
