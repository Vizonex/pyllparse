from llparse_frontend import code as frontend

from .. import compilation
from .field import Field


class Or(Field[frontend.Or]):
    def do_build(self, ctx: "compilation.Compilation", out: list[str]):
        out.append(f"{self.field(ctx)} |= {self.ref.value};")
        out.append("return 0;")
