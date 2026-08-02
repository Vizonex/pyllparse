from collections.abc import Mapping

from ..code.base import Code
from ..edge import Edge
from .base import Node


class Invoke(Node):
    __slots__ = ("code", "map")

    def __init__(self, code: Code, map: Mapping[int | str | bytes, Node]):
        super().__init__(f"invoke_{code.name}")

        for k, v in map.items():
            assert isinstance(k, int), "Invoke's map keys must be integers"
            self.add_edge(Edge(v, True, k))
        self.code = code
        self.map = map
