from llparse.ext import Writer
from llparse_frontend import node as frontend

from .base import Node


class Empty(Node[frontend.Empty]):
    def do_build(self, out: Writer) -> None:
        out.append(self.format(""))
