from llparse_frontend import node as frontend

from .base import Node


class Invoke(Node[frontend.Invoke]):
    def do_build(self, out: list[str]) -> None:
        out.append(self.format(""))
