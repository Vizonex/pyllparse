from llparse_frontend import node as frontend

from ....ext import Writer
from .base import Node


class TableLookup(Node[frontend.TableLookup]):
    def do_build(self, out: Writer) -> None:
        super().do_build(out)
