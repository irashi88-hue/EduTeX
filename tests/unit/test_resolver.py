"""Unit tests — Resolver (COMP-RES-001)"""
import sys
sys.path.insert(0, "/opt/pysite")
sys.path.insert(0, "/home/user/edutex/src")

from pathlib import Path
from edutex.registry.models import EntityRecord, EntityType, EntityReference
from edutex.registry.registry import Registry
from edutex.resolver.resolver import Resolver, ResolvedEdge, ResolvedGraph
from edutex.core.errors import ResolverError

def make_registry(*records):
    reg = Registry()
    for r in records:
        reg.register(r)
    reg.close_registration_window()
    return reg

def test_public_resolver_api_exports_contract():
    import edutex.resolver as public_resolver

    assert public_resolver.Resolver is Resolver
    assert public_resolver.ResolvedGraph is ResolvedGraph
    assert public_resolver.ResolvedEdge is ResolvedEdge
    assert "Resolver" in public_resolver.__all__


def test_resolve_no_references():
    reg = make_registry(
        EntityRecord("km-001", EntityType.KNOWLEDGE_MODEL, Path("a.md")),
        EntityRecord("theme-default", EntityType.THEME, Path("t")),
    )
    graph = Resolver(reg).resolve()
    assert len(graph.entities) == 2
    assert graph.edges == []

def test_resolve_valid_reference():
    km = EntityRecord("km-001", EntityType.KNOWLEDGE_MODEL, Path("a.md"),
                      references=[EntityReference("uses", "theme-default", EntityType.THEME)])
    theme = EntityRecord("theme-default", EntityType.THEME, Path("t"))
    reg = make_registry(km, theme)
    graph = Resolver(reg).resolve()
    assert len(graph.edges) == 1
    assert graph.edges[0].source_id == "km-001"
    assert graph.edges[0].target_id == "theme-default"

def test_unresolvable_reference_raises():
    km = EntityRecord("km-001", EntityType.KNOWLEDGE_MODEL, Path("a.md"),
                      references=[EntityReference("uses", "nonexistent-theme", EntityType.THEME)])
    reg = make_registry(km)
    try:
        Resolver(reg).resolve()
        assert False, "should have raised"
    except ResolverError as e:
        assert "Unresolvable" in str(e)

def test_optional_reference_does_not_raise():
    km = EntityRecord("km-001", EntityType.KNOWLEDGE_MODEL, Path("a.md"),
                      references=[EntityReference("uses", "missing", EntityType.THEME, optional=True)])
    reg = make_registry(km)
    graph = Resolver(reg).resolve()
    assert graph.edges == []

def test_circular_dependency_raises():
    a = EntityRecord("a", EntityType.COMPONENT, Path("a"),
                     references=[EntityReference("uses", "b", EntityType.COMPONENT)])
    b = EntityRecord("b", EntityType.COMPONENT, Path("b"),
                     references=[EntityReference("uses", "a", EntityType.COMPONENT)])
    reg = make_registry(a, b)
    try:
        Resolver(reg).resolve()
        assert False, "should have raised"
    except ResolverError as e:
        assert "circular" in str(e).lower()

def test_resolved_graph_freezes_collections():
    graph = Resolver(
        make_registry(
            EntityRecord(
                "km-001",
                EntityType.KNOWLEDGE_MODEL,
                Path("assets/km/example.md"),
            )
        )
    ).resolve()

    try:
        graph.entities.append(
            EntityRecord(
                "km-002",
                EntityType.KNOWLEDGE_MODEL,
                Path("assets/km/other.md"),
            )
        )
    except (AttributeError, TypeError):
        pass
    else:
        raise AssertionError("ResolvedGraph.entities remains mutable after freeze")

    try:
        graph.edges.clear()
    except (AttributeError, TypeError):
        pass
    else:
        raise AssertionError("ResolvedGraph.edges remains mutable after freeze")


def test_resolve_before_window_closes_raises():
    reg = Registry()
    reg.register(EntityRecord("km-001", EntityType.KNOWLEDGE_MODEL, Path("a.md")))
    # window still open
    try:
        Resolver(reg).resolve()
        assert False, "should have raised"
    except ResolverError as e:
        assert "registration window" in str(e).lower()

def test_graph_is_frozen():
    reg = make_registry(EntityRecord("km-001", EntityType.KNOWLEDGE_MODEL, Path("a.md")))
    graph = Resolver(reg).resolve()
    assert graph._frozen is True

print("Running resolver tests...")
test_resolve_no_references();         print("  OK test_resolve_no_references")
test_resolve_valid_reference();       print("  OK test_resolve_valid_reference")
test_unresolvable_reference_raises(); print("  OK test_unresolvable_reference_raises")
test_optional_reference_does_not_raise(); print("  OK test_optional_reference_does_not_raise")
test_circular_dependency_raises();    print("  OK test_circular_dependency_raises")
test_resolve_before_window_closes_raises(); print("  OK test_resolve_before_window_closes_raises")
test_graph_is_frozen();               print("  OK test_graph_is_frozen")
print("Resolver: 7/7 passed")
