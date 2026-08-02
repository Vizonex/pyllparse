from ..utils import UniqueName
from .base import Node


class Consume(Node):
    __slots__ = ("field",)

    def __init__(self, id: UniqueName, field: str):
        super().__init__(id)
        self.field = field
