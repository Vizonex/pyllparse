from llparse_frontend import code as frontend

from .field import Field


class MulAdd(Field[frontend.MulAdd]):
    def build(self):
        return ""
