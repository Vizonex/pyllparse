from llparse.ext import Writer
from llparse_frontend import code as frontend

from .field import Field


class Store(Field[frontend.Store]):
    def do_build(self, out: Writer) -> None:
        super().do_build(out)
