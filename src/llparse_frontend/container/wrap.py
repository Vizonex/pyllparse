from collections.abc import Callable
from typing import Generic, TypeVar

from ..wrap import T, Wrap

R = TypeVar("R", bound=Wrap)

# It can be quite confusing in typescript but
# in python we are simply calling the node implementation
# that we were looking for by calling it's constructor.


class ContainerWrap(Wrap[T], Generic[T, R]):
    __slots__ = ("map",)

    def __init__(self, ref: T, map: dict[str, Callable[[T], R]]):
        super().__init__(ref)
        self.map = map

    def get(self, key: str) -> R:
        assert key in self.map, f'Unknown implementation key "{key}"'
        # Typescript doesn't show it but it's simply storing
        # the node inside our implementation. Example: "C"
        return self.map[key](self.ref)
