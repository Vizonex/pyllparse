from llparse_frontend import code as frontend

from .. import compilation
from .field import Field


class Store(Field[frontend.Store]):
    def do_build(self, ctx: "compilation.Compilation", out: list[str]):
        out.append(f"{self.field(ctx)} = {ctx.match_var()};")
        out.append("return 0;")
