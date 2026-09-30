"""Unit tests — Registry (COMP-REG-001)"""
import sys
sys.path.insert(0, "/opt/pysite")
sys.path.insert(0, "/home/user/edutex/src")

from pathlib import Path
from edutex.registry.models import EntityRecord, EntityType, EntityReference
from edutex.registry.registry import Registry
from edutex.core.errors import RegistryError

def test_public_registry_api_exports_contract():
    import edutex.registry as public_registry

    assert public_registry.Registry is Registry
    assert public_registry.EntityRecord is EntityRecord
    assert public_registry.EntityReference is EntityReference
    assert public_registry.EntityType is EntityType
    assert "Registry" in public_registry.__all__


def test_register_and_retrieve():
    reg = Registry()
    rec = EntityRecord("km-001", EntityType.KNOWLEDGE_MODEL, Path("assets/km/example.md"))
    reg.register(rec)
    assert reg.exists(EntityType.KNOWLEDGE_MODEL, "km-001")
    assert reg.get(EntityType.KNOWLEDGE_MODEL, "km-001") == rec
    assert len(reg) == 1

def test_get_all():
    reg = Registry()
    reg.register(EntityRecord("km-001", EntityType.KNOWLEDGE_MODEL, Path("a.md")))
    reg.register(EntityRecord("theme-default", EntityType.THEME, Path("b")))
    assert len(reg.get_all()) == 2

def test_get_by_type():
    reg = Registry()
    reg.register(EntityRecord("km-001", EntityType.KNOWLEDGE_MODEL, Path("a.md")))
    reg.register(EntityRecord("km-002", EntityType.KNOWLEDGE_MODEL, Path("b.md")))
    reg.register(EntityRecord("theme-default", EntityType.THEME, Path("c")))
    kms = reg.get_by_type(EntityType.KNOWLEDGE_MODEL)
    assert len(kms) == 2

def test_closed_registry_does_not_expose_mutable_records():
    registry = Registry()
    record = EntityRecord(
        "km-001",
        EntityType.KNOWLEDGE_MODEL,
        Path("assets/km/example.md"),
    )
    registry.register(record)
    registry.close_registration_window()

    exposed = registry.get(EntityType.KNOWLEDGE_MODEL, "km-001")
    assert exposed is not None

    exposed.entity_id = "changed"
    exposed.metadata["changed"] = True

    stored = registry.get(EntityType.KNOWLEDGE_MODEL, "km-001")
    assert stored is not None
    assert stored.entity_id == "km-001"
    assert "changed" not in stored.metadata


def test_duplicate_raises():
    reg = Registry()
    rec = EntityRecord("km-001", EntityType.KNOWLEDGE_MODEL, Path("a.md"))
    reg.register(rec)
    try:
        reg.register(EntityRecord("km-001", EntityType.KNOWLEDGE_MODEL, Path("b.md")))
        assert False, "should have raised"
    except RegistryError:
        pass

def test_closed_window_raises():
    reg = Registry()
    reg.close_registration_window()
    try:
        reg.register(EntityRecord("km-001", EntityType.KNOWLEDGE_MODEL, Path("a.md")))
        assert False, "should have raised"
    except RegistryError:
        pass

def test_not_found_returns_none():
    reg = Registry()
    assert reg.get(EntityType.KNOWLEDGE_MODEL, "nonexistent") is None

print("Running registry tests...")
test_register_and_retrieve(); print("  OK test_register_and_retrieve")
test_get_all();               print("  OK test_get_all")
test_get_by_type();           print("  OK test_get_by_type")
test_duplicate_raises();      print("  OK test_duplicate_raises")
test_closed_window_raises();  print("  OK test_closed_window_raises")
test_not_found_returns_none();print("  OK test_not_found_returns_none")
print("Registry: 6/6 passed")
