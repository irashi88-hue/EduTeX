"""Unit tests for the Knowledge public contracts."""

from pathlib import Path


def test_public_knowledge_api_exports_contract():
    import edutex.knowledge as public_knowledge
    from edutex.knowledge.loader import KnowledgeModelMeta, load_knowledge_model
    from edutex.knowledge.models import ContentModel, ContentNode, TextBlock
    from edutex.knowledge.service import KnowledgeService

    expected = {
        "ContentModel": ContentModel,
        "ContentNode": ContentNode,
        "KnowledgeModelMeta": KnowledgeModelMeta,
        "KnowledgeService": KnowledgeService,
        "TextBlock": TextBlock,
        "load_knowledge_model": load_knowledge_model,
    }

    for name, expected_value in expected.items():
        assert getattr(public_knowledge, name) is expected_value
        assert name in public_knowledge.__all__


def test_knowledge_service_contract_requires_processing():
    import pytest

    from edutex.core.errors import KnowledgeError
    from edutex.knowledge import KnowledgeService

    service = KnowledgeService()

    with pytest.raises(KnowledgeError, match="process"):
        _ = service.content

    with pytest.raises(KnowledgeError, match="process"):
        _ = service.meta

def test_knowledge_service_does_not_expose_mutable_state(tmp_path: Path):
    from edutex.activator.activator import ActivatedEntity, ActivatedState
    from edutex.knowledge import KnowledgeService
    from edutex.registry.models import EntityRecord, EntityType

    source = tmp_path / "knowledge.md"
    source.write_text(
        """---
id: km-001
title: Test Knowledge Model
language: it
level: A1
version: 1.0.0
tags:
  - grammar
---

Plain educational content.
""",
        encoding="utf-8",
    )

    record = EntityRecord(
        "km-001",
        EntityType.KNOWLEDGE_MODEL,
        Path("knowledge.md"),
    )
    state = ActivatedState([ActivatedEntity(record=record)])

    service = KnowledgeService()
    service.process(state, tmp_path)

    exposed_content = service.content
    exposed_meta = service.meta

    exposed_content.items.clear()
    exposed_meta.tags.append("mutated")

    assert len(service.content) == 1
    assert service.meta.tags == ["grammar"]
