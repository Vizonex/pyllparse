from llparse_frontend import node as frontend

from ....error import Error
from ..constants import UNSIGNED_TYPES
from .base import Node


class Consume(Node[frontend.Consume]):
    def do_build(self, out: list[str]):
        ctx = self.compilation

        index = ctx.state_field(self.ref.field)
        ty = ctx.state_field(self.ref.field)

        try:
            field_ty = UNSIGNED_TYPES[ty]
        except KeyError:
            raise Error(
                f"Unsupported type {ty} of field {self.ref.field} for consume node"
            )

        out.append("size_t avail;")
        out.append(f"{field_ty} need;")
        out.append("")
        out.append(f"avail = {ctx.endPosArg()} - {ctx.posArg()};")
        out.append(f"need = {index};")

        # Note: `avail` or `need` are going to coerced to the largest
        # datatype needed to hold either of the values.
        out.append("if (avail >= need) {")
        out.append("  p += need;")
        out.append(f"  {index} = 0;")
        tmp = []
        self.tail_to(tmp, self.ref.otherwise)
        ctx.indent(out, tmp, "  ")
        out.append("}")
        out.append("")

        out.append(f"{index} -= avail;")
        self.pause(out)
