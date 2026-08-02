import sys
from collections.abc import Sequence

from ..edge import Edge
from ..transform import Transform
from ..utils import to_buffer
from .base import Node

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


MatchSingleValue = str | int | bytes
MatchValue = MatchSingleValue | Sequence[MatchSingleValue]


class Match(Node):
    __slots__ = ("transform_fn",)

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.transform_fn: Transform | None = None

    def transform(self, transform: Transform) -> Self:
        self.transform_fn = transform
        return self

    def match(self, value: MatchValue, next: Node) -> Self:
        if not isinstance(value, (str, bytes, int, bytearray, memoryview)):
            for subvalue in value:
                self.match(subvalue, next)
            return self

        edge = Edge(next, False, to_buffer(value))
        self.add_edge(edge)
        return self

    def peek(self, value: MatchValue, next: Node) -> Self:

        if not isinstance(value, str) and isinstance(value, Sequence):
            for subvalue in value:
                self.peek(subvalue, next)
            return self
        b = to_buffer(value)
        assert len(b) == 1, "`.peek()` accepts only single character keys"
        # NOTE: Numbers with peek are considered unacceptable.
        # this is because of the loop-checker, therefore we
        # transform it into bytes. Got stuck for weeks with this library
        # because it was configured as Edge(next, True, ord(b)) Very costly
        # mistake, Do NOT DO IT!!!
        edge = Edge(next, True, b)
        self.add_edge(edge)
        return self

    def select(
        self,
        key_or_map: str | bytes | int | dict[str | bytes | int, int],
        value_or_next: int | Node | None = None,
        next: Node | None = None,
    ):
        if isinstance(key_or_map, dict):
            assert isinstance(value_or_next, Node), "Invalid next argument of select"
            assert next is None, "Inavlid argument count of select"
            for k, v in key_or_map.items():
                self.select(k, v, value_or_next)
            return self

        assert isinstance(value_or_next, int), "Invalid value argument of select"
        assert next is not None, "Invalid next argument of select"
        edge = Edge(next, False, to_buffer(key_or_map), value_or_next)
        self.add_edge(edge)
        return self

    def get_transform(self) -> Transform | None:
        return self.transform_fn
