"""
EduTeX Runtime Context
Component: Core (COMP-CORE-001)
Contract: CC-001 (Runtime Context Contract)

Provides the shared Runtime Context accessible to all framework components.
The Runtime Context is the single authoritative source of runtime state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

from edutex.core.errors import EduTeXError


class LifecyclePhase(Enum):
    """
    EduTeX Runtime Lifecycle phases.
    Contract: CC-002 (Lifecycle Contract)
    """
    INITIALIZING = auto()
    CONFIGURING = auto()
    REGISTERING = auto()
    RESOLVING = auto()
    ACTIVATING = auto()
    PROCESSING = auto()
    BUILDING = auto()
    COMPLETE = auto()
    FAILED = auto()


_ALLOWED_LIFECYCLE_TRANSITIONS: dict[
    LifecyclePhase, frozenset[LifecyclePhase]
] = {
    LifecyclePhase.INITIALIZING: frozenset(
        {LifecyclePhase.CONFIGURING, LifecyclePhase.FAILED}
    ),
    LifecyclePhase.CONFIGURING: frozenset(
        {LifecyclePhase.REGISTERING, LifecyclePhase.FAILED}
    ),
    LifecyclePhase.REGISTERING: frozenset(
        {LifecyclePhase.RESOLVING, LifecyclePhase.FAILED}
    ),
    LifecyclePhase.RESOLVING: frozenset(
        {LifecyclePhase.ACTIVATING, LifecyclePhase.FAILED}
    ),
    LifecyclePhase.ACTIVATING: frozenset(
        {LifecyclePhase.PROCESSING, LifecyclePhase.FAILED}
    ),
    LifecyclePhase.PROCESSING: frozenset(
        {LifecyclePhase.BUILDING, LifecyclePhase.FAILED}
    ),
    LifecyclePhase.BUILDING: frozenset(
        {LifecyclePhase.COMPLETE, LifecyclePhase.FAILED}
    ),
    LifecyclePhase.COMPLETE: frozenset(),
    LifecyclePhase.FAILED: frozenset(),
}


@dataclass
class RuntimeContext:
    """
    Shared runtime context for the EduTeX framework session.
    Exposed through CC-001.

    All components receive a reference to this context at activation time.
    Components SHALL NOT modify fields they do not own.
    """
    project_root: Path
    phase: LifecyclePhase = LifecyclePhase.INITIALIZING
    metadata: dict[str, object] = field(default_factory=dict)

    def advance(self, phase: LifecyclePhase) -> None:
        """Advance the lifecycle to the next valid phase."""
        allowed = _ALLOWED_LIFECYCLE_TRANSITIONS[self.phase]
        if phase not in allowed:
            raise EduTeXError(
                "Invalid lifecycle transition: "
                f"{self.phase.name} -> {phase.name}"
            )
        self.phase = phase

    def set_metadata(self, key: str, value: object) -> None:
        """Store arbitrary metadata in the runtime context."""
        self.metadata[key] = value

    def get_metadata(self, key: str, default: object = None) -> object:
        """Retrieve metadata from the runtime context."""
        return self.metadata.get(key, default)
