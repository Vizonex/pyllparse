from llparse_frontend import code as frontend

from .. import compilation
from .field import Field


class Test(Field[frontend.Test]):
    def do_build(self, ctx: "compilation.Compilation", out: list[str]):
        value = self.ref.value
        out.append(f"return ({self.field(ctx)} & {value}) == {value};")
