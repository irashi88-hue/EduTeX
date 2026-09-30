"""
EduTeX Registry — Entity Models
Component: Registry (COMP-REG-001)
Contract: REG-002 (Entity Registration Contract)

Defines the data models for all registrable runtime entities.
Every entity registered with the Registry SHALL conform to one of these models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path


class EntityType(Enum):
    """
    Recognized runtime entity types.
    Defined by REG-002 (Entity Registration Contract).
    """
    KNOWLEDGE_MODEL = auto()
    THEME            = auto()
    LAYOUT           = auto()
    EXTENSION        = auto()
    COMPONENT        = auto()


@dataclass
class EntityRecord:
    """
    A single registered runtime entity.

    Every entity in the Registry is represented as an EntityRecord.
    EntityRecords are immutable after registration (REG-C-003).
    """
    entity_id:   str
    entity_type: EntityType
    source_path: Path
    metadata:    dict[str, object] = field(default_factory=dict)

    # Optional declared references to other entities (used by Resolver)
    references:  list[EntityReference] = field(default_factory=list)

    def __hash__(self) -> int:
        return hash((self.entity_id, self.entity_type))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EntityRecord):
            return NotImplemented
        return self.entity_id == other.entity_id and self.entity_type == other.entity_type


@dataclass
class EntityReference:
    """
    A declared reference from one entity to another.
    Used by the Resolver (RES-001) to build the resolved entity graph.
    """
    reference_type: str        # e.g. "requires", "extends", "uses"
    target_id:      str        # entity_id of the target entity
    target_type:    EntityType # expected type of the target entity
    optional:       bool = False
