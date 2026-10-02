"""Test del contratto pubblico di query del Content Model."""

from __future__ import annotations

from pathlib import Path

import pytest

from edutex.knowledge import ContentModel, ContentNode, ContentQuery, TextBlock, query_content


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "CONTENT_MODEL_QUERY_CONTRACT.md"


def make_model() -> ContentModel:
    nested = ContentNode(
        node_type="example",
        subtype="Simple",
        fields=["ciao", "hello"],
        body="Hello example",
    )
    return ContentModel(
        items=[
            TextBlock("Intro prose"),
            ContentNode(
                node_type="rule",
                subtype="simple",
                fields=["present"],
                body="The present tense",
                children=[nested],
            ),
            ContentNode(
                node_type="vocab",
                subtype=None,
                fields=["casa"],
                body="house",
            ),
        ]
    )


def test_documentazione_query_content_model() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    for marker in (
        "ContentQuery",
        "query_content",
        "by_type",
        "by_subtype",
        "search",
        "snapshot",
        "preorder",
        "TextBlock",
        "ValueError",
        "TypeError",
    ):
        assert marker in contract, f"Marker mancante: {marker}"
    assert all(
        not line.rstrip("\n").endswith((" ", "\t"))
        for line in contract.splitlines(keepends=True)
    )


def test_query_is_public_and_returns_deterministic_preorder() -> None:
    query = query_content(make_model())

    assert isinstance(query, ContentQuery)
    assert [node.node_type for node in query.all()] == ["rule", "example", "vocab"]
    assert query.count() == 3
    assert query.count("RULE") == 1
    assert len(query) == 3


def test_query_filters_and_search_are_case_insensitive() -> None:
    query = query_content(make_model())

    assert [node.node_type for node in query.by_type("RULE")] == ["rule"]
    assert [node.node_type for node in query.by_subtype("simple")] == ["rule", "example"]
    assert [node.node_type for node in query.search("HELLO")] == ["example"]
    assert [node.node_type for node in query.search("present")] == ["rule"]
    assert [node.node_type for node in query.search("casa")] == ["vocab"]


def test_query_results_are_detached_from_model_and_snapshot() -> None:
    model = make_model()
    query = query_content(model)

    result = query.by_type("rule")
    result[0].body = "mutated result"
    assert query.by_type("rule")[0].body == "The present tense"

    model.items[1].body = "mutated source"
    assert query.by_type("rule")[0].body == "The present tense"


def test_query_rejects_invalid_inputs() -> None:
    with pytest.raises(TypeError):
        query_content(object())  # type: ignore[arg-type]

    query = query_content(make_model())
    for method in (query.by_type, query.by_subtype, query.search):
        with pytest.raises(ValueError):
            method("   ")
