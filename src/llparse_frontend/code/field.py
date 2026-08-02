from .base import Code, Signature


class Field(Code):
    __slots__ = ("field",)

    def __init__(self, signature: Signature, cache_key: str, name: str, field: str):
        super().__init__(signature, cache_key, name)
        self.field = field
