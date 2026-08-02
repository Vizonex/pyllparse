from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class Transform(ABC, Generic[T]):
    __slots__ = ("ref",)

    def __init__(self, ref: T) -> None:
        self.ref = ref

    @abstractmethod
    def build(self, ctx, value: str) -> str: ...
