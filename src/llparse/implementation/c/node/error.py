from ..constants import STATE_ERROR
from .base import Node, T


class ErrorNode(Node[T]):
    def store_error(self, out: list[str]):
        ctx = self.compilation
        hex_code = hex(self.ref.code)

        out.append(f"{ctx.error_field()} = {hex_code};")
        out.append(f"{ctx.reason_field()} = {ctx.cstring(self.ref.reason)};")
        out.append(f"{ctx.error_pos_field()} = (const char*) {ctx.pos_arg()};")

    def do_build(self, out: list[str]) -> None:
        self.store_error(out)

        out.append(
            f"{self.compilation.current_field()} = "
            + f"(void*) (intptr_t) {STATE_ERROR};"
        )
        out.append(f"return {STATE_ERROR};")

Error = ErrorNode