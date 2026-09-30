"""
EduTeX Resolver
Component: Resolver (COMP-RES-001)
Contracts: RES-001 (Resolution Contract), RES-002 (Resolution Error Contract)

Resolves relationships and references between registered runtime entities.
Operates after the Registry registration window closes and before Activator runs.

Responsibilities:
  - Read all registered entities from Registry (REG-001).
  - Identify and traverse declared references between entities.
  - Detect unresolvable references and circular dependencies.
  - Produce the resolved entity graph (RES-001) for Activator.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from edutex.core.errors import ResolverError
from edutex.registry.models import EntityRecord, EntityType
from edutex.registry.registry import Registry


class _FrozenList(list):
    """List-compatible collection that rejects all mutations."""

    def _reject(self, *args, **kwargs):
        raise TypeError("ResolvedGraph collections are immutable.")

    __setitem__ = _reject
    __delitem__ = _reject
    __iadd__ = _reject
    __imul__ = _reject
    append = _reject
    clear = _reject
    extend = _reject
    insert = _reject
    pop = _reject
    remove = _reject
    reverse = _reject
    sort = _reject


@dataclass
class ResolvedEdge:
    """A resolved directional relationship between two entities."""
    source_id:      str
    source_type:    EntityType
    target_id:      str
    target_type:    EntityType
    reference_type: str


@dataclass
class ResolvedGraph:
    """
    The resolved entity graph produced by the Resolver (RES-001).

    Immutable after the resolution pass completes (RES-C-007).
    Contains all registered entities and their resolved relationship edges.
    """
    entities: list[EntityRecord]
    edges:    list[ResolvedEdge] = field(default_factory=list)
    _frozen:  bool = field(default=False, init=False, repr=False)

    def freeze(self) -> None:
        """Freeze the graph; no further modifications are allowed."""
        if self._frozen:
            return
        self.entities = _FrozenList(self.entities)
        self.edges = _FrozenList(self.edges)
        self._frozen = True

    def get(self, entity_type: EntityType, entity_id: str) -> EntityRecord | None:
        """Look up an entity in the resolved graph."""
        for e in self.entities:
            if e.entity_type == entity_type and e.entity_id == entity_id:
                return e
        return None

    def edges_from(self, entity_id: str) -> list[ResolvedEdge]:
        """Return all outgoing edges from a given entity."""
        return [e for e in self.edges if e.source_id == entity_id]


class Resolver:
    """
    Resolves the entity graph from the Registry (COMP-RES-001).

    Usage:
        resolver = Resolver(registry)
        graph = resolver.resolve()   # raises ResolverError on failure
    """

    def __init__(self, registry: Registry) -> None:
        self._registry = registry

    def resolve(self) -> ResolvedGraph:
        """
        Perform the resolution pass.

        Returns:
            A frozen ResolvedGraph (RES-001).

        Raises:
            ResolverError: On unresolvable references (RES-C-005)
                           or circular dependencies (RES-C-006).
        """
        if self._registry.is_open:
            raise ResolverError(
                "Resolution cannot begin before the registration window closes (RES-C-004)."
            )

        entities = self._registry.get_all()
        edges: list[ResolvedEdge] = []
        errors: list[str] = []

        # Pass 1: resolve all declared references
        for entity in entities:
            for ref in entity.references:
                target = self._registry.get(ref.target_type, ref.target_id)
                if target is None:
                    if ref.optional:
                        continue
                    errors.append(
                        f"Unresolvable reference: "
                        f"'{entity.entity_id}' ({entity.entity_type.name}) "
                        f"→ '{ref.target_id}' ({ref.target_type.name}) "
                        f"[{ref.reference_type}]"
                    )
                else:
                    edges.append(ResolvedEdge(
                        source_id=entity.entity_id,
                        source_type=entity.entity_type,
                        target_id=ref.target_id,
                        target_type=ref.target_type,
                        reference_type=ref.reference_type,
                    ))

        if errors:
            raise ResolverError(
                "Resolution failed — unresolvable references:\n" + "\n".join(f"  - {e}" for e in errors)
            )

        # Pass 2: detect circular dependencies via DFS
        graph = ResolvedGraph(entities=entities, edges=edges)
        cycle = self._detect_cycle(graph)
        if cycle:
            raise ResolverError(
                f"Resolution failed — circular dependency detected: {' → '.join(cycle)}"
            )

        graph.freeze()
        return graph

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _detect_cycle(self, graph: ResolvedGraph) -> list[str] | None:
        """
        DFS-based cycle detection on the resolved entity graph.
        Returns the cycle path if found, None otherwise.
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {e.entity_id: WHITE for e in graph.entities}
        parent: dict[str, str | None] = {e.entity_id: None for e in graph.entities}

        def dfs(node_id: str) -> list[str] | None:
            color[node_id] = GRAY
            for edge in graph.edges_from(node_id):
                neighbor = edge.target_id
                if neighbor not in color:
                    continue  # external reference, already validated
                if color[neighbor] == GRAY:
                    # reconstruct cycle
                    cycle = [neighbor, node_id]
                    cur = node_id
                    while parent[cur] and parent[cur] != neighbor:
                        cur = parent[cur]  # type: ignore[assignment]
                        cycle.append(cur)
                    cycle.append(neighbor)
                    return list(reversed(cycle))
                if color[neighbor] == WHITE:
                    parent[neighbor] = node_id
                    result = dfs(neighbor)
                    if result:
                        return result
            color[node_id] = BLACK
            return None

        for entity in graph.entities:
            if color[entity.entity_id] == WHITE:
                result = dfs(entity.entity_id)
                if result:
                    return result
        return None
