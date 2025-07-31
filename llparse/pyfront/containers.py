from typing import Generic, TypeVar

from implementation import IImplementation
from pyfront.front import IWrap, T

R = TypeVar("R")


class ContainerWrap(Generic[T]):
    def __init__(self, ref: T) -> None:
        self.ref = ref
        self.map: dict[str, IWrap[T]] = {}

    def get(self, R: type[R], key: str) -> IWrap[R]:
        """Changes and Alters the refrence to the orginal object..."""

        # UnPack Object to Do Conversion From Since We aren't Using Typescript...
        return IWrap(R(**self.map.get[key].__dict__))


# TODO Vizonex Figure out how containers
# should be implemented in python Spcae...
# Since Interfaces and other thinsg in it
# are tricky to just simply determine
class Container:
    def __init__(self) -> None:
        self.map: dict[str, IImplementation] = {}

    def build(self):
        return IImplementation()

    def buildCode(self):
        return
