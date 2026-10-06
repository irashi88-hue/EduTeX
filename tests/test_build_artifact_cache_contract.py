from __future__ import annotations

import json
from pathlib import Path

import pytest

from edutex.build.artifact_cache import (
    ARTIFACT_CACHE_SCHEMA,
    ARTIFACT_CACHE_VERSION,
    ArtifactCache,
    ArtifactCacheError,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "BUILD_ARTIFACT_CACHE_CONTRACT.md"
IMPLEMENTATION = ROOT / "src" / "edutex" / "build" / "artifact_cache.py"
KEY = "a" * 64


def test_store_and_restore_round_trip_artifact_bytes(tmp_path: Path) -> None:
    source = tmp_path / "rendered.bin"
    source.write_bytes(b"artifact\x00bytes\xff")
    destination = tmp_path / "out" / "restored.bin"
    cache = ArtifactCache(tmp_path / "cache")

    stored = cache.store(KEY, source)
    restored = cache.restore(KEY, destination)

    assert stored.hit is True
    assert restored.hit is True
    assert restored.fingerprint == KEY
    assert restored.artifact_sha256 == stored.artifact_sha256
    assert restored.size_bytes == len(b"artifact\x00bytes\xff")
    assert destination.read_bytes() == source.read_bytes()


def test_restore_of_absent_key_is_a_noop(tmp_path: Path) -> None:
    destination = tmp_path / "output.bin"
    result = ArtifactCache(tmp_path / "cache").restore(KEY, destination)

    assert result.hit is False
    assert result.path == destination
    assert not destination.exists()


def test_fingerprint_must_be_sha256_hex_and_cannot_escape_cache_root(tmp_path: Path) -> None:
    cache = ArtifactCache(tmp_path / "cache")
    for invalid in ("../outside", "A" * 64, "a" * 63, "g" * 64, ""):
        with pytest.raises(ArtifactCacheError, match="64-character SHA-256"):
            cache.restore(invalid, tmp_path / "out.bin")
    assert not (tmp_path / "outside").exists()


def test_same_fingerprint_cannot_map_to_different_artifact_content(tmp_path: Path) -> None:
    cache = ArtifactCache(tmp_path / "cache")
    first = tmp_path / "first.bin"
    second = tmp_path / "second.bin"
    first.write_bytes(b"first")
    second.write_bytes(b"different")

    cache.store(KEY, first)
    with pytest.raises(ArtifactCacheError, match="different artifact content"):
        cache.store(KEY, second)


def test_corrupted_artifact_does_not_replace_existing_destination(tmp_path: Path) -> None:
    cache = ArtifactCache(tmp_path / "cache")
    source = tmp_path / "source.bin"
    source.write_bytes(b"original artifact")
    cache.store(KEY, source)
    _directory, data_path, _metadata_path = cache._paths(KEY)
    data_path.write_bytes(b"corrupt")
    destination = tmp_path / "destination.bin"
    destination.write_bytes(b"keep existing")

    with pytest.raises(ArtifactCacheError, match="integrity check failed"):
        cache.restore(KEY, destination)
    assert destination.read_bytes() == b"keep existing"


def test_incomplete_or_invalid_metadata_is_rejected(tmp_path: Path) -> None:
    cache = ArtifactCache(tmp_path / "cache")
    source = tmp_path / "source.bin"
    source.write_bytes(b"bytes")
    cache.store(KEY, source)
    _directory, _data_path, metadata_path = cache._paths(KEY)
    metadata_path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(ArtifactCacheError, match="Invalid artifact-cache metadata"):
        cache.restore(KEY, tmp_path / "restored.bin")


def test_cache_metadata_is_stable_and_contains_no_timestamps_or_source_paths(tmp_path: Path) -> None:
    cache = ArtifactCache(tmp_path / "cache")
    source = tmp_path / "source.bin"
    source.write_bytes(b"stable")
    cache.store(KEY, source)
    _directory, _data_path, metadata_path = cache._paths(KEY)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    assert metadata == {
        "artifact_sha256": __import__("hashlib").sha256(b"stable").hexdigest(),
        "cache_version": ARTIFACT_CACHE_VERSION,
        "fingerprint": KEY,
        "schema": ARTIFACT_CACHE_SCHEMA,
        "size_bytes": 6,
    }
    assert "timestamp" not in metadata
    assert "source_path" not in metadata


def test_missing_source_artifact_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ArtifactCacheError, match="does not exist"):
        ArtifactCache(tmp_path / "cache").store(KEY, tmp_path / "missing.bin")


def test_documentation_and_implementation_markers_are_present() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    implementation = IMPLEMENTATION.read_text(encoding="utf-8")
    for marker in ("opt-in", "sha256", "atomica", "timestamp", "cache miss", "fingerprint"):
        assert marker in contract
    for marker in ("ArtifactCache", "ArtifactCacheResult", "ArtifactCacheError", "hashlib.sha256", "os.replace"):
        assert marker in implementation
