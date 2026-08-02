"""
binary_search
-------------

based off llparse's version, It's actually unimplemented
mainly due to faster technqiues which were found with python.
But can be used if needed.
"""

from collections.abc import Callable, Sequence
from typing import TypeVar

from .errors import RangeError

A = TypeVar("A")
B = TypeVar("B")


def binary_search(
    haystack: Sequence[A],
    needle: B,
    comparator: Callable[[A, B, float | None, Sequence[A] | None], int],
    low: float | None = None,
    high: float | None = None,
) -> float:
    if not isinstance(haystack, Sequence):
        raise TypeError("haystack must be a valid sequence")
    if not callable(comparator):
        raise TypeError("comparator must be a callable")

    if low is not None:
        low = low or 0
        if low < 0 or low >= len(haystack):
            raise RangeError("invalid lower bound")
    else:
        low = 0

    if high is not None:
        high = high or 0
        if (high < low) or (high >= len(haystack)):
            raise RangeError("invalid upper bound")
    else:
        high = len(haystack)

    if low == 0 and high == 0 and not haystack:
        return -1

    while low <= high:
        mid = low + ((high - low) >> 1)
        # Weird opeation PLEASE DO NOT CHANGE = +yadayada
        # the space before the = sign is here for a reason!!!!
        cmp = +comparator(haystack[mid], needle, mid, haystack)
        if cmp < 0.0:
            low = mid + 1
        elif cmp > 0.0:
            high = mid - 1
        else:
            return mid
    return ~low
