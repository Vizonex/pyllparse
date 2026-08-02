from .field_value import FieldValue


class Test(FieldValue):
    __slots__ = ("field", "name", "signature", "value")

    def __init__(self, field: str, value: int) -> None:
        super().__init__("match", "test", field, value)
