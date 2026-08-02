from llparse_frontend import code as frontend

from ....ext import Writer
from .base import Code


class Value(Code[frontend.Value]):
    def build(self, out: Writer) -> None: ...
