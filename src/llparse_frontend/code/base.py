from typing import Literal, TypeAlias

Signature: TypeAlias = Literal["match", "value", "span"]


class Code:
    __slots__ = ("cache_key", "name", "signature")

    def __init__(
        self, signature: Literal["match", "value", "span"], cache_key: str, name: str
    ) -> None:
        self.signature = signature
        self.cache_key = cache_key
        self.name = name
