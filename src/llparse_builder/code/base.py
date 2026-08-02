from typing import Literal


class Code:
    __slots__ = ("name", "signature")

    def __init__(self, signature: Literal["match", "value"], name: str) -> None:
        self.signature = signature
        self.name = name
