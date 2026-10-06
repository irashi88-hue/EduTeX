"""Deterministic cache primitives for opt-in incremental builds."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


INCREMENTAL_CACHE_VERSION = "1.0.0"


@dataclass(frozen=True)
class IncrementalBuildState:
    """Persisted identity of one successfully generated build artifact."""

    fingerprint: str
    output_path: str
    cache_version: str = INCREMENTAL_CACHE_VERSION

    def to_dict(self) -> dict[str, str]:
        return {
            "cache_version": self.cache_version,
            "fingerprint": self.fingerprint,
            "output_path": self.output_path,
        }


def compute_build_fingerprint(
    inputs: Iterable[Path],
    *,
    configuration: str = "",
) -> str:
    """Hash ordered file identities, contents, and configuration deterministically."""
    digest = hashlib.sha256()
    for path in sorted((Path(item) for item in inputs), key=lambda item: item.as_posix()):
        resolved = path.resolve()
        digest.update(b"path\0")
        digest.update(resolved.as_posix().encode("utf-8"))
        digest.update(b"\0")
        if resolved.is_file():
            digest.update(b"file\0")
            digest.update(resolved.read_bytes())
        else:
            digest.update(b"missing\0")
    digest.update(b"configuration\0")
    digest.update(configuration.encode("utf-8"))
    return digest.hexdigest()


def read_incremental_state(path: Path) -> IncrementalBuildState | None:
    """Read a valid cache state, returning None for an absent cache."""
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid incremental build cache: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid incremental build cache: {path}")
    expected = {"cache_version", "fingerprint", "output_path"}
    if set(payload) != expected or any(not isinstance(payload[key], str) for key in expected):
        raise ValueError(f"Invalid incremental build cache: {path}")
    return IncrementalBuildState(
        cache_version=payload["cache_version"],
        fingerprint=payload["fingerprint"],
        output_path=payload["output_path"],
    )


def is_incremental_hit(
    state: IncrementalBuildState | None,
    *,
    fingerprint: str,
    output_path: Path,
) -> bool:
    """Return whether a cache state proves that an output is reusable."""
    return bool(
        state is not None
        and state.cache_version == INCREMENTAL_CACHE_VERSION
        and state.fingerprint == fingerprint
        and Path(state.output_path).resolve() == output_path.resolve()
        and output_path.is_file()
    )


def write_incremental_state(path: Path, state: IncrementalBuildState) -> None:
    """Atomically persist one cache state next to the build output."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        text=True,
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(state.to_dict(), stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise
