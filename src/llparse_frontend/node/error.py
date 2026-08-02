from ..utils import UniqueName
from .base import Node


class Error(Node):
    __slots__ = ("code", "reason")

    def __init__(self, id: UniqueName, code: int, reason: str) -> None:
        super().__init__(id)
        self.code = code
        self.reason = reason
