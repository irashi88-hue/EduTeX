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

        entities = sorted(
            self._registry.get_all(),
            key=lambda entity: (entity.entity_type.name, entity.entity_id),
        )
        edges: list[ResolvedEdge] = []
        errors: list[str] = []
        missing_references: list[dict[str, object]] = []

        # Pass 1: resolve all declared references
        for entity in entities:
            for ref in sorted(
                entity.references,
                key=lambda ref: (
                    ref.target_type.name,
                    ref.target_id,
                    ref.reference_type,
                    ref.optional,
                ),
            ):
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
                    missing_references.append(
                        {
                            "source": {
                                "type": entity.entity_type.name.lower(),
                                "id": entity.entity_id,
                            },
                            "expected_target": {
                                "type": ref.target_type.name.lower(),
                                "id": ref.target_id,
                            },
                            "reference_type": ref.reference_type,
                        },
                    )
                else:
                    edges.append(ResolvedEdge(
                        source_id=entity.entity_id,
                        source_type=entity.entity_type,
                        target_id=ref.target_id,
                        target_type=ref.target_type,
                        reference_type=ref.reference_type,
                    ))

        edges.sort(
            key=lambda edge: (
                edge.source_type.name,
                edge.source_id,
                edge.target_type.name,
                edge.target_id,
                edge.reference_type,
            )
        )

        if errors:
            raise ResolverError(
                "Resolution failed \u2014 unresolvable references:\n"
                + "\n".join(f"  - {error}" for error in errors),
                code="RUNTIME_REFERENCE_MISSING",
                details={"missing_references": missing_references},
            )

        # Pass 2: detect circular dependencies via DFS
        graph = ResolvedGraph(entities=entities, edges=edges)
        cycle = self._detect_cycle(graph)
        if cycle:
            cycle_details = []
            for identity in cycle:
                entity_type, separator, entity_id = identity.partition(":")
                if not separator:
                    raise ResolverError(
                        "Cycle identity is not a typed entity identity."
                    )
                cycle_details.append(
                    {"type": entity_type.lower(), "id": entity_id}
                )
            cycle_text = " \u2192 ".join(cycle)
            raise ResolverError(
                f"Resolution failed \u2014 circular dependency detected: {cycle_text}",
                code="RUNTIME_DEPENDENCY_CYCLE",
                details={"cycle": cycle_details},
            )

        graph.freeze()
        return graph

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _detect_cycle(self, graph: ResolvedGraph) -> list[str] | None:
        """
        Detect cycles using typed entity identities.

        The returned cycle follows edge direction and starts at its
        canonically smallest identity.
        """
        identity_keys = [
            (entity.entity_type, entity.entity_id)
            for entity in graph.entities
        ]
        adjacency: dict[
            tuple[EntityType, str],
            list[tuple[EntityType, str]],
        ] = {identity: [] for identity in identity_keys}

        for edge in graph.edges:
            source = (edge.source_type, edge.source_id)
            target = (edge.target_type, edge.target_id)
            if source in adjacency and target in adjacency:
                adjacency[source].append(target)

        for neighbors in adjacency.values():
            neighbors.sort(key=lambda identity: (identity[0].name, identity[1]))

        WHITE, GRAY, BLACK = 0, 1, 2
        color = {identity: WHITE for identity in identity_keys}
        parent: dict[
            tuple[EntityType, str],
            tuple[EntityType, str] | None,
        ] = {identity: None for identity in identity_keys}

        def dfs(node: tuple[EntityType, str]) -> list[str] | None:
            color[node] = GRAY

            for neighbor in adjacency[node]:
                if color[neighbor] == GRAY:
                    chain = [node]
                    while chain[-1] != neighbor:
                        ancestor = parent[chain[-1]]
                        if ancestor is None:
                            return None
                        chain.append(ancestor)

                    cycle = list(reversed(chain))
                    smallest_index = min(
                        range(len(cycle)),
                        key=lambda index: (
                            cycle[index][0].name,
                            cycle[index][1],
                        ),
                    )
                    canonical_cycle = (
                        cycle[smallest_index:] + cycle[:smallest_index]
                    )
                    canonical_cycle.append(canonical_cycle[0])

                    return [
                        f"{entity_type.name}:{entity_id}"
                        for entity_type, entity_id in canonical_cycle
                    ]

                if color[neighbor] == WHITE:
                    parent[neighbor] = node
                    result = dfs(neighbor)
                    if result:
                        return result

            color[node] = BLACK
            return None

        for identity in sorted(
            identity_keys,
            key=lambda item: (item[0].name, item[1]),
        ):
            if color[identity] == WHITE:
                result = dfs(identity)
                if result:
                    return result

        return None
