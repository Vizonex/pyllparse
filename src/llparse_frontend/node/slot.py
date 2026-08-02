from collections.abc import Callable
from typing import Generic, TypeVar

from ..wrap import Wrap

Node = TypeVar("Node")


class Slot(Generic[Node]):
    def __init__(self, node: Wrap[Node], update: Callable[[Wrap[Node]], None]):
        self.priv_node = node
        self.priv_update = update

    @property
    def node(self) -> Wrap[Node]:
        return self.priv_node

    @node.setter
    def node(self, value: Wrap[Node]):
        self.priv_node = value
        self.priv_update(value)
