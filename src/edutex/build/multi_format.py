"""Deterministic opt-in planning and execution for multiple build formats."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path


SUPPORTED_OUTPUT_FORMATS = ("html", "latex", "pdf")
_OUTPUT_SUFFIXES = {"html": ".html", "latex": ".tex", "pdf": ".pdf"}


def normalize_output_formats(value: str | Iterable[str]) -> tuple[str, ...]:
    """Normalize a comma-separated or iterable format selection."""
    values = value.split(",") if isinstance(value, str) else value
    normalized: list[str] = []
    for raw_value in values:
        if not isinstance(raw_value, str):
            raise ValueError("Output formats must be strings")
        item = raw_value.strip().lower()
        if not item:
            raise ValueError("Output format names must not be empty")
        if item not in SUPPORTED_OUTPUT_FORMATS:
            allowed = ", ".join(SUPPORTED_OUTPUT_FORMATS)
            raise ValueError(f"Unsupported output format {item!r}; allowed: {allowed}")
        if item in normalized:
            raise ValueError(f"Duplicate output format: {item}")
        normalized.append(item)
    if not normalized:
        raise ValueError("At least one output format is required")
    return tuple(normalized)


@dataclass(frozen=True)
class MultiFormatBuildPlan:
    """Immutable plan for one deterministic multi-format build session."""

    formats: tuple[str, ...]
    output_dir: Path
    output_file: str

    @classmethod
    def create(
        cls,
        formats: str | Iterable[str],
        output_dir: Path,
        output_file: str,
    ) -> "MultiFormatBuildPlan":
        normalized = normalize_output_formats(formats)
        if not isinstance(output_dir, Path):
            raise TypeError("output_dir must be a pathlib.Path")
        if not output_file or output_file.strip() != output_file:
            raise ValueError("output_file must be a non-empty name without surrounding whitespace")
        if Path(output_file).name != output_file:
            raise ValueError("output_file must not contain directory separators")
        if Path(output_file).suffix:
            raise ValueError("output_file must not include a suffix")
        return cls(normalized, output_dir, output_file)

    def output_path(self, output_format: str) -> Path:
        """Return the stable destination for one format in this plan."""
        normalized = normalize_output_formats((output_format,))[0]
        if normalized not in self.formats:
            raise ValueError(f"Format {normalized!r} is not part of this build plan")
        return self.output_dir / f"{self.output_file}{_OUTPUT_SUFFIXES[normalized]}"

    def output_paths(self) -> tuple[Path, ...]:
        """Return destinations in the exact declared format order."""
        return tuple(self.output_path(item) for item in self.formats)


BuildOne = Callable[[str, Path], Path]


def execute_multi_format(
    plan: MultiFormatBuildPlan,
    build_one: BuildOne,
) -> tuple[Path, ...]:
    """Execute each requested format once, sequentially and in declared order."""
    plan.output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for output_format in plan.formats:
        destination = plan.output_path(output_format)
        result = build_one(output_format, destination)
        if not isinstance(result, Path):
            raise TypeError("build_one must return a pathlib.Path")
        if result != destination:
            raise ValueError(
                f"Builder returned {result} for {output_format}; expected {destination}"
            )
        outputs.append(result)
    return tuple(outputs)
