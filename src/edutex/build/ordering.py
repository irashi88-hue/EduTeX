"""Memory-conscious, stable merging of document content streams."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, Sequence
from heapq import merge
from typing import TypeVar


T = TypeVar("T")


def _is_non_decreasing(positions: Iterable[int]) -> bool:
    """Return whether integer positions are already sorted without materializing them."""
    iterator = iter(positions)
    try:
        previous = next(iterator)
    except StopIteration:
        return True
    for position in iterator:
        if position < previous:
            return False
        previous = position
    return True


def iter_positioned_items(
    elements: Sequence[T],
    prose_blocks: Sequence[tuple[int, object]],
    *,
    element_value: Callable[[T], object] | None = None,
) -> Iterator[tuple[int, object]]:
    """Yield elements and prose in stable position order with a lazy sorted fast path.

    Render pipeline sequences are commonly already position ordered. In that case,
    ``heapq.merge`` avoids constructing and sorting a second combined list. Arbitrary
    unsorted inputs retain the historical stable-sort behavior as a compatibility path.
    For equal positions, element entries precede prose entries, matching the former
    combined-list insertion order.
    """
    project = element_value or (lambda item: item)
    element_positions = (getattr(element, "position_index") for element in elements)
    prose_positions = (position for position, _ in prose_blocks)

    if _is_non_decreasing(element_positions) and _is_non_decreasing(prose_positions):
        yield from merge(
            (
                (getattr(element, "position_index"), project(element))
                for element in elements
            ),
            iter(prose_blocks),
            key=lambda item: item[0],
        )
        return

    combined = [
        (getattr(element, "position_index"), project(element))
        for element in elements
    ]
    combined.extend(prose_blocks)
    combined.sort(key=lambda item: item[0])
    yield from combined
