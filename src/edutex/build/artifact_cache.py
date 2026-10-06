"""Atomic, integrity-checked storage for opt-in EduTeX build artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO


ARTIFACT_CACHE_VERSION = "1.0.0"
ARTIFACT_CACHE_SCHEMA = "edutex.build-artifact-cache.v1"
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_CHUNK_SIZE = 1024 * 1024


class ArtifactCacheError(RuntimeError):
    """Raised when cache state is invalid, corrupt, or cannot be written."""


@dataclass(frozen=True)
class ArtifactCacheResult:
    """Stable result returned by artifact-cache store and restore operations."""

    hit: bool
    fingerprint: str
    artifact_sha256: str | None
    size_bytes: int | None
    path: Path


class ArtifactCache:
    """Opt-in artifact store indexed by a build fingerprint."""

    def __init__(self, cache_dir: Path) -> None:
        if not isinstance(cache_dir, Path):
            raise TypeError("cache_dir must be a pathlib.Path")
        self.cache_dir = cache_dir

    def store(self, fingerprint: str, artifact_path: Path) -> ArtifactCacheResult:
        """Store one completed artifact; identical keys must map to identical bytes."""
        key = self._validate_fingerprint(fingerprint)
        if not isinstance(artifact_path, Path):
            raise TypeError("artifact_path must be a pathlib.Path")
        if not artifact_path.is_file():
            raise ArtifactCacheError(f"Artifact file does not exist: {artifact_path}")

        entry_dir, data_path, metadata_path = self._paths(key)
        entry_dir.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()
        size = 0
        temporary_data: Path | None = None
        try:
            with artifact_path.open("rb") as source, tempfile.NamedTemporaryFile(
                mode="wb", dir=entry_dir, prefix=".artifact-", suffix=".tmp", delete=False
            ) as target:
                temporary_data = Path(target.name)
                size = self._copy_and_hash(source, target, digest)
                target.flush()
                os.fsync(target.fileno())

            digest_value = digest.hexdigest()
            if metadata_path.exists() != data_path.exists():
                raise ArtifactCacheError(f"Incomplete cache entry for fingerprint {key}")
            if metadata_path.exists():
                previous = self._read_metadata(key, metadata_path)
                if previous["artifact_sha256"] != digest_value or previous["size_bytes"] != size:
                    raise ArtifactCacheError(
                        f"Fingerprint {key} already maps to different artifact content"
                    )

            os.replace(temporary_data, data_path)
            temporary_data = None
            metadata = {
                "artifact_sha256": digest_value,
                "cache_version": ARTIFACT_CACHE_VERSION,
                "fingerprint": key,
                "schema": ARTIFACT_CACHE_SCHEMA,
                "size_bytes": size,
            }
            self._atomic_write_metadata(metadata_path, metadata)
        except ArtifactCacheError:
            raise
        except OSError as exc:
            raise ArtifactCacheError(f"Could not store artifact for {key}: {exc}") from exc
        finally:
            if temporary_data is not None:
                temporary_data.unlink(missing_ok=True)

        return ArtifactCacheResult(True, key, digest_value, size, data_path)

    def restore(self, fingerprint: str, destination: Path) -> ArtifactCacheResult:
        """Restore an artifact atomically, returning a cache miss when absent."""
        key = self._validate_fingerprint(fingerprint)
        if not isinstance(destination, Path):
            raise TypeError("destination must be a pathlib.Path")
        _entry_dir, data_path, metadata_path = self._paths(key)
        if not data_path.exists() and not metadata_path.exists():
            return ArtifactCacheResult(False, key, None, None, destination)
        if not data_path.is_file() or not metadata_path.is_file():
            raise ArtifactCacheError(f"Incomplete cache entry for fingerprint {key}")

        metadata = self._read_metadata(key, metadata_path)
        digest = hashlib.sha256()
        size = 0
        temporary_output: Path | None = None
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with data_path.open("rb") as source, tempfile.NamedTemporaryFile(
                mode="wb", dir=destination.parent, prefix=f".{destination.name}.",
                suffix=".tmp", delete=False
            ) as target:
                temporary_output = Path(target.name)
                size = self._copy_and_hash(source, target, digest)
                target.flush()
                os.fsync(target.fileno())

            if digest.hexdigest() != metadata["artifact_sha256"] or size != metadata["size_bytes"]:
                raise ArtifactCacheError(f"Artifact integrity check failed for fingerprint {key}")
            os.replace(temporary_output, destination)
            temporary_output = None
        except ArtifactCacheError:
            raise
        except OSError as exc:
            raise ArtifactCacheError(f"Could not restore artifact for {key}: {exc}") from exc
        finally:
            if temporary_output is not None:
                temporary_output.unlink(missing_ok=True)

        return ArtifactCacheResult(
            True, key, str(metadata["artifact_sha256"]), int(metadata["size_bytes"]), destination
        )

    def _paths(self, fingerprint: str) -> tuple[Path, Path, Path]:
        directory = self.cache_dir / ARTIFACT_CACHE_VERSION / fingerprint[:2]
        return (
            directory,
            directory / f"{fingerprint}.artifact",
            directory / f"{fingerprint}.json",
        )

    @staticmethod
    def _validate_fingerprint(fingerprint: str) -> str:
        if not isinstance(fingerprint, str) or _SHA256_PATTERN.fullmatch(fingerprint) is None:
            raise ArtifactCacheError("Fingerprint must be a lowercase 64-character SHA-256 hex string")
        return fingerprint

    @staticmethod
    def _copy_and_hash(source: BinaryIO, target: BinaryIO, digest: object) -> int:
        size = 0
        while chunk := source.read(_CHUNK_SIZE):
            target.write(chunk)
            digest.update(chunk)  # type: ignore[attr-defined]
            size += len(chunk)
        return size

    @staticmethod
    def _atomic_write_metadata(path: Path, metadata: dict[str, object]) -> None:
        payload = json.dumps(metadata, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="\n", dir=path.parent,
                prefix=".metadata-", suffix=".tmp", delete=False
            ) as stream:
                temporary = Path(stream.name)
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
            temporary = None
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    @staticmethod
    def _read_metadata(fingerprint: str, path: Path) -> dict[str, object]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ArtifactCacheError(f"Invalid artifact-cache metadata for {fingerprint}: {exc}") from exc
        if not isinstance(value, dict):
            raise ArtifactCacheError(f"Invalid artifact-cache metadata for {fingerprint}: expected object")
        expected_keys = {"artifact_sha256", "cache_version", "fingerprint", "schema", "size_bytes"}
        if set(value) != expected_keys:
            raise ArtifactCacheError(f"Invalid artifact-cache metadata fields for {fingerprint}")
        if value.get("schema") != ARTIFACT_CACHE_SCHEMA:
            raise ArtifactCacheError(f"Unsupported artifact-cache schema for {fingerprint}")
        if value.get("cache_version") != ARTIFACT_CACHE_VERSION:
            raise ArtifactCacheError(f"Unsupported artifact-cache version for {fingerprint}")
        if value.get("fingerprint") != fingerprint:
            raise ArtifactCacheError(f"Artifact-cache fingerprint mismatch for {fingerprint}")
        digest = value.get("artifact_sha256")
        if not isinstance(digest, str) or _SHA256_PATTERN.fullmatch(digest) is None:
            raise ArtifactCacheError(f"Invalid artifact SHA-256 for {fingerprint}")
        size = value.get("size_bytes")
        if type(size) is not int or size < 0:
            raise ArtifactCacheError(f"Invalid artifact size for {fingerprint}")
        return value
