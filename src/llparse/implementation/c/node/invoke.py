from llparse_frontend import node as frontend

from .base import Node, NodeEdge


class Invoke(Node[frontend.Invoke]):
    def do_build(self, out: list[str]) -> None:
        ctx = self.compilation

        code = ctx.unwrap_code(self.ref.code)

        code_decl = ctx.build_code(code)

        args = [ctx.state_arg(), ctx.pos_arg(), ctx.end_pos_arg()]

        signature = code.ref.signature

        if signature == "value":
            args.append(ctx.match_var())

        out.append(f"switch ({code_decl}({', '.join(args)})) {{")

        for edge in self.ref.edges:
            out.append(f"  case {edge.code}:")
            tmp = []
            self.tail_to(tmp, NodeEdge(no_advance=True, node=edge.node, value=None))
            ctx.indent(out, tmp, "    ")

        out.append("  default:")
        tmp = []

        self.tail_to(tmp, self.ref.otherwise)
        ctx.indent(out, tmp,  "    ")
        out.append("}")
