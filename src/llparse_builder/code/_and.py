from .field_value import FieldValue


class And(FieldValue):
    __slots__ = ("name", "signature", "value")

    def __init__(self, field: str, value: int) -> None:
        super().__init__("match", "and", field, value)
