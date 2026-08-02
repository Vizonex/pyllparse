from .field import Field


class Load(Field):
    __slots__ = ("name", "signature")

    def __init__(self, field: str):
        super().__init__("match", "load", field)
