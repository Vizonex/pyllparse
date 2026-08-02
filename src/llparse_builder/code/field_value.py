from typing import Literal

from .field import Field


class FieldValue(Field):
    __slots__ = ("name", "signature", "value")

    def __init__(
        self, signature: Literal["match", "value"], name: str, field: str, value: int
    ):
        super().__init__(signature, name, field)
        self.value = value
