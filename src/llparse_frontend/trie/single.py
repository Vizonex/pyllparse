from collections.abc import Sequence
from dataclasses import dataclass

from .empty import TrieEmpty
from .node import TrieNode


@dataclass(slots=True)
class TrieSingleChild:
    key: int
    no_advance: bool
    node: TrieNode


class TrieSingle(TrieNode):
    __slots__ = ("children", "otherwise")

    def __init__(
        self, children: Sequence[TrieSingleChild], otherwise: TrieEmpty | None
    ) -> None:
        self.children = children
        self.otherwise = otherwise
