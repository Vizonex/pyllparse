from llparse_frontend import code as frontend

from .. import compilation
from .base import Code


class External(Code[frontend.External]):
    def build(self, ctx: "compilation.Compilation", out: list[str]) -> None:
        out.append(f"int {self.ref.name}(")
        out.append(f"    {ctx.prefix}_t* s, const unsigned char* p,")
        if self.ref.signature == "value":
            out.append("    const unsigned char* endp,")
            out.append("    int value);")
        else:
            out.append("    const unsigned char* endp);")
