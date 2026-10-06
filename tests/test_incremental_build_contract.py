"""Tests for deterministic incremental-build cache primitives."""

from __future__ import annotations

from pathlib import Path

import pytest

from edutex.build.incremental import (
    IncrementalBuildState,
    compute_build_fingerprint,
    is_incremental_hit,
    read_incremental_state,
    write_incremental_state,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "INCREMENTAL_BUILD_CONTRACT.md"


def test_fingerprint_is_stable_and_changes_with_content(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text("one", encoding="utf-8")
    first = compute_build_fingerprint([source], configuration="html|default")
    second = compute_build_fingerprint([source], configuration="html|default")
    assert first == second

    source.write_text("two", encoding="utf-8")
    assert compute_build_fingerprint([source], configuration="html|default") != first


def test_missing_input_is_part_of_the_fingerprint(tmp_path: Path) -> None:
    missing = tmp_path / "missing.md"
    first = compute_build_fingerprint([missing])
    missing.write_text("now exists", encoding="utf-8")
    assert compute_build_fingerprint([missing]) != first


def test_cache_state_round_trips_and_hit_requires_existing_output(tmp_path: Path) -> None:
    output = tmp_path / "document.html"
    cache = tmp_path / ".edutex" / "incremental.json"
    state = IncrementalBuildState(fingerprint="abc", output_path=str(output))
    write_incremental_state(cache, state)

    loaded = read_incremental_state(cache)
    assert loaded == state
    assert not is_incremental_hit(loaded, fingerprint="abc", output_path=output)

    output.write_text("<html></html>", encoding="utf-8")
    assert is_incremental_hit(loaded, fingerprint="abc", output_path=output)
    assert not is_incremental_hit(loaded, fingerprint="changed", output_path=output)


def test_corrupt_cache_is_not_silently_accepted(tmp_path: Path) -> None:
    cache = tmp_path / "incremental.json"
    cache.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid incremental build cache"):
        read_incremental_state(cache)


def test_documentation_covers_the_incremental_contract() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    for marker in (
        "compute_build_fingerprint",
        "is_incremental_hit",
        "write_incremental_state",
        "SHA-256",
        "timestamp",
        "atomico",
        "cache_version",
    ):
        assert marker in contract, f"Marker mancante: {marker}"
    assert all(
        not line.rstrip("\n").endswith((" ", "\t"))
        for line in contract.splitlines(keepends=True)
    )
