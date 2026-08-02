from .field import Field


class Store(Field):
    __slots__ = ("field", "name", "signature")

    def __init__(self, field: str):
        super().__init__("value", "store", field)
