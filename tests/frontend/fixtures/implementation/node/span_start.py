from llparse_frontend import node as frontend

from .base import Node


class SpanStart(Node[frontend.SpanStart]):
    def do_build(self, out: list[str]) -> None:
        out.append(self.format(""))
