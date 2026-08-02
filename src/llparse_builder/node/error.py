from enum import IntEnum

from ..errors import Error
from .base import Node


class NodeError(Node):
    """Node that terminates execution with a given error"""

    __slots__ = ("code", "reason")

    def __init__(self, code: int | IntEnum, reason: str):
        super().__init__("error")
        # Decided to would go a step further and support
        # enums just like the typescript version would permit
        self.code = code.value if isinstance(code, IntEnum) else code
        self.reason = reason

    def otherwise(self):
        """`.otherwise()` is not supported with this type of Node"""
        raise Error("Not supported.")

    def skip_to(self):
        """`.skip_to` is not supported with this type of node."""
        raise Error("Not supported.")
