from llparse.ext import Writer
from llparse_frontend import code as frontend

from .field import Field


class Test(Field[frontend.Or]):
    def do_build(self, out: Writer) -> None:
        super().do_build(out)
