from abc import ABC
from typing import Generic, TypeVar

T = TypeVar("T")


class Code(ABC, Generic[T]):
    __slots__ = ("ref",)

    def __init__(self, ref: T) -> None:
        self.ref = ref

    def build(self) -> str:
        return ""
