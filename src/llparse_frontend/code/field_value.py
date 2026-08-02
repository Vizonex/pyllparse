from .base import Signature
from .field import Field


class FieldValue(Field):
    __slots__ = ("value",)

    def __init__(
        self, signature: Signature, cache_key: str, name: str, field: str, value: int
    ):
        super().__init__(signature, cache_key, name, field)
        self.value = value
