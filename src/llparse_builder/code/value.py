from .base import Code


class Value(Code):
    __slots__ = ("name", "signature")

    def __init__(self, name):
        super().__init__("value", name)
