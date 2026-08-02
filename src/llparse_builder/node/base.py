import sys
from collections import deque
from collections.abc import Iterator, Sequence

from ..edge import Edge
from ..errors import Error

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


# shortcut so we don't leak functions into the main node that gets
# subclassed quite a lot.
def add_otherwise_edge(this: "Node", other: "Node", no_advance: bool):
    if this.otherwise_edge is not None:
        raise Error("Node already has an `otherwise` or `skip_to`")
    this.otherwise_edge = Edge(other, no_advance, None, None)


class Node:
    __slots__ = ("name", "otherwise_edge", "priv_edges")

    def __init__(self, name: str) -> None:
        self.otherwise_edge: Edge | None = None
        self.priv_edges: deque[Edge] = deque()
        self.name = name

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, value):
        if not isinstance(value, Node):
            return False
        return (
            value.name == self.name
            and value.priv_edges == self.priv_edges
            and value.otherwise_edge == self.otherwise_edge
        )

    def otherwise(self, node: "Node") -> Self:
        add_otherwise_edge(self, node, True)
        return self

    def skip_to(self, node: "Node") -> Self:
        add_otherwise_edge(self, node, False)
        return self

    def get_otherwise_edge(self) -> Edge | None:
        return self.otherwise_edge

    def get_all_edges(self) -> Sequence[Edge]:
        if edge := self.otherwise_edge:
            return [*self.priv_edges, edge]
        return self.priv_edges

    def __iter__(self) -> Iterator[Edge]:
        yield from self.priv_edges

    def add_edge(self, edge: Edge) -> None:
        assert edge.key is not None
        assert edge not in self.priv_edges, "Attempting to create duplicate edge"
        self.priv_edges.appendleft(edge)
