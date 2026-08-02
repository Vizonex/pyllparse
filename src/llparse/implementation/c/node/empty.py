from llparse_frontend import node as frontend

from .base import Node


class Empty(Node[frontend.Empty]):
    def do_build(self, out: list[str]) -> None:
        otherwise = self.ref.otherwise
        if not otherwise.no_advance:
            self.prologue(out)
        self.tail_to(out, otherwise)
