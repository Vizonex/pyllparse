from llparse_frontend import code as frontend

from .field import Field


class Or(Field[frontend.Or]):
    def build(self):
        return super().build()
