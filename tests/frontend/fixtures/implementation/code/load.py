from llparse_frontend import code as frontend

from .field import Field


class Load(Field[frontend.Load]):
    def build(self):
        return ""
