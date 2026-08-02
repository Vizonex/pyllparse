from .field_value import FieldValue


class Update(FieldValue):
    __slots__ = ("name", "signature", "value")

    def __init__(self, field: str, value: int):
        super().__init__("match", "update", field, value)
