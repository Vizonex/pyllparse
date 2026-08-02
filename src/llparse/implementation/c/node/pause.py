from llparse_frontend import node as frontend

from ..constants import STATE_ERROR
from .error import ErrorNode


class Pause(ErrorNode[frontend.Pause]):
    def do_build(self, out: list[str]) -> None:
        ctx = self.compilation

        self.store_error(out)

        otherwise = ctx.unwrap_node(self.ref.otherwise.node).build(ctx)
        out.append(f"{ctx.current_field()} = " + f"(void*) (intptr_t) {otherwise};")
        out.append(f"return {STATE_ERROR};")
