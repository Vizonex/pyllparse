from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from functools import partial

from typing_extensions import Self

from ..utils import UniqueName
from ..wrap import Wrap
from .slot import Slot


@dataclass(slots=True, frozen=True)
class ReadonlyOtherwiseEdge:
    node: "Wrap[Node]"
    no_advance: bool
    value: int | None


@dataclass(slots=True, frozen=True)
class OtherwiseEdge:
    node: "Wrap[Node]"
    no_advance: bool
    value: int | None


def update_otherwise(otherwise: OtherwiseEdge, value: "Wrap[Node]") -> None:
    otherwise.node = value


class Node:
    __slots__ = ("id", "priv_otherwise", "priv_slots")
    priv_otherwise: OtherwiseEdge | None
    priv_slots: Sequence["Slot[Node]"] | None

    def __init__(self, id: UniqueName):
        self.id = id
        self.priv_otherwise = None
        self.priv_slots = None

    def set_otherwise(
        self, node: "Wrap[Self]", no_advance: bool, value: int | None = None
    ):
        self.priv_otherwise = OtherwiseEdge(node, no_advance, value)

    @property
    def otherwise(self) -> ReadonlyOtherwiseEdge | None:
        if self.priv_otherwise:
            return ReadonlyOtherwiseEdge(
                node=self.priv_otherwise.node,
                no_advance=self.priv_otherwise.no_advance,
                value=self.priv_otherwise.value,
            )

    def get_slots(self) -> Iterator["Slot[Node]"]:
        if self.priv_slots is None:
            self.priv_slots = list(self.build_slots())
        yield from self.priv_slots

    def build_slots(self):
        otherwise = self.priv_otherwise
        if otherwise is not None:
            yield Slot(otherwise.node, partial(update_otherwise, otherwise))

    # incase needed...
    def __hash__(self) -> int:
        return hash(self.id)
