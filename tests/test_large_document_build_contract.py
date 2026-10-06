from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from edutex.build.ordering import iter_positioned_items


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "LARGE_DOCUMENT_BUILD_CONTRACT.md"
ORDERING = ROOT / "src" / "edutex" / "build" / "ordering.py"
LATEX_RENDERER = ROOT / "src" / "edutex" / "build" / "renderer.py"
HTML_RENDERER = ROOT / "src" / "edutex" / "build" / "html_renderer.py"


@dataclass(frozen=True)
class Element:
    position_index: int
    value: str


def legacy_order(elements: list[Element], prose: list[tuple[int, object]]) -> list[tuple[int, object]]:
    combined: list[tuple[int, object]] = [
        (element.position_index, element.value) for element in elements
    ]
    combined.extend(prose)
    combined.sort(key=lambda item: item[0])
    return combined


def test_sorted_streams_match_historical_stable_order_including_ties() -> None:
    elements = [Element(1, "element-1a"), Element(1, "element-1b"), Element(3, "element-3")]
    prose = [(1, "prose-1"), (2, "prose-2")]

    actual = list(iter_positioned_items(
        elements,
        prose,
        element_value=lambda element: element.value,
    ))

    assert actual == legacy_order(elements, prose)


def test_unsorted_streams_use_compatible_stable_fallback() -> None:
    elements = [Element(4, "element-4"), Element(1, "element-1"), Element(3, "element-3")]
    prose = [(2, "prose-2"), (0, "prose-0")]

    actual = list(iter_positioned_items(
        elements,
        prose,
        element_value=lambda element: element.value,
    ))

    assert actual == legacy_order(elements, prose)


def test_large_sorted_streams_preserve_every_item_and_order() -> None:
    count = 12_000
    elements = [Element(position, f"e-{position}") for position in range(0, count * 2, 2)]
    prose = [(position, f"p-{position}") for position in range(1, count * 2, 2)]

    merged = list(iter_positioned_items(elements, prose, element_value=lambda item: item.value))

    assert len(merged) == count * 2
    assert [position for position, _ in merged] == list(range(count * 2))
    assert merged[0] == (0, "e-0")
    assert merged[-1] == (count * 2 - 1, f"p-{count * 2 - 1}")


def test_empty_streams_are_supported() -> None:
    assert list(iter_positioned_items([], [])) == []


def test_renderers_and_documentation_use_the_optimization_contract() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    ordering = ORDERING.read_text(encoding="utf-8")
    latex = LATEX_RENDERER.read_text(encoding="utf-8")
    html = HTML_RENDERER.read_text(encoding="utf-8")

    for marker in ("documenti grandi", "O(n)", "fallback stabile", "semantica", "deterministico"):
        assert marker in contract
    assert "heapq.merge" in ordering
    assert "iter_positioned_items" in latex
    assert "iter_positioned_items" in html
    assert "all_items.sort" not in latex
    assert "all_items.sort" not in html
