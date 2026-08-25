"""
EduTeX Registry
Component: Registry (COMP-REG-001)
Contracts: REG-001 (Registry Contract), REG-002 (Entity Registration Contract)

Maintains the authoritative registry of runtime entities managed by the framework.
The Registry is the single source of truth for all registered entities.

Lifecycle:
  - Registration window: open between REGISTERING and RESOLVING phases.
  - After the registration window closes, the registry becomes read-only.
  - The Resolver consumes the registry through REG-001 after the window closes.
"""

from __future__ import annotations

from edutex.core.errors import RegistryError
from edutex.registry.models import EntityRecord, EntityType


class Registry:
    """
    Authoritative registry of runtime entities (REG-001).

    Entities are registered during the REGISTERING lifecycle phase.
    After the registration window closes, no further registrations are accepted.
    """

    def __init__(self) -> None:
        self._entities: dict[tuple[EntityType, str], EntityRecord] = {}
        self._open: bool = True   # registration window

    # ------------------------------------------------------------------
    # REG-001 — Registry Contract (read interface, used by Resolver)
    # ------------------------------------------------------------------

    def get_all(self) -> list[EntityRecord]:
        """
        Return all registered entities.
        Available to the Resolver after the registration window closes (REG-001).
        """
        return list(self._entities.values())

    def get(self, entity_type: EntityType, entity_id: str) -> EntityRecord | None:
        """
        Return a single entity by type and ID, or None if not found.
        """
        return self._entities.get((entity_type, entity_id))

    def get_by_type(self, entity_type: EntityType) -> list[EntityRecord]:
        """
        Return all entities of a given type.
        """
        return [e for (t, _), e in self._entities.items() if t == entity_type]

    def exists(self, entity_type: EntityType, entity_id: str) -> bool:
        """Return True if an entity with the given type and ID is registered."""
        return (entity_type, entity_id) in self._entities

    # ------------------------------------------------------------------
    # REG-002 — Entity Registration Contract (write interface)
    # ------------------------------------------------------------------

    def register(self, record: EntityRecord) -> None:
        """
        Register a new entity record.

        Args:
            record: The entity to register.

        Raises:
            RegistryError: If the registration window is closed (REG-C-005),
                           or if a duplicate entity is registered (REG-C-004).
        """
        if not self._open:
            raise RegistryError(
                f"Registration window is closed. "
                f"Cannot register entity '{record.entity_id}' of type '{record.entity_type.name}'."
            )

        key = (record.entity_type, record.entity_id)
        if key in self._entities:
            raise RegistryError(
                f"Duplicate entity registration: "
                f"'{record.entity_id}' of type '{record.entity_type.name}' is already registered."
            )

        self._entities[key] = record

    def close_registration_window(self) -> None:
        """
        Close the registration window.

        After this call, no further registrations are accepted.
        The Resolver may begin consuming the registry through REG-001.
        """
        self._open = False

    @property
    def is_open(self) -> bool:
        """True if the registration window is still open."""
        return self._open

    def __len__(self) -> int:
        return len(self._entities)

    def __repr__(self) -> str:
        return f"Registry(entities={len(self._entities)}, open={self._open})"
