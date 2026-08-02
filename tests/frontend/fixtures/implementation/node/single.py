from typing import cast

from llparse_frontend import node as frontend

from .base import Node


class Single(Node[frontend.Single]):
    def do_build(self, out: list[str]) -> None:
        edges = []
        for edge in self.ref.edges:
            code = (
                f"k{edge.key}{'-no_adv-' if edge.no_advance else ''}="
                + edge.node.ref.id.name
            )
            if edge.value is not None:
                code += f":{edge.value}"
            edges.append(code)
        out.append(self.format(" ".join(edges)))

        for edge in self.ref.edges:
            edge_node = cast(Node, edge.node)
            edge_node.build(out)
