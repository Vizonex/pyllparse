from typing import Literal

from .base import Code


class Field(Code):
    __slots__ = ("field", "name", "signature")

    def __init__(self, signature: Literal["match", "value"], name: str, field: str):
        super().__init__(signature, name + "_" + field)
        assert not field.startswith("_"), "Can't access internal field from user code"
        self.field = field
