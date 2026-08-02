from enum import IntEnum

from .base import Node


class Pause(Node):
    __slots__ = ("code", "reason")

    def __init__(self, code: int | IntEnum, reason: str) -> None:
        super().__init__("pause")
        self.code = code.value if isinstance(code, IntEnum) else code
        self.reason = reason
