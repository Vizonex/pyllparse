from .base import Code


class Match(Code):
    __slots__ = ("name", "signature")

    def __init__(self, name: str):
        super().__init__("match", name)
