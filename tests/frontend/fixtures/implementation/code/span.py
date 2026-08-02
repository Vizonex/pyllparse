from llparse_frontend import code as frontend

from .base import Code


class Span(Code[frontend.Span]):
    def build(self) -> str:
        return ""
