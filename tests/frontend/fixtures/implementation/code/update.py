from llparse.ext import Writer
from llparse_frontend import code as frontend

from .field import Field


class Update(Field[frontend.Update]):
    def do_build(self, out: Writer) -> None:
        super().do_build(out)
