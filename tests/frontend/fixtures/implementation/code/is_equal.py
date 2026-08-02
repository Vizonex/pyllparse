from llparse_frontend import code as frontend

from .field import Field


class IsEqual(Field[frontend.IsEqual]):
    def build(self) -> str:
        return ""
