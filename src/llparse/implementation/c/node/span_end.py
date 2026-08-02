from llparse_frontend import node as frontend

from ..constants import STATE_ERROR, STATE_PREFIX
from .base import Node, NodeEdge


class SpanEnd(Node[frontend.SpanEnd]):
    def do_build(self, out: list[str]):
        out.append("const unsigned char* start;")
        out.append("int err;")
        out.append("")

        ctx = self.compilation
        field = self.ref.field
        posField = ctx.span_pos_field(field.index)

        # Loast start position
        out.append(f"start = {posField};")

        # reset position
        out.append(f"{posField} = NULL;")

        # Invoke callback
        callback = ctx.build_code(ctx.unwrap_code(self.ref.callback))

        out.append(f"err = {callback}({ctx.state_arg()}, start, {ctx.pos_arg()});")

        out.append("if (err != 0) {")
        tmp = []
        self.build_error(tmp, "err")
        ctx.indent(out, tmp, "  ")
        out.append("}")

        otherwise = self.ref.otherwise
        self.tail_to(out, NodeEdge(otherwise.node, otherwise.no_advance, None))

    def build_error(self, out: list[str], code: str):
        ctx = self.compilation

        out.append(f"{ctx.error_field()} = {code};")

        otherwise = self.ref.otherwise
        assert otherwise

        resume_pos = ctx.pos_arg()

        if not otherwise.no_advance:
            resume_pos = f"({resume_pos} +  1)"

        out.append(f"{ctx.error_pos_field()} = (const char*) {resume_pos};")

        rt = ctx.unwrap_node(otherwise.node)
        # check if the resumption target has already been built or not...
        resumption_target = rt.build(ctx)

        out.append(
            f"{ctx.current_field()} = "
            + f"(void*) (intptr_t) {STATE_PREFIX + resumption_target if not resumption_target.startswith(STATE_PREFIX) else resumption_target};"
        )
        out.append(f"return {STATE_ERROR};")
