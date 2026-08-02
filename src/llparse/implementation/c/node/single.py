from llparse_frontend import node as frontend

from .base import Node, NodeEdge


class Single(Node[frontend.Single]):
    def do_build(self, out: list[str]):
        ctx = self.compilation
        otherwise = self.ref.otherwise
        assert otherwise

        self.prologue(out)
        transform = ctx.unwrap_transform(self.ref.transform)
        current = transform.build(ctx, f"*{ctx.pos_arg()}")
        out.append(f"switch ({current})" + "{")

        for e in self.ref.edges:
            if e.key < 0x20 or e.key > 0x7E or e.key == 0x27 or e.key == 0x5C:
                ch = e.key
            else:
                ch = f"'{chr(e.key)}'"

            out.append(f"  case {ch}: " + "{")
            tmp: list[str] = []

            # For now debug everything....

            self.tail_to(tmp, NodeEdge(e.node, e.no_advance, e.value))

            ctx.indent(out, tmp, "    ")
            out.append("  }")

        out.append("  default: {")

        tmp: list[str] = []
        self.tail_to(tmp, NodeEdge(otherwise.node, otherwise.no_advance, None))
        ctx.indent(out, tmp, "    ")
        out.append("  }")
        out.append("}")
