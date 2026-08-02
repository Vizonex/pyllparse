from dataclasses import dataclass
from functools import partial

from ..code import Code
from ..utils import UniqueName
from ..wrap import Wrap
from .base import Node
from .slot import Slot


@dataclass(slots=True)
class InvokeEdge:
    code: int
    node: Wrap[Node]


@dataclass(slots=True, frozen=True)
class ReadonlyInvokeEdge:
    code: int
    node: Wrap[Node]


def update_edge(edge: InvokeEdge, value: Wrap[Node]) -> None:
    edge.node = value


class Invoke(Node):
    __slots__ = ("code", "priv_edges")

    def __init__(self, id: UniqueName, code: Wrap[Code]):
        super().__init__(id)
        self.code = code
        self.priv_edges: list[InvokeEdge] = []

    def add_edge(self, code: int, node: Wrap[Node]):
        self.priv_edges.append(InvokeEdge(code, node))

    @property
    def edges(self) -> list[ReadonlyInvokeEdge]:
        return [ReadonlyInvokeEdge(e.code, e.node) for e in self.priv_edges]

    def build_slots(self):
        for edge in self.priv_edges:
            yield Slot(edge.node, partial(update_edge, edge))
        return super().build_slots()
