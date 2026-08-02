from llparse_frontend import node as frontend

from ..constants import SEQUENCE_COMPLETE, SEQUENCE_MISMATCH, SEQUENCE_PAUSE
from .base import Node, NodeEdge


class Sequence(Node[frontend.Sequence]):
    def do_build(self, out):
        ctx = self.compilation

        out.append("llparse_match_t match_seq;")
        out.append("")

        self.prologue(out)

        match_sequence = ctx.get_match_sequence(self.ref.transform, self.ref.select)

        out.append(
            f"match_seq = {match_sequence}({ctx.state_arg()}, "
            + f"{ctx.pos_arg()}, "
            + f"{ctx.end_pos_arg()}, {ctx.blob(self.ref.select)}, "
            + f"{len(self.ref.select)});"
        )
        out.append("p = match_seq.current;")

        tmp = []

        out.append("switch (match_seq.status) {")

        out.append(f"  case {SEQUENCE_COMPLETE}: {{")
        tmp = []
        self.tail_to(
            tmp,
            NodeEdge(
                no_advance=False,
                node=self.ref.edge.node,
                value=self.ref.edge.value,
            ),
        )
        ctx.indent(out, tmp, "    ")
        out.append("  }")

        out.append(f"  case {SEQUENCE_PAUSE}: {{")
        tmp = []
        self.pause(tmp)
        ctx.indent(out, tmp, "    ")
        out.append("  }")

        out.append(f"  case {SEQUENCE_MISMATCH}: {{")
        tmp = []
        self.tail_to(tmp, self.ref.otherwise)
        ctx.indent(out, tmp, "    ")
        out.append("  }")
        out.append("}")
