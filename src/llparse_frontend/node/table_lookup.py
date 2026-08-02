from collections.abc import Iterator, MutableSequence, Sequence
from dataclasses import dataclass
from functools import partial

from ..utils import UniqueName
from ..wrap import Wrap
from .base import Node
from .match import Match
from .slot import Slot


@dataclass(slots=True)
class TableEdge:
    keys: Sequence[int]
    node: Wrap[Node]
    no_advance: bool


@dataclass(slots=True, frozen=True)
class ReadonlyTableEdge:
    keys: Sequence[int]
    node: Wrap[Node]
    no_advance: bool


def update_edge(edge: TableEdge, value: Wrap[Node]) -> None:
    edge.node = value


class TableLookup(Match):
    __slots__ = ("priv_edges",)

    priv_edges: MutableSequence[TableEdge]

    def __init__(self, id: UniqueName):
        super().__init__(id)
        self.priv_edges = []

    def add_edge(self, edge: ReadonlyTableEdge) -> None:
        self.priv_edges.append(
            TableEdge(
                keys=edge.keys,
                no_advance=edge.no_advance,
                node=edge.node,
            )
        )

    @property
    def edges(self) -> list[ReadonlyTableEdge]:
        return [
            ReadonlyTableEdge(
                keys=edge.keys,
                no_advance=edge.no_advance,
                node=edge.node,
            )
            for edge in self.priv_edges
        ]

    def build_slots(self) -> Iterator[Slot[Node]]:
        for edge in self.priv_edges:
            yield Slot(edge.node, partial(update_edge, edge))
        yield from super().build_slots()
