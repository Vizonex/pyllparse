from llparse_frontend import node as frontend

from .base import Node


class Consume(Node[frontend.Consume]):
    def do_build(self, out: list[str]) -> None:
        out.append(self.format(f"field={self.ref.field}"))
