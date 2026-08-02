from typing import Generic, TypeVar

T = TypeVar("T")

# While it may not make as much sense to have this in python
# due to duck-typing, It was kept to preverse the parody incase
# of unknown edge cases.


class Wrap(Generic[T]):
    __slots__ = ("ref",)

    def __init__(self, ref: T) -> None:
        self.ref = ref

    def __hash__(self) -> int:
        return hash(self.ref)
