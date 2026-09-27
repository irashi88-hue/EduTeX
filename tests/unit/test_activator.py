"""Unit tests — Activator (COMP-ACT-001)"""
import sys
sys.path.insert(0, "/opt/pysite")
sys.path.insert(0, "/home/user/edutex/src")

from pathlib import Path
from edutex.registry.models import EntityRecord, EntityType, EntityReference
from edutex.registry.registry import Registry
from edutex.resolver.resolver import Resolver
from edutex.activator.activator import Activator, ActivatedState
from edutex.core.errors import ActivationError

def make_graph(*records):
    reg = Registry()
    for r in records:
        reg.register(r)
    reg.close_registration_window()
    return Resolver(reg).resolve()

def test_activated_state_does_not_expose_mutable_entities():
    graph = make_graph(
        EntityRecord("km-001", EntityType.KNOWLEDGE_MODEL, Path("a.md"))
    )
    state = Activator().activate(graph)

    exposed = state.get(EntityType.KNOWLEDGE_MODEL, "km-001")
    assert exposed is not None

    exposed.is_active = False

    stored = state.get(EntityType.KNOWLEDGE_MODEL, "km-001")
    assert stored is not None
    assert stored.is_active


def test_activate_single_entity():
    graph = make_graph(EntityRecord("km-001", EntityType.KNOWLEDGE_MODEL, Path("a.md")))
    state = Activator().activate(graph)
    assert isinstance(state, ActivatedState)
    assert len(state) == 1
    e = state.get(EntityType.KNOWLEDGE_MODEL, "km-001")
    assert e is not None
    assert e.is_active

def test_activation_order_is_deterministic_for_independent_entities():
    graph = make_graph(
        EntityRecord("component-b", EntityType.COMPONENT, Path("b")),
        EntityRecord("component-a", EntityType.COMPONENT, Path("a")),
        EntityRecord("component-c", EntityType.COMPONENT, Path("c")),
    )

    activator = Activator()
    activator.activate(graph)

    ids = [entity.entity_id for entity in activator._activated]
    assert ids == ["component-a", "component-b", "component-c"]


def test_activation_order_dependency_first():
    # b depends on a → a must be activated first
    a = EntityRecord("a", EntityType.COMPONENT, Path("a"))
    b = EntityRecord("b", EntityType.COMPONENT, Path("b"),
                     references=[EntityReference("uses", "a", EntityType.COMPONENT)])
    graph = make_graph(a, b)
    activator = Activator()
    state = activator.activate(graph)
    ids = [e.entity_id for e in activator._activated]
    assert ids.index("a") < ids.index("b"), f"Expected a before b, got: {ids}"

def test_deactivate():
    graph = make_graph(
        EntityRecord("km-001", EntityType.KNOWLEDGE_MODEL, Path("a.md")),
        EntityRecord("theme-default", EntityType.THEME, Path("t")),
    )
    activator = Activator()
    activator.activate(graph)
    activator.deactivate()
    assert activator.state is None
    assert activator._activated == []

def test_get_by_type():
    graph = make_graph(
        EntityRecord("km-001", EntityType.KNOWLEDGE_MODEL, Path("a.md")),
        EntityRecord("km-002", EntityType.KNOWLEDGE_MODEL, Path("b.md")),
        EntityRecord("theme-default", EntityType.THEME, Path("t")),
    )
    state = Activator().activate(graph)
    kms = state.get_by_type(EntityType.KNOWLEDGE_MODEL)
    assert len(kms) == 2

def test_get_first():
    graph = make_graph(EntityRecord("theme-default", EntityType.THEME, Path("t")))
    state = Activator().activate(graph)
    e = state.get_first(EntityType.THEME)
    assert e is not None
    assert e.entity_id == "theme-default"

def test_get_first_missing_returns_none():
    graph = make_graph(EntityRecord("km-001", EntityType.KNOWLEDGE_MODEL, Path("a.md")))
    state = Activator().activate(graph)
    assert state.get_first(EntityType.THEME) is None

print("Running activator tests...")
test_activate_single_entity();        print("  OK test_activate_single_entity")
test_activation_order_dependency_first(); print("  OK test_activation_order_dependency_first")
test_deactivate();                    print("  OK test_deactivate")
test_get_by_type();                   print("  OK test_get_by_type")
test_get_first();                     print("  OK test_get_first")
test_get_first_missing_returns_none();print("  OK test_get_first_missing_returns_none")
print("Activator: 6/6 passed")
