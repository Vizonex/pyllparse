from llparse_frontend import transform as frontend

from .base import Transform


class ID(Transform[frontend.ID]):
    def build(self, ctx, value: str) -> str:
        return value
