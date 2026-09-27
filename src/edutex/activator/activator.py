"""
EduTeX Activator
Component: Activator (COMP-ACT-001)
Contracts: ACT-001 (Activation Contract), ACT-002 (Deactivation Contract)

Activates runtime entities according to the Runtime Lifecycle.
Consumes the resolved entity graph from the Resolver (RES-001).
Determines activation order by performing a topological sort on the graph.
"""

from __future__ import annotations

from collections import deque
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path

from edutex.core.errors import ActivationError
from edutex.registry.models import EntityRecord, EntityType
from edutex.resolver.resolver import ResolvedGraph


EntityKey = tuple[EntityType, str]   # composite key: (type, id)


@dataclass
class ActivatedEntity:
    """
    Represents a runtime entity that has been successfully activated.
    Exposed through ACT-001 to Framework Services.
    """
    record:       EntityRecord
    is_active:    bool = True
    runtime_data: dict[str, object] = field(default_factory=dict)

    @property
    def entity_id(self) -> str:
        return self.record.entity_id

    @property
    def entity_type(self) -> EntityType:
        return self.record.entity_type

    @property
    def source_path(self) -> Path:
        return self.record.source_path


class ActivatedState:
    """
    The activated framework state exposed through ACT-001.
    Provides read-only access to all activated entities.
    """

    def __init__(self, activated: list[ActivatedEntity]) -> None:
        self._entities: dict[EntityKey, ActivatedEntity] = {
            (e.entity_type, e.entity_id): e for e in activated
        }

    def get(self, entity_type: EntityType, entity_id: str) -> ActivatedEntity | None:
        entity = self._entities.get((entity_type, entity_id))
        return deepcopy(entity) if entity is not None else None

    def get_by_type(self, entity_type: EntityType) -> list[ActivatedEntity]:
        return [
            deepcopy(entity)
            for (entity_type_key, _), entity in self._entities.items()
            if entity_type_key == entity_type
        ]

    def get_first(self, entity_type: EntityType) -> ActivatedEntity | None:
        results = self.get_by_type(entity_type)
        return results[0] if results else None

    def all(self) -> list[ActivatedEntity]:
        return [deepcopy(entity) for entity in self._entities.values()]

    def __len__(self) -> int:
        return len(self._entities)

    def __repr__(self) -> str:
        return f"ActivatedState(entities={len(self._entities)})"


class Activator:
    """
    Activates runtime entities from the resolved entity graph (COMP-ACT-001).
    """

    def __init__(self) -> None:
        self._activated: list[ActivatedEntity] = []
        self._state: ActivatedState | None = None

    def activate(self, graph: ResolvedGraph) -> ActivatedState:
        """
        Activate all entities in dependency order (topological sort).

        Raises:
            ActivationError: If activation order cannot be determined.
        """
        order = self._topological_sort(graph)
        self._activated = [self._activate_entity(r) for r in order]
        self._state = ActivatedState(self._activated)
        return self._state

    def deactivate(self) -> None:
        """Deactivate all entities in reverse activation order (ACT-002)."""
        for entity in reversed(self._activated):
            entity.is_active = False
        self._activated = []
        self._state = None

    @property
    def state(self) -> ActivatedState | None:
        return self._state

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _activate_entity(self, record: EntityRecord) -> ActivatedEntity:
        return ActivatedEntity(record=record)

    def _topological_sort(self, graph: ResolvedGraph) -> list[EntityRecord]:
        """
        Kahn's algorithm — topological sort using composite (type, id) keys
        to avoid collisions between entities of different types sharing the same id.
        """
        # Map composite key → EntityRecord
        key_to_record: dict[EntityKey, EntityRecord] = {
            (e.entity_type, e.entity_id): e for e in graph.entities
        }
        all_keys: set[EntityKey] = set(key_to_record)

        in_degree:  dict[EntityKey, int]        = {k: 0 for k in all_keys}
        dependents: dict[EntityKey, list[EntityKey]] = {k: [] for k in all_keys}

        for edge in graph.edges:
            src = (edge.source_type, edge.source_id)
            tgt = (edge.target_type, edge.target_id)
            if src in all_keys and tgt in all_keys:
                # target must be activated before source
                in_degree[src] += 1
                dependents[tgt].append(src)

        queue: deque[EntityKey] = deque(k for k, deg in in_degree.items() if deg == 0)
        sorted_keys: list[EntityKey] = []

        while queue:
            node = queue.popleft()
            sorted_keys.append(node)
            for dep in dependents[node]:
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)

        if len(sorted_keys) != len(all_keys):
            raise ActivationError(
                "Activation order could not be determined — "
                "cycle detected in resolved entity graph."
            )

        return [key_to_record[k] for k in sorted_keys]
