from abc import ABC, abstractmethod
from typing import Generic, TypeVar, cast

from llparse_frontend import node

T = TypeVar("T", bound="node.Node")


class Node(ABC, Generic[T]):
    __slots__ = ("built", "ref")

    def __init__(self, ref: T) -> None:
        self.ref = ref
        self.built = False

    @abstractmethod
    def do_build(self, out: list[str]) -> None: ...

    def build(self, out: list[str]) -> None:
        if self.built:
            return
        self.built = True
        self.do_build(out)
        if self.ref.otherwise is not None:
            return cast(Node[T], self.ref.otherwise.node).build(out)

    def format(self, value: str) -> str:
        otherwise = ""
        if self.ref.otherwise is not None:
            otherwise_ref = cast(Node[T], self.ref.otherwise.node).ref
            otherwise = (
                " otherwise="
                + ("-no_adv" if self.ref.otherwise.no_advance else "")
                + otherwise_ref.id.name
            )
            if self.ref.otherwise.value is not None:
                otherwise += f":{self.ref.otherwise.value}"

        return (
            f"<{self.__class__.__name__} name={self.ref.id.name} "
            + f"{value}{otherwise}/>"
        )
