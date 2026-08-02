from abc import abstractmethod

from .. import compilation
from .base import Code, T


class Field(Code[T]):
    def build(self, ctx: "compilation.Compilation", out: list[str]) -> None:
        out.append(f"int {self.ref.name}(")
        out.append(f"    {ctx.prefix}_t* {ctx.state_arg()},")
        out.append(f"    const unsigned char* {ctx.pos_arg()},")
        if self.ref.signature == "value":
            out.append(f"    const unsigned char* {ctx.end_pos_arg()},")
            out.append(f"    int {ctx.match_var()}) {{")
        else:
            out.append(f"    const unsigned char* {ctx.end_pos_arg()}) {{")

        tmp = []
        self.do_build(ctx, tmp)
        ctx.indent(out, tmp, "  ")
        out.append("}")

    @abstractmethod
    def do_build(self, ctx: "compilation.Compilation", out: list[str]) -> None: ...

    def field(self, ctx: "compilation.Compilation") -> str:
        return f"{ctx.state_arg()}->{self.ref.field}"
