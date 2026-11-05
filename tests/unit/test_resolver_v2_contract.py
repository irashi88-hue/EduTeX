"""V2 contract tests for Resolver graph identity and deterministic ordering."""

from pathlib import Path

from edutex.registry.models import EntityRecord, EntityReference, EntityType
from edutex.registry.registry import Registry
from edutex.resolver.resolver import Resolver


def resolve_records(records: list[EntityRecord]):
    registry = Registry()
    for record in records:
        registry.register(record)
    registry.close_registration_window()
    return Resolver(registry).resolve()


def entity_key(record: EntityRecord) -> tuple[str, str]:
    return (record.entity_type.name, record.entity_id)


def edge_key(edge) -> tuple[str, str, str, str, str]:
    return (
        edge.source_type.name,
        edge.source_id,
        edge.target_type.name,
        edge.target_id,
        edge.reference_type,
    )


def test_entities_and_edges_are_canonically_ordered_independent_of_registration_order():
    records = [
        EntityRecord(
            "km-z",
            EntityType.KNOWLEDGE_MODEL,
            Path("km-z.md"),
            references=[
                EntityReference("uses", "theme-z", EntityType.THEME),
                EntityReference("uses", "layout-a", EntityType.LAYOUT),
            ],
        ),
        EntityRecord("theme-z", EntityType.THEME, Path("theme-z.yaml")),
        EntityRecord("layout-a", EntityType.LAYOUT, Path("layout-a.yaml")),
        EntityRecord(
            "component-a",
            EntityType.COMPONENT,
            Path("component-a"),
            references=[
                EntityReference("uses", "theme-z", EntityType.THEME),
            ],
        ),
    ]

    graph_forward = resolve_records(records)
    graph_reverse = resolve_records(list(reversed(records)))

    expected_entities = sorted(entity_key(record) for record in records)
    forward_entities = [entity_key(record) for record in graph_forward.entities]
    reverse_entities = [entity_key(record) for record in graph_reverse.entities]

    assert forward_entities == expected_entities
    assert reverse_entities == expected_entities

    forward_edges = [edge_key(edge) for edge in graph_forward.edges]
    reverse_edges = [edge_key(edge) for edge in graph_reverse.edges]

    assert forward_edges == sorted(forward_edges)
    assert reverse_edges == sorted(reverse_edges)
    assert forward_edges == reverse_edges


def test_same_entity_id_under_different_types_is_not_a_cycle():
    component = EntityRecord(
        "shared-id",
        EntityType.COMPONENT,
        Path("component"),
        references=[
            EntityReference("uses", "shared-id", EntityType.THEME),
        ],
    )
    theme = EntityRecord(
        "shared-id",
        EntityType.THEME,
        Path("theme.yaml"),
    )

    graph = resolve_records([component, theme])

    assert len(graph.entities) == 2
    assert graph.get(EntityType.COMPONENT, "shared-id") is not None
    assert graph.get(EntityType.THEME, "shared-id") is not None
    assert len(graph.edges) == 1
    assert graph.edges[0].source_type is EntityType.COMPONENT
    assert graph.edges[0].target_type is EntityType.THEME