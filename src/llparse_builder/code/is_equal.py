from .field_value import FieldValue


class IsEqual(FieldValue):
    __slots__ = ("field", "name", "signature", "value")

    def __init__(self, field: str, value: int):
        super().__init__("value", "is_equal", field, value)
