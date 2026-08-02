from collections.abc import Iterator
from dataclasses import dataclass
from functools import partial

from ..utils import UniqueName
from ..wrap import Wrap
from .base import Node
from .match import Match
from .slot import Slot


@dataclass(slots=True)
class SequenceEdge:
    node: Wrap[Node]
    value: int | None


@dataclass(slots=True, frozen=True)
class ReadonlySequenceEdge:
    node: Wrap[Node]
    value: int | None


def update_edge(edge: SequenceEdge, value: Wrap[Node]) -> None:
    edge.node = value


class Sequence(Match):
    __slots__ = ("priv_edge", "select")

    priv_edge: SequenceEdge | None

    def __init__(self, id: UniqueName, select: bytes):
        super().__init__(id)
        self.select = select
        self.priv_edge = None

    def set_edge(self, node: Wrap[Node], value: int | None):
        assert self.priv_edge is None
        self.priv_edge = SequenceEdge(node, value)

    @property
    def edge(self) -> ReadonlySequenceEdge:
        return ReadonlySequenceEdge(self.priv_edge.node, self.priv_edge.value)

    def build_slots(self) -> Iterator[Slot[Node]]:
        edge = self.priv_edge
        if edge is not None:
            yield Slot(edge.node, partial(update_edge, edge))
        yield from super().build_slots()
