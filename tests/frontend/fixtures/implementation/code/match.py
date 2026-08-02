from llparse_frontend import code as frontend

from .base import Code


class Match(Code[frontend.Match]):
    def build(self) -> str:
        return ""
