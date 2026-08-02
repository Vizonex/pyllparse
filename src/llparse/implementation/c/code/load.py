from llparse_frontend import code as frontend

from .. import compilation
from .field import Field


class Load(Field[frontend.Load]):
    def do_build(self, ctx: "compilation.Compilation", out: list[str]) -> None:
        out.append(f"return {self.field(ctx)};")
