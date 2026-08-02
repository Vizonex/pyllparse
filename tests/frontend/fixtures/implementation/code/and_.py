from llparse_frontend import code as frontend

from .base import Code


class And(Code[frontend.And]):
    def build(self) -> str:
        return ""
