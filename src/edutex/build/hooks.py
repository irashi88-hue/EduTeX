"""Deterministic opt-in pre-build and post-build hook execution."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from types import MappingProxyType

from edutex.core.errors import BuildError


class BuildHookPhase(str, Enum):
    PRE_BUILD = "pre-build"
    POST_BUILD = "post-build"


@dataclass(frozen=True)
class BuildHookContext:
    """Read-only context shared with one build hook invocation."""

    project_root: Path
    output_format: str
    output_path: Path | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.output_format or self.output_format.strip() != self.output_format:
            raise ValueError("output_format must be a non-empty name without surrounding whitespace")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


BuildHookCallback = Callable[[BuildHookContext], None]


@dataclass(frozen=True)
class BuildHook:
    """One named callback registered for one lifecycle phase."""

    hook_id: str
    phase: BuildHookPhase
    callback: BuildHookCallback

    def __post_init__(self) -> None:
        if not self.hook_id or self.hook_id.strip() != self.hook_id:
            raise ValueError("hook_id must be a non-empty name without surrounding whitespace")
        if not isinstance(self.phase, BuildHookPhase):
            raise TypeError("phase must be a BuildHookPhase")
        if not callable(self.callback):
            raise TypeError("callback must be callable")


class BuildHookError(BuildError):
    """Typed build failure identifying the hook and lifecycle phase."""

    def __init__(self, hook_id: str, phase: BuildHookPhase, cause: Exception) -> None:
        self.hook_id = hook_id
        self.phase = phase
        self.cause = cause
        super().__init__(f"Build hook {hook_id!r} failed during {phase.value}: {cause}")


class BuildHookRegistry:
    """Registration and deterministic execution boundary for build hooks."""

    def __init__(self) -> None:
        self._hooks: list[BuildHook] = []
        self._ids: set[str] = set()
        self._frozen = False

    def register(self, hook: BuildHook) -> None:
        if self._frozen:
            raise RuntimeError("Build hook registry is frozen")
        if hook.hook_id in self._ids:
            raise ValueError(f"Duplicate build hook ID: {hook.hook_id}")
        self._hooks.append(hook)
        self._ids.add(hook.hook_id)

    def freeze(self) -> tuple[BuildHook, ...]:
        self._frozen = True
        return tuple(self._hooks)

    def hooks_for(self, phase: BuildHookPhase) -> tuple[BuildHook, ...]:
        if not isinstance(phase, BuildHookPhase):
            raise TypeError("phase must be a BuildHookPhase")
        return tuple(hook for hook in self._hooks if hook.phase is phase)

    def run(self, phase: BuildHookPhase, context: BuildHookContext) -> None:
        """Run matching hooks once in registration order."""
        for hook in self.hooks_for(phase):
            try:
                hook.callback(context)
            except Exception as exc:
                raise BuildHookError(hook.hook_id, phase, exc) from exc


def run_build_hooks(
    hooks: Iterable[BuildHook],
    phase: BuildHookPhase,
    context: BuildHookContext,
) -> None:
    """Run an opt-in hook sequence without reordering or swallowing failures."""
    registry = BuildHookRegistry()
    for hook in hooks:
        registry.register(hook)
    registry.freeze()
    registry.run(phase, context)
