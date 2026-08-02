from ..transform import Transform
from ..wrap import Wrap
from .base import Node


class Match(Node):
    __slots__ = ("transform",)

    def __init__(self, id):
        super().__init__(id)
        self.transform: Transform | None = None

    def set_transform(self, transform: Wrap[Transform]):
        self.transform = transform
