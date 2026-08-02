from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from .. import compilation

T = TypeVar("T")


class Code(ABC, Generic[T]):
    __slots__ = ("ref",)

    def __init__(self, ref: T) -> None:
        self.ref = ref

    @abstractmethod
    def build(self, ctx: "compilation.Compilation", out: list[str]) -> None: ...
