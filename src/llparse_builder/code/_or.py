from .field_value import FieldValue


class Or(FieldValue):
    __slots__ = ("name", "signature", "value")

    def __init__(self, field: str, value: int):
        super().__init__("match", "or", field, value)
