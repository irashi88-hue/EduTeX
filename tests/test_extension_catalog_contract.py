"""Tests for the official extension catalog contract."""

from __future__ import annotations

from pathlib import Path

from edutex.extension.catalog import (
    get_official_extension,
    official_extension_catalog,
    search_official_extensions,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "EXTENSION_CATALOG_CONTRACT.md"


def test_catalog_is_stable_and_contains_reading_tip() -> None:
    catalog = official_extension_catalog()
    assert [entry.extension_id for entry in catalog] == ["reading_tip"]

    entry = get_official_extension("reading_tip")
    assert entry is not None
    assert entry.version == "1.0.0"
    assert entry.framework == ">=1.0.0,<2.0.0"
    assert entry.target == "layout.post_structure"
    assert entry.optional is False


def test_catalog_lookup_and_search_are_deterministic() -> None:
    assert get_official_extension("missing") is None
    assert [entry.extension_id for entry in search_official_extensions("READING")] == [
        "reading_tip"
    ]
    assert [entry.extension_id for entry in search_official_extensions("")] == [
        "reading_tip"
    ]
    assert search_official_extensions("not present") == ()


def test_catalog_entries_serialize_as_detached_mappings() -> None:
    first = official_extension_catalog()[0].to_dict()
    first["id"] = "changed"
    assert official_extension_catalog()[0].extension_id == "reading_tip"
    assert first["version"] == "1.0.0"


def test_documentation_covers_the_catalog_contract() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    for marker in (
        "official_extension_catalog",
        "get_official_extension",
        "search_official_extensions",
        "ExtensionCatalogEntry",
        "reading_tip",
        "metadata-only",
        "detached",
    ):
        assert marker in contract, f"Marker mancante: {marker}"
    assert all(
        not line.rstrip("\n").endswith((" ", "\t"))
        for line in contract.splitlines(keepends=True)
    )
