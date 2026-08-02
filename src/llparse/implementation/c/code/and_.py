from llparse_frontend import code as frontend

from .. import compilation
from .field import Field


class And(Field[frontend.And]):
    def build(self, ctx: "compilation.Compilation", out: list[str]) -> None:
        out.append(f"{self.field(ctx)} &= {self.ref.value};")
        out.append("return 0;")
