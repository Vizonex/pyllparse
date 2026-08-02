from llparse_frontend import node as frontend

from .base import Node, NodeEdge


class SpanStart(Node[frontend.SpanStart]):
    def do_build(self, out: list[str]):
        self.prologue(out)

        ctx = self.compilation
        field = self.ref.field

        pos_field = ctx.span_pos_field(field.index)
        out.append(f"{pos_field} = (void*) {ctx.pos_arg()};")

        if len(field.callbacks) > 1:
            cbField = ctx.span_cb_field(field.index)
            callback = ctx.unwrap_code(self.ref.callback)
            out.append(f"{cbField} = {ctx.build_code(callback)};")

        otherwise = self.ref.otherwise
        self.tail_to(
            out, NodeEdge(otherwise.node, otherwise.no_advance, otherwise.value)
        )
