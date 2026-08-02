from collections.abc import Iterator, MutableSequence
from dataclasses import dataclass
from functools import partial

from ..utils import UniqueName
from ..wrap import Wrap
from .base import Node
from .match import Match
from .slot import Slot


@dataclass(slots=True)
class SingleEdge:
    key: int
    node: Wrap[Node]
    no_advance: bool
    value: int | None


@dataclass(slots=True, frozen=True)
class ReadonlySingleEdge:
    key: int
    node: Wrap[Node]
    no_advance: bool
    value: int | None


def update_edge(edge: SingleEdge, value: Wrap[Node]) -> None:
    edge.node = value


class Single(Match):
    __slots__ = ("priv_edges", "select")

    priv_edges: MutableSequence[SingleEdge]

    def __init__(self, id: UniqueName):
        super().__init__(id)
        self.priv_edges = []

    def add_edge(self, edge: ReadonlySingleEdge) -> None:
        self.priv_edges.append(
            SingleEdge(
                key=edge.key,
                no_advance=edge.no_advance,
                node=edge.node,
                value=edge.value,
            )
        )

    @property
    def edges(self) -> list[ReadonlySingleEdge]:
        return [
            ReadonlySingleEdge(
                key=edge.key,
                no_advance=edge.no_advance,
                node=edge.node,
                value=edge.value,
            )
            for edge in self.priv_edges
        ]

    def build_slots(self) -> Iterator[Slot[Node]]:
        for edge in self.priv_edges:
            yield Slot(edge.node, partial(update_edge, edge))
        yield from super().build_slots()
