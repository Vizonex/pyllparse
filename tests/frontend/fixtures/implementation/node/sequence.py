from binascii import hexlify
from typing import cast

from llparse_frontend import node as frontend

from .base import Node


class Sequence(Node[frontend.Sequence]):
    def do_build(self, out: list[str]) -> None:
        code = f'select="{hexlify(self.ref.select).decode("utf-8")}" '
        code += f'edge="{self.ref.edge.node.ref.id.name}"'
        if self.ref.edge.value is not None:
            code += f":{self.ref.edge.value}"
        out.append(self.format(code))
        edge_node = cast(Node, self.ref.edge.node)
        edge_node.build(out)
